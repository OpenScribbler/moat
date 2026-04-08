# moat-verify Specification

**Status:** Pre-spec (extracted from moat-revised-outline.md)
**Part of:** MOAT v1
**Language:** Python 3.9+
**Dependencies:** `moat_hash.py` (imported as module), `cosign` CLI on PATH, stdlib only

> `moat-verify` allows any user to verify MOAT-attested content without depending on a specific client implementation. It makes the trust model auditable end-to-end.

---

## Interface

```bash
moat-verify <directory> --registry <url> [--source <uri>] [--json]
```

| Argument | Required | Description |
|---|---|---|
| `<directory>` | Yes | Path to content directory to verify. |
| `--registry <url>` | Yes | Base URL of registry to verify against. The user decides which registries to trust — `moat-verify` does not evaluate registry trustworthiness. |
| `--source <uri>` | No | Source repository URI for publisher co-attestation. When absent, publisher tier is reported as `NOT REQUESTED` — not a failure. |
| `--json` | No | Emit machine-readable JSON to stdout in addition to human-readable report. |

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | All requested verifications passed. |
| `1` | Verification failed (hash not in manifest, Rekor entry invalid, Rekor unreachable, content hash mismatch). |
| `2` | Input or protocol error (directory not found, invalid arguments, registry unreachable, malformed manifest). |

---

## Verification Steps

### Step 1: Compute content hash

Apply the MOAT content hashing algorithm (`moat_hash.py::content_hash()`) to `<directory>`.

Fail with exit code 2 if: directory does not exist or is not a directory; directory contains symlinks; directory is empty after VCS directory exclusion.

Output:
```
Content hash: sha256:<hex>
```

### Step 2: Fetch registry manifest

GET `<registry-url>/manifest.json`. MUST be valid JSON with a `schema_version` field.

Fail with exit code 2 if: registry unreachable; HTTP status not 200; response not valid JSON; `schema_version` unknown.

### Step 3: Look up content hash

Search manifest `items` array for an entry whose `content_hash` matches Step 1.

Fail (exit 1) if no match:
```
[✗] Hash not found in registry manifest
    Computed: sha256:<hex>
    Registry: <url>
```

If found:
```
[✓] Hash found in registry manifest
    Name:    <item-name>
    Version: <version or "unset">
    Type:    <item-type>
```

### Step 4: Verify registry Rekor attestation

Read `attestation.rekor_log_id` from the matching manifest item.

**Rekor unavailability MUST produce an explicit failure — never a silent pass.**

```
[✗] Cannot verify Rekor attestation — transparency log unreachable
    Rekor URL: https://rekor.sigstore.dev
    This is a hard failure. moat-verify will never pass without Rekor verification.
```

Verification:
1. Extract payload hash from entry. Compare to computed content hash. Fail if mismatch.
2. Verify entry signature against embedded certificate using `cosign verify-blob`. Fail if verification fails.
3. Extract signing identity from verified certificate.

```
[✓] Registry Rekor attestation verified
    Log ID:    <rekor-log-id>
    Log Index: <index>
    Signer:    <certificate-subject>
```

### Step 5: Publisher attestation (conditional on `--source`)

If `--source` not provided:
```
Publisher attestation: NOT REQUESTED
(Pass --source <uri> to verify publisher CI attestation)
```

If `--source <uri>` provided:

Fetch `<source-uri>/raw/main/moat-attestation.json`. v1 scope: GitHub repository URIs only.

Fail (exit 1) if: source URI unreachable; `moat-attestation.json` missing or malformed; no matching `content_hash` entry.

Verify the Rekor entry using the same procedure as Step 4, plus: verify certificate OIDC issuer is `https://token.actions.githubusercontent.com` and certificate subject matches:
```
https://github.com/<owner>/<repo>/.github/workflows/moat.yml@refs/heads/<branch>
```

**`moat-verify` MUST report the actual OIDC identity found — it MUST NOT decide whether this identity is the legitimate owner of the source repository. That decision belongs to the user.**

```
[✓] Publisher Rekor attestation verified
    Log ID:        <rekor-log-id>
    Log Index:     <index>
    OIDC Identity: https://github.com/alice/my-skills/.github/workflows/moat.yml@refs/heads/main
```

---

## Trust Result

| Conditions | Result |
|---|---|
| Step 4 passed, Step 5 `NOT REQUESTED` | `SIGNED` |
| Steps 4 and 5 both passed | `DUAL-ATTESTED` |
| Any step failed | `FAILED` |

---

## Required "NOT Verified" Block

At the end of every run — including failures — `moat-verify` MUST output:

```
What this script did NOT verify:
  - Whether the registry at <url> is one you should trust
  - Whether the registry signing identity is the legitimate operator of this registry
  - Whether the publisher OIDC identity is the legitimate owner of this source repository
  - Content safety, malicious behavior, or sandbox escape
```

Implementations that omit this block do not conform. Its purpose is to prevent users from mistaking cryptographic verification for a safety guarantee.

---

## JSON Output (`--json`)

```json
{
  "schema_version": "1",
  "content_hash": "sha256:abc123...",
  "registry": "https://registry.example.com",
  "result": "SIGNED",
  "steps": {
    "hash_computed": true,
    "manifest_fetched": true,
    "hash_found_in_manifest": true,
    "registry_rekor_verified": true,
    "publisher_rekor_verified": null
  },
  "registry_attestation": {
    "rekor_log_id": "24296fb24b8ad77a...",
    "rekor_log_index": 12345678,
    "signer": "did:web:registry.example.com"
  },
  "publisher_attestation": null,
  "not_verified": [
    "registry trustworthiness",
    "registry signing identity legitimacy",
    "publisher OIDC identity ownership",
    "content safety"
  ],
  "error": null
}
```

`steps` values: `true` = passed, `false` = failed, `null` = not attempted. `publisher_rekor_verified` is `null` when `--source` was not provided.
