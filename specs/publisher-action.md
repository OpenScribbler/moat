# Publisher Action Specification

**Version:** 0.1.0 (Draft)
**Requires:** moat-spec.md ≥ 0.4.0
**Part of:** [MOAT Specification](../moat-spec.md)

> The Publisher Action is the primary adoption mechanism for the `Dual-Attested` trust tier. Any source repo adopts it with a single workflow file — no key management, no MOAT-specific knowledge required.

---

## What It Does (on push)

1. Detects source repository visibility. If `private` or `internal` and `allow-private-repo: true` is not set, exits immediately with a non-zero code and a clear error message. See Private Repository Guard.
2. Discovers content items via two-tier model: canonical category directories (`skills/`, `subagents/`, `rules/`, `commands/`) or `moat.yml` if present.
3. Computes content hashes using the MOAT algorithm ([`reference/moat_hash.py`](../reference/moat_hash.py)). Errors (symlinks, empty directories) skip the item with a logged warning.
4. Builds one attestation payload JSON per content item (schema below).
5. Signs each payload with `cosign sign-blob` using Sigstore keyless OIDC. GitHub Actions provides the OIDC token automatically — no keys or secrets required.
6. Rekor creates a transparency log entry. `cosign` returns a bundle file containing `logID` and `logIndex`.
7. Writes/updates `moat-attestation.json` with Rekor references for each attested item, including the `private_repo` field.
8. Pushes `moat-attestation.json` to the `moat-attestation` branch with commit message `chore(moat): update attestation`. If the branch does not exist, the action creates it. The `moat-attestation` branch is never merged into the source branch — it contains only attestation data.
9. If `registry-webhook` is configured and the repository is public, POSTs a signed notification payload to the webhook URL. On private or internal repositories, webhook delivery requires an additional explicit opt-in. See Webhook section.

**Branch isolation note:** The Publisher Action pushes to `moat-attestation`, not to the branch that triggered it. Workflow triggers scoped to `main` (or equivalent) do not fire on pushes to `moat-attestation`, so recursive execution is structurally impossible. Publishers MUST NOT configure the action to trigger on pushes to the `moat-attestation` branch. Unlike the commit-back model, this approach works with standard branch protection on `main` — no PAT or bypass configuration is required.

---

## Attestation Payload Schema (normative)

Each content item produces one payload. This is what gets signed and recorded in Rekor.

```json
{
  "_type": "https://moatspec.org/attestation/v1",
  "item_name": "summarizer-skill",
  "item_type": "skill",
  "content_hash": "sha256:abc123...",
  "source_uri": "https://github.com/alice/my-skills",
  "source_ref": "abc123def456...",
  "attested_at": "2026-04-07T14:00:00Z"
}
```

**Field definitions:**

| Field | Description |
|---|---|
| `_type` | URI identifying this as a MOAT attestation payload. Versioned with schema version. |
| `item_name` | The content item's `name` (basename of content directory, or `name` from `moat.yml`). |
| `item_type` | One of the normative content type identifiers: `skill`, `subagent`, `rules`, `command`. |
| `content_hash` | MOAT content hash in `<alg>:<hex>` format. |
| `source_uri` | Source repository URI (`https://github.com/$GITHUB_REPOSITORY`). |
| `source_ref` | Full commit SHA (`$GITHUB_SHA`). Branch name excluded — branch refs drift; commit SHAs do not. |
| `attested_at` | RFC 3339 UTC timestamp of when the action signed. |

**Rekor entry:** `cosign sign-blob` creates a `hashedrekord` entry. The certificate subject encodes the GitHub Actions OIDC identity:

```
https://github.com/{owner}/{repo}/.github/workflows/moat.yml@refs/heads/main
```

This identity is what registries and `moat-verify` use to confirm the attestation came from a legitimate Publisher Action run on the claimed source repository.

---

## `moat-attestation.json` Format (normative)

Location: `moat-attestation` branch root. One file per repo. The file is never present in the source branch, so it is never included in content hashing — the circular dependency concern from the commit-back model does not apply.

```json
{
  "schema_version": 1,
  "attested_at": "2026-04-07T14:00:00Z",
  "private_repo": false,
  "items": [
    {
      "name": "summarizer-skill",
      "content_hash": "sha256:abc123...",
      "rekor_log_id": "24296fb24b8ad77a...",
      "rekor_log_index": 12345678
    }
  ],
  "revocations": []
}
```

**`private_repo` field:** REQUIRED. `true` when the action ran on a `private` or `internal` repository; `false` for `public`. This annotation is visible to registries and conforming clients — they MAY use it to isolate, flag, or reject attestations from private repositories. Attestations created before this field was added will not have it; conforming registries SHOULD treat absent `private_repo` as unknown visibility rather than assuming public.

---

## Revocation via Publisher Action

Publishers can post signed Rekor revocation entries without waiting for their registry to update. To revoke: add an entry to `moat-attestation.json` revocations and trigger the action. It posts a signed Rekor revocation entry and optionally notifies the registry via webhook.

Publisher revocations are **warnings, not hard blocks.** The registry is the gating authority for hard blocks. This prevents abuse (compromised publisher accounts triggering mass revocations). See [main spec](../moat-spec.md) for full client behavior rules.

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
