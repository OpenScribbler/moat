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
6. Writes/updates `moat-attestation.json` at repo root with Rekor references for each attested item.
7. Commits `moat-attestation.json` back to the repo with commit message `chore(moat): update attestation [skip ci]`.
8. If `registry-webhook` is configured, POSTs a signed notification payload to the webhook URL.

**Bootstrapping note:** GitHub Actions using `GITHUB_TOKEN` do not trigger other workflow runs by default, preventing infinite loops. The action MUST include an explicit guard against re-runs triggered by its own commits.

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

Location: repo root. One file per repo. MUST be excluded from content hashing (including it creates a circular dependency — the hash changes when attestation is written, requiring a new hash, ad infinitum).

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
![MOAT Dual-Attested](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/{owner}/{repo}/main/moat-attestation.json)
```

Badge asserts per-hash attestation status. Clients can read `moat-attestation.json` directly to verify specific content hashes without depending on the badge service.

---

## Scope

**v1:** GitHub Actions only.
**v1.1 target:** GitLab CI.
