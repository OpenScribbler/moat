# Registry Action Specification

**Version:** 0.1.0 (Draft)
**Requires:** moat-spec.md ≥ 0.5.0
**Part of:** [MOAT Specification](../moat-spec.md)

> The Registry Action is the standard mechanism for producing a MOAT registry manifest. Any GitHub repository becomes a registry with a single workflow file and a `registry.yml` config — no key management, no MOAT-specific knowledge required.

---

## What It Does (on schedule / on `registry.yml` change)

1. Reads `registry.yml` at the repository root. If the file is absent or invalid, exits non-zero with a clear error message identifying the violation.
2. For each source URI in `sources`:
   a. Fetches the source repository at HEAD using an authenticated GitHub API request. Source failures (network error, non-existent repo, rate limit) are non-fatal — the run continues and the failure is logged per source.
   b. Checks source repository visibility. If private and `allow-private-source: true` is not set, skips the source with a warning. See Private Repository Guard.
   c. Attempts to fetch `moat-attestation.json` from the source's `moat-attestation` branch. If the branch or file does not exist, the source contributes Signed items only.
3. Discovers content items from each source via the same two-tier model as the Publisher Action: canonical category directories (`skills/`, `subagents/`, `rules/`, `commands/`) or `moat.yml` if present.
4. Computes content hashes for all discovered items using the MOAT algorithm ([`reference/moat_hash.py`](../reference/moat_hash.py)).
5. Determines trust tier per item. See Trust Tier Determination.
6. Signs each Signed or Dual-Attested item's canonical payload with `cosign sign-blob` using Sigstore keyless OIDC. GitHub Actions provides the OIDC token automatically — no keys or secrets required. Records the Rekor `logIndex` per item.
7. Assembles the registry manifest (`registry.json`) with all indexed items, revocations (registry-initiated from `registry.yml` plus publisher-initiated from `moat-attestation.json` sources), and metadata fields including the runtime-derived `registry_signing_profile`.
8. Signs the assembled manifest with `cosign sign-blob`. The resulting bundle is written to `registry.json.sigstore` alongside `registry.json`.
9. Pushes `registry.json` and `registry.json.sigstore` to the `moat-registry` branch with commit message `chore(moat): update registry manifest`. If the branch does not exist, the action creates it as an orphan. The `moat-registry` branch is never merged into the source branch — it contains only manifest data.

**Branch isolation note:** The Registry Action pushes to `moat-registry`, not to the branch that triggered it. Pushes to `moat-registry` do not re-trigger the action, so recursive execution is structurally impossible. Registry operators MUST NOT configure the action to trigger on pushes to the `moat-registry` branch. The action MUST be configured with a schedule trigger (e.g., daily) as its primary crawl mechanism and SHOULD include `workflow_dispatch` for manual runs. The `paths: ['registry.yml']` push trigger is intentional — it makes an emergency revocation (editing `registry.yml`) immediately kick off a run.

**All-sources-fail behavior:** If every source in `sources` fails to return content, the action MUST exit non-zero. A run that contacts no sources successfully produces no manifest update and must not silently succeed.

---

## `registry.yml` Config Format (normative)

```yaml
schema_version: 1

registry:
  name: my-registry           # lowercase letters, digits, hyphens only
  operator: My Name or Org
  manifest_uri: https://raw.githubusercontent.com/owner/repo/main/registry.json

sources:
  - uri: https://github.com/alice/ai-skills
  - uri: https://github.com/bob/agent-rules
    allow-private-source: true  # see Private Repository Guard

revocations: []
```

**Field definitions:**

| Field | Required | Description |
|---|---|---|
| `schema_version` | REQUIRED | Config format version; currently `1` (integer). If absent or unrecognized, the action MUST exit non-zero. |
| `registry.name` | REQUIRED | Machine identifier for this registry. Constraint: lowercase letters (`a-z`), digits (`0-9`), hyphens (`-`). If the constraint is violated, the action MUST exit non-zero. |
| `registry.operator` | REQUIRED | Human-readable name of the registry operator. |
| `registry.manifest_uri` | REQUIRED | Canonical URL at which `registry.json` will be hosted. Used as the manifest's `manifest_uri` field. MUST be a stable path-based URL with no query parameters or fragments. |
| `sources[].uri` | REQUIRED | Source repository URI. One entry per source repository. |
| `sources[].allow-private-source` | OPTIONAL | `true` to permit indexing of private or internal repositories. Absent is equivalent to `false`. See Private Repository Guard. |
| `revocations` | OPTIONAL | Array of registry-initiated revocation entries. Absent is equivalent to an empty array. |
| `revocations[].content_hash` | REQUIRED | Hash of the revoked content item in `<alg>:<hex>` format. |
| `revocations[].reason` | REQUIRED | One of: `malicious`, `compromised`, `deprecated`, `policy_violation`. |
| `revocations[].details_url` | REQUIRED | URL to public revocation details. |

**Emergency revocation path:** The Registry Action triggers on pushes to `registry.yml`. Adding a revocation entry to `registry.yml` and pushing immediately triggers a run, propagating the hard block to the manifest without waiting for the next scheduled crawl. This is the normative fast path for urgent registry-initiated revocations.

---

## Trust Tier Determination (normative)

For each discovered content item, the action applies these rules in order:

1. **No registry Rekor entry** → `Unsigned`. The action does not sign the item. (Reserved for future use; the current action signs all indexed items.)
2. **Registry Rekor entry only** → `Signed`. Applied when:
   - No `moat-attestation.json` was found on the source's `moat-attestation` branch, or
   - Publisher Rekor verification failed for this item (see below), or
   - The action's computed hash differs from the hash in `moat-attestation.json` (see Hash Mismatch below).
3. **Registry Rekor entry + verified publisher Rekor entry** → `Dual-Attested`.

**Publisher Rekor verification procedure:** To qualify an item as Dual-Attested, the action MUST verify the publisher's Rekor entry by:

1. Locating the item's `rekor_log_index` in `moat-attestation.json`.
2. Fetching the Rekor entry at that index from the transparency log.
3. Confirming the entry's certificate OIDC issuer is `https://token.actions.githubusercontent.com`.
4. Confirming the entry's certificate OIDC subject matches the expected publisher subject, constructed from the
   source URI and the `publisher_workflow_ref` field in `moat-attestation.json`:
   ```
   https://github.com/{owner}/{repo}/{publisher_workflow_ref}
   ```
   where `{owner}` and `{repo}` are derived from the source `uri`, and `{publisher_workflow_ref}` is read from
   `moat-attestation.json` (e.g., `.github/workflows/moat.yml@refs/heads/main`). If `publisher_workflow_ref` is
   absent — attestations written before the field was introduced — the action MUST fall back to
   `.github/workflows/moat.yml@refs/heads/main`.

5. Confirming the signed payload in the Rekor entry decodes to a valid MOAT attestation payload (see [Per-Item Canonical Payload](#per-item-canonical-payload)) with a `content_hash` matching the action's computed hash.

If any step fails, the item falls back to `Signed`. The fallback is non-fatal for the run, but the action MUST log a clear, actionable message identifying the item, the failure step, and the expected vs. observed values. Example:

```
Publisher Rekor verification failed for skills/my-skill (log index 12345678):
  Expected OIDC subject: https://github.com/alice/my-skills/.github/workflows/moat.yml@refs/heads/main
  Observed OIDC subject: https://github.com/alice/my-skills/.github/workflows/ci.yml@refs/heads/main
  Item will be indexed as Signed.
```

**Hash mismatch:** If the action's computed hash for an item differs from the hash recorded in `moat-attestation.json`, the action's computed hash is authoritative. The item is indexed at the computed hash, the trust tier falls to `Signed`, and the action MUST log a warning identifying the item and both hash values. The mismatch MUST be recorded in the manifest entry — see `content[].attestation_hash_mismatch` in the manifest format.

---

## Per-Item Canonical Payload

Each Signed or Dual-Attested item is attested with one registry-signed payload. This payload is structurally identical to the per-item attestation payload defined in the main spec:

```json
{"_version":1,"content_hash":"sha256:<hex>"}
```

Serialization rules: UTF-8, no BOM, no trailing newline, no insignificant whitespace, lexicographic key order. The payload MUST be identical to the one produced by `moat-verify` for the same item. See [main spec attestation payload](../moat-spec.md#per-item-attestation-payload) for the full canonical form and test vector.

**Registry Rekor entry:** `cosign sign-blob` creates a `hashedrekord` entry. The certificate subject encodes the GitHub Actions OIDC identity for the Registry Action workflow:

```
https://github.com/{owner}/{repo}/.github/workflows/moat-registry.yml@refs/heads/main
```

This identity is what `moat-verify` and conforming clients use to confirm registry attestations came from a legitimate Registry Action run on the declared registry repository.

**`registry_signing_profile` derivation:** The action derives the registry's signing identity from its own OIDC token at runtime and writes it to the manifest's `registry_signing_profile` field automatically. Registry operators do not declare their signing identity in `registry.yml` — the OIDC token is the authoritative source and self-declaration is redundant and error-prone.

---

## Revocation Handling

The manifest's `revocations` array is populated from two sources per run:

**Registry-initiated revocations** — from the `revocations` array in `registry.yml`. These are hard blocks for conforming clients. The `source` field is set to `"registry"`.

**Publisher-initiated revocations** — from the `revocations` array in each source's `moat-attestation.json`. These are warnings for conforming clients. The `source` field is set to `"publisher"`.

When both a registry-initiated and publisher-initiated revocation exist for the same content hash, the registry-initiated entry takes precedence and the publisher entry is omitted from the manifest.

Revocation entries from `moat-attestation.json` are propagated on each scheduled crawl. The maximum propagation delay for publisher-initiated revocations is equal to the registry's crawl interval (the time between scheduled runs). Registry operators SHOULD configure a crawl interval of 24 hours or less. For urgent revocations requiring immediate propagation, publishers SHOULD contact the registry operator directly — registry-initiated revocation via `registry.yml` push is the normative fast path.

---

## Self-Publishing

A publisher may run both the Publisher Action and the Registry Action from the same repository. This produces valid `Dual-Attested` content even within a single repo.

The independence guarantee comes from the OIDC subject binding, not from organizational separation. The two workflow files produce two distinct OIDC subjects:

- Publisher Action: `.../{publisher_workflow_ref}` (default: `.github/workflows/moat.yml@refs/heads/main`)
- Registry Action: `.../.github/workflows/moat-registry.yml@refs/heads/main`

These map to two distinct, independently verifiable Rekor entries. Compromising one workflow's execution context does not automatically compromise the other.

**Assurance caveat:** Self-publishing Dual-Attested provides integrity, tamper evidence, and replay protection. It does not provide the organizational independence that cross-repo Dual-Attested provides: both OIDC identities are accessible to anyone with push access to the repository. End Users who require organizational independence between publisher and registry operator MUST use separate repositories controlled by separate GitHub accounts or organizations.

**Disclosure:** When the Registry Action detects that the registry repository URI matches a source URI (self-publishing), it MUST set `self_published: true` in the manifest. Conforming clients SHOULD surface this to End Users so they can make an informed trust decision.

---

## Private Repository Guard

Source repository visibility is checked at crawl time. The action applies three-state logic identical to the Publisher Action:

| Visibility | Detection | Action behavior |
|---|---|---|
| `public` | Repository accessible to unauthenticated requests | Proceed normally |
| `private` | Repository returns 403/404 to unauthenticated requests, OR `private_repo: true` in `moat-attestation.json` | Requires `allow-private-source: true` on the source entry in `registry.yml` |
| `internal` | Same as `private` | Requires `allow-private-source: true` |

Without `allow-private-source: true`, the action MUST skip the source and emit a warning. It MUST NOT fail the run — other sources continue normally.

With `allow-private-source: true`, the action indexes content from the private source and sets `private_repo: true` on all manifest entries from that source. Conforming clients MAY isolate, warn on, or reject content where `private_repo` is `true`.

**Note on `private_repo: true` in `moat-attestation.json`:** This field is authored by the publisher and is advisory. The normative visibility check is the action's unauthenticated-request probe at crawl time. The `private_repo` field in `moat-attestation.json` MAY add restriction (a public repo that declares itself private-for-indexing) but MUST NOT override API-reported visibility in the permissive direction.

---

## Scope

**Current version:** GitHub Actions only. Source repositories must be hosted on GitHub.com or GitHub Enterprise Server.
**Planned future version:** GitLab CI.
