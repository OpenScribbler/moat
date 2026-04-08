# Publisher Action Specification

**Status:** Pre-spec (extracted from [moat-revised-outline.md](../docs/moat-revised-outline.md))
**Part of:** [MOAT](../docs/moat-revised-outline.md)

> The Publisher Action is the primary adoption mechanism for the `Dual-Attested` trust tier. Any source repo adopts it with a single workflow file — no key management, no MOAT-specific knowledge required.

---

## What It Does (on push)

1. Discovers content items via two-tier model: canonical category directories (`skills/`, `agents/`, `rules/`, `commands/`) or `moat.yml` if present.
2. Computes content hashes using the MOAT algorithm (`moat_hash.py`). Errors (symlinks, empty directories) skip the item with a logged warning.
3. Builds one attestation payload JSON per content item (schema below).
4. Signs each payload with `cosign sign-blob` using Sigstore keyless OIDC. GitHub Actions provides the OIDC token automatically — no keys or secrets required.
5. Rekor creates a transparency log entry. `cosign` returns a bundle file containing `logID` and `logIndex`.
6. Writes/updates `moat-attestation.json` with Rekor references for each attested item.
7. Pushes `moat-attestation.json` to the `moat-attestation` branch with commit message `chore(moat): update attestation`. If the branch does not exist, the action creates it. The `moat-attestation` branch is never merged into the source branch — it contains only attestation data.
8. If `registry-webhook` is configured, POSTs a signed notification payload to the webhook URL.

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
| `attested_at` | ISO 8601 UTC timestamp of when the action signed. |

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
  "schema_version": "1",
  "attested_at": "2026-04-07T14:00:00Z",
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

---

## Revocation via Publisher Action

Publishers can post signed Rekor revocation entries without waiting for their registry to update. To revoke: add an entry to `moat-attestation.json` revocations and trigger the action. It posts a signed Rekor revocation entry and optionally notifies the registry via webhook.

Publisher revocations are **warnings, not hard blocks.** The registry is the gating authority for hard blocks. This prevents abuse (compromised publisher accounts triggering mass revocations). See [main spec](../docs/moat-revised-outline.md) for full client behavior rules.

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

---

## Badge Integration

```
![MOAT Dual-Attested](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/{owner}/{repo}/moat-attestation/moat-attestation.json)
```

Badge asserts per-hash attestation status. Clients can read `moat-attestation.json` directly to verify specific content hashes without depending on the badge service.

---

## Private Repository Guard

The Publisher Action MUST detect source repository visibility before signing. If the source repository is private, the
action MUST NOT proceed unless the publisher has explicitly opted in via workflow configuration:

```yaml
uses: moat-spec/publisher-action@v1
with:
  allow-private-repo: true
```

Without this opt-in, the action MUST exit with a non-zero code and a clear error message when run on a private
repository.

**Why this matters:** Rekor is a public, append-only transparency log. Running the Publisher Action on a private
repository — even with `allow-private-repo: true` — creates permanent public records containing the content hash and
repository identity. The content itself is not uploaded, but the metadata is irreversibly public. Publishers who opt
in on a private repository MUST understand this before proceeding. The action SHOULD emit a prominent warning when
`allow-private-repo: true` is set, reminding the publisher that attestation metadata will become permanent public
record.

---

## Scope

**v1:** GitHub Actions only.
**v1.1 target:** GitLab CI.
