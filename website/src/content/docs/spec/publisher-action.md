---
title: "Publisher Action"
description: "Specification for the MOAT Publisher Action GitHub Actions workflow."
---

:::note[Spec metadata]
**Version:** 0.2.0 (Draft) · **Requires:** moat-spec.md ≥ 0.5.0
:::

The Publisher Action is the primary adoption mechanism for the `Dual-Attested` trust tier. Any source repo adopts it with a single workflow file — no key management, no MOAT-specific knowledge required.

---

## What It Does (on push)

1. Detects source repository visibility. If `private` or `internal` and `allow-private-repo: true` is not set, exits immediately with a non-zero code and a clear error message. See Private Repository Guard.
2. Discovers content items via two-tier model: canonical category directories (`skills/`, `subagents/`, `rules/`, `commands/`) or `.moat/publisher.yml` if present.
3. Computes content hashes using the MOAT algorithm (`reference/moat_hash.py`). Errors (symlinks, empty directories) skip the item with a logged warning.
4. Builds one attestation payload JSON per content item (schema below).
5. Signs each payload with `cosign sign-blob --new-bundle-format` using Sigstore keyless OIDC. GitHub Actions provides the OIDC token automatically — no keys or secrets required. The `--new-bundle-format` flag is REQUIRED — it produces a Sigstore protobuf bundle v0.3 as mandated by [Signature Envelope](../moat-spec.md#signature-envelope). The workflow path and branch are encoded into the OIDC certificate at signing time and recorded automatically in `publisher_workflow_ref` in `moat-attestation.json`. Registries read this field to derive the expected OIDC subject for publisher verification — no manual filename configuration is needed.
6. Rekor creates a transparency log entry. `cosign` returns a v0.3 bundle. The Publisher Action reads the Rekor log id from `verificationMaterial.tlogEntries[0].logId.keyId` and the log index from `verificationMaterial.tlogEntries[0].logIndex`, and records them as `rekor_log_id` and `rekor_log_index` in `moat-attestation.json`.
7. Writes/updates `moat-attestation.json` with Rekor references for each attested item, including the `private_repo` field.
8. Pushes `moat-attestation.json` to the `moat-attestation` branch with commit message `chore(moat): update attestation`. If the branch does not exist, the action creates it. The `moat-attestation` branch is never merged into the source branch — it contains only attestation data.
9. If `registry-webhook` is configured and the repository is public, POSTs a signed notification payload to the webhook URL. On private or internal repositories, webhook delivery requires an additional explicit opt-in. See Webhook section.

**Branch isolation note:** The Publisher Action pushes to `moat-attestation`, not to the branch that triggered it. Workflow triggers scoped to `main` (or equivalent) do not fire on pushes to `moat-attestation`, so recursive execution is structurally impossible. Publishers MUST NOT configure the action to trigger on pushes to the `moat-attestation` branch. Unlike the commit-back model, this approach works with standard branch protection on `main` — no PAT or bypass configuration is required.

## Undiscovered Content Detection (normative)

After tier-1 discovery (canonical category directories) and tier-2 discovery (`.moat/publisher.yml`) are complete, the action MUST inspect the repository root for directories with content-like structure that were not covered by either discovery tier.

**Detection rule (normative — MUST):** A directory is "content-like" if it contains at least one file with a text extension (`.md`, `.yaml`, `.json`, `.py`, etc.) and is not one of: `.git`, `.github`, `.moat`, `node_modules`, `.venv`, `__pycache__`, or other VCS/tooling directories. If such a directory was not matched by discovery, it is reported as potentially undiscovered content.

**Required action log output:**

1. **Discovery summary (always):** After discovery, emit a log line of the form:
   ```
   Attested N items: X skills, Y agents, Z rules. Skipped: hooks/ (empty).
   ```
   Where `N` is the total attested count and the per-type breakdown covers all types with at least one item. "Skipped" lists directories that exist but contained no attested items (empty directories, or directories skipped due to symlinks or other errors).

2. **Undiscovered content warning:** When a content-like directory is found but not covered by discovery, emit:
   ```
   Warning: directory 'tools/' looks like it may contain content items but was not attested.
   If these are MOAT content items, add them to .moat/publisher.yml:

     items:
       - path: tools/my-tool
         type: skill
         name: my-tool
   ```
   The suggested `.moat/publisher.yml` snippet MUST list every unmatched directory as a separate entry with `path`, `type` (defaulting to `skill` as the most common type), and `name` (defaulting to the directory name). Publishers copy and edit this snippet — the action does not write `.moat/publisher.yml` automatically.

This behavior is detection-only and non-blocking. Unmatched directories do not cause the action to fail. The warning is surfaced in the action log so publishers can review and optionally extend their coverage.

---

## `.moat/` Directory Reservation (normative)

The `.moat/` directory at the repository root is reserved for MOAT protocol files. Publishers MUST NOT use this directory for content items, arbitrary configuration, or any purpose not defined by this specification.

Currently defined files:

- `.moat/publisher.yml` — tier-2 discovery config (this spec)
- `.moat/registry.yml` — registry operator config ([registry-action](/spec/registry-action))

**Unknown-file warning (normative — MUST):** The Publisher Action MUST emit a warning for any file under `.moat/` whose name matches `^[^.].*\.(yml|yaml)$` and is not a currently defined file. Example:

```
Warning: .moat/foo.yml is not a recognized MOAT config file. The .moat/ directory is reserved for MOAT protocol files; unexpected files here may indicate a typo or a forward-compatibility issue with a newer MOAT version.
```

Non-YAML files under `.moat/` (e.g., `.moat/README.md`, `.moat/.gitkeep`) MUST NOT trigger the warning.

**Attestation exclusion (normative — MUST):** Files under `.moat/` MUST NOT be included in the attestation payload. They are protocol metadata, not content. Their presence or absence does not affect any `content_hash`.

---

## Actionable Error Messages (normative — SHOULD)

The Publisher Action SHOULD emit actionable error messages for common misconfigurations. These messages are not failure gates — they surface in the action log to help publishers self-diagnose.

**Config at wrong location:** If `moat.yml` exists at the repository root (legacy pre-v0.7.0 location) and `.moat/publisher.yml` does not, emit:

```
Warning: found moat.yml at repository root. MOAT v0.7.0+ expects this file at .moat/publisher.yml. Move it with: mkdir -p .moat && git mv moat.yml .moat/publisher.yml
```

**Workflow rename without `paths:` update:** If the workflow file is named `.github/workflows/moat-publisher.yml` but the workflow's `paths:` trigger (when present as an allow-list) still references `moat.yml`, the Publisher Action SHOULD emit:

```
Warning: .github/workflows/moat-publisher.yml has a paths: trigger referencing moat.yml. Update the trigger to reference .moat/publisher.yml, or the workflow will not fire on publisher config changes.
```

These messages apply only when the misconfiguration is detectable from the Publisher Action's runtime context. They are best-effort diagnostics, not completeness guarantees.

---

## Attestation Payload Schema (normative)

Each content item produces one payload. This is what gets signed and recorded in Rekor.

```json
{"_version":1,"content_hash":"sha256:abc123..."}
```

Serialization rules: UTF-8, no BOM, no trailing newline, no insignificant whitespace, lexicographic key order. This is identical to the canonical payload the Registry Action signs for the same item. Both the Publisher Action and Registry Action sign the same payload bytes — they are distinguished by the OIDC subject in the Rekor certificate, not by payload content.

**Why the same payload?** A richer payload (with `item_name`, `source_ref`, `attested_at`, etc.) cannot be verified by the Registry Action at crawl time because `source_ref` and `attested_at` are unknown to the registry — they cannot be reconstructed. The OIDC certificate already encodes the repository, workflow path, and ref at signing time; a richer payload would duplicate that data without adding verifiability.

**Rekor entry:** `cosign sign-blob` creates a `hashedrekord` entry. The certificate subject encodes the GitHub Actions OIDC identity:

```
https://github.com/{owner}/{repo}/.github/workflows/moat-publisher.yml@refs/heads/main
```

This identity is what registries and `moat-verify` use to confirm the attestation came from a legitimate Publisher Action run on the claimed source repository. The Rekor certificate's `sub` claim encodes the repository, workflow path, and ref — no additional provenance fields in the payload are needed or verified.

**Workflow filename and branch:** The Publisher Action may use any valid workflow filename. At runtime it reads its own path and branch from `GITHUB_WORKFLOW_REF` (a GitHub-injected environment variable) and records the result as `publisher_workflow_ref` in `moat-attestation.json`. The Registry Action reads this field when verifying publisher Rekor entries — the registry never needs to know the filename in advance. The recommended filename is `.github/workflows/moat-publisher.yml`, which the reference workflow uses by default.

---

## `moat-attestation.json` Format (normative)

Location: `moat-attestation` branch root. One file per repo. The file is never present in the source branch, so it is never included in content hashing — the circular dependency concern from the commit-back model does not apply.

```json
{
  "schema_version": 1,
  "attested_at": "2026-04-07T14:00:00Z",
  "publisher_workflow_ref": ".github/workflows/moat-publisher.yml@refs/heads/main",
  "private_repo": false,
  "items": [
    {
      "name": "summarizer-skill",
      "content_hash": "sha256:abc123...",
      "source_ref": "abc123def456...",
      "rekor_log_id": "24296fb24b8ad77a...",
      "rekor_log_index": 12345678
    }
  ],
  "revocations": []
}
```

**`private_repo` field:** REQUIRED. `true` when the action ran on a `private` or `internal` repository; `false` for `public`. This annotation is visible to registries and conforming clients — they MAY use it to isolate, flag, or reject attestations from private repositories. Attestations created before this field was added will not have it; conforming registries SHOULD treat absent `private_repo` as unknown visibility rather than assuming public.

**`publisher_workflow_ref` field:** OPTIONAL. The workflow path and ref that produced this attestation, derived from `GITHUB_WORKFLOW_REF` at signing time (e.g., `.github/workflows/moat-publisher.yml@refs/heads/main`). The Registry Action reads this field to construct the expected OIDC subject for publisher verification. If absent, the Registry Action cannot construct the expected subject and MUST downgrade the item to `Signed` (no legacy-path fallback).

**`source_ref` field (per item):** OPTIONAL. Full commit SHA at the time of attestation. Stored in `moat-attestation.json` as informational context only — it is not part of the signed payload and MUST NOT be used in trust decisions. The Rekor certificate's encoded ref is authoritative for provenance; `source_ref` here is for human auditing and tooling convenience.

---

## Revocation via Publisher Action

Publishers can post signed Rekor revocation entries without waiting for their registry to update. To revoke: add an entry to `moat-attestation.json` revocations and trigger the action. It posts a signed Rekor revocation entry and optionally notifies the registry via webhook.

Publisher revocations are **warnings, not hard blocks.** The registry is the gating authority for hard blocks. This prevents abuse (compromised publisher accounts triggering mass revocations). See [core spec](/spec/core) for full client behavior rules.

---

## Webhook (optional)

Passive by default — the action signs and stops. Registries discover attestations on their own crawl cycle. For fast propagation, publishers can configure an optional webhook URL:

```yaml
uses: moat-spec/publisher-action@v1
with:
  registry-webhook: ${{ secrets.MOAT_REGISTRY_WEBHOOK }}
```

**Two-layer security:**

- **Transport auth (HMAC-SHA256):** Publisher Action signs the webhook payload with a shared secret. Registries verify the `X-MOAT-Signature-256` header before processing. Authenticates the sender.
- **Content proof (Rekor):** Webhook payload contains Rekor `logID` and `logIndex`. Registries independently verify the attestation. Authenticates the content.

These are intentionally separate. A spoofed webhook with a valid HMAC but no matching Rekor entry fails content verification. Registries MUST verify both layers before processing.

Registries SHOULD rate-limit webhook calls per source identity and flag anomalous revocation volumes.

**Webhook delivery on private and internal repositories:** The action MUST NOT deliver webhook notifications for `private` or `internal` repositories unless `allow-private-repo-webhook: true` is also set. This is a separate opt-in from `allow-private-repo: true` because they cover distinct disclosures: Rekor permanence (content hash and repo identity are public record) is a different decision from sending that information to a third-party registry operator via webhook. The webhook endpoint is an external party with no inherent relationship to the private repository's access controls.

---

## Badge Integration

```
![MOAT Dual-Attested](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/{owner}/{repo}/moat-attestation/moat-attestation.json)
```

Badge asserts per-hash attestation status. Clients can read `moat-attestation.json` directly to verify specific content hashes without depending on the badge service.

**Badge behavior on private and internal repositories (informative):** The `moat-attestation` branch inherits the source repository's access controls. On a private or internal repository, the branch is not publicly accessible — the badge URL will return 404 for unauthorized requestors. Publishers who enable `allow-private-repo: true` should not expect the badge to render for external viewers.

---

## Private Repository Guard

### Visibility States (normative)

Source repository visibility falls into three states. The action MUST detect visibility at runtime and apply the
corresponding behavior:

| Visibility | GitHub.com / GHES | GitLab (planned future version) | Action behavior |
|---|---|---|---|
| `public` | `GITHUB_REPOSITORY_VISIBILITY=public` | `CI_PROJECT_VISIBILITY=public` | Proceed normally |
| `private` | `GITHUB_REPOSITORY_VISIBILITY=private` | `CI_PROJECT_VISIBILITY=private` | Require `allow-private-repo: true` |
| `internal` | `GITHUB_REPOSITORY_VISIBILITY=internal` (GHES ≥ 3.6) | `CI_PROJECT_VISIBILITY=internal` | Require `allow-private-repo: true` |

The action MUST treat `internal` identically to `private`. `internal` repositories are visible to organization or
enterprise members but not to the public internet — Rekor entries for `internal` repositories still expose content
hashes and repository identity to the public transparency log. The leak concern is the same.

Without `allow-private-repo: true`, the action MUST exit with a non-zero code and a clear error message when detected
visibility is `private` or `internal`.

### Opting In

```yaml
uses: moat-spec/publisher-action@v1
with:
  allow-private-repo: true
  # registry-webhook: ${{ secrets.MOAT_REGISTRY_WEBHOOK }}  # requires allow-private-repo-webhook: true separately
```

When `allow-private-repo: true` is set, the action MUST:

1. Emit a prominent warning in the action log that attestation metadata (content hashes and repository identity) will
   be permanently recorded in the public Rekor transparency log. The content itself is not uploaded, but the metadata
   is irreversibly public.
2. Set `"private_repo": true` in `moat-attestation.json`. This annotation surfaces the private-repo origin to
   registries and conforming clients independently of any configuration — they MAY isolate or reject attestations
   where `private_repo` is `true`.
3. Block webhook delivery unless `allow-private-repo-webhook: true` is also explicitly set. These are separate
   opt-ins because they cover distinct disclosures. See Webhook section.

### Informed Consent Limitation (informative)

The `allow-private-repo: true` flag prevents the fully accidental case — a publisher who did not know they were
running on a private repository or did not understand that Rekor is a public, append-only log. It does not guarantee
that publishers who add the flag have read or understood the implications. In practice, publishers commonly add
configuration flags because an action failed and documentation told them to, without reading the accompanying
warnings.

The `"private_repo": true` annotation in `moat-attestation.json` is the downstream signal that matters. It surfaces
the private-repo origin to registries and clients regardless of whether the publisher understood what they opted into.
Downstream enforcement does not depend on publisher comprehension.

---

## Scope

**Current version:** GitHub Actions only.
**Planned future version:** GitLab CI.
