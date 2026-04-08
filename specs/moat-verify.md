# moat-verify Specification

**Status:** Pre-spec (extracted from [moat-revised-outline.md](../docs/moat-revised-outline.md))
**Part of:** [MOAT](../docs/moat-revised-outline.md)
**Language:** Python 3.9+
**Dependencies:** `moat_hash.py` (imported as module), `cosign` CLI on PATH, stdlib only

> `moat-verify` allows any user to verify MOAT-attested content without depending on a specific client implementation. It makes the trust model auditable end-to-end.

> **Offline mode (`--lockfile`) — design pending stress test.**
>
> A `--lockfile <path>` mode is planned to support verification of already-installed content without network
> connectivity. Because the lockfile stores an `attestation_bundle`, offline mode can provide the same attestation
> assurance as online verification for the original install state — re-hashing the local directory and verifying
> the stored bundle without any external calls. What it cannot verify is current registry state (revocations,
> superseding versions, trust tier changes).
>
> **Interface under consideration:**
> ```
> moat-verify <directory> --lockfile <path> [--json]
> ```
>
> **Design questions that must be resolved before this is normative:**
>
> 1. **Mutual exclusivity.** If both `--lockfile` and `--registry` are passed, is that exit 2 (input error), or
>    does one silently take precedence? Current lean: exit 2 with an explicit error — they represent different
>    trust paths and should not be combined silently.
>
> 2. **No matching entry.** If the computed hash is not found in the lockfile, is that exit 1 (verification
>    failure — content not in lockfile) or exit 2 (input error — wrong lockfile for this directory)? Current lean:
>    exit 1, because "content not in lockfile" is a verification outcome, not a user input mistake.
>
> 3. **Multiple entries with same content hash.** If the lockfile has two entries with identical `content_hash`
>    values (same content, installed from two different registries), should both be reported or just the first
>    match? Current lean: report all matches — the user should see that the content is attested by multiple sources.
>
> 4. **Multiple entries with same name but different hashes.** If the lockfile has two entries with the same
>    `name` but different `content_hash` values (two versions installed), which entry does the tool use? Current
>    lean: verify against whichever entry's hash matches the computed hash; if neither matches, exit 1. Do not
>    pick by name alone.
>
> 5. **`--source` combined with `--lockfile`.** Publisher attestation in online mode re-fetches
>    `moat-attestation.json` from the source URI. In offline mode there is no network call — publisher attestation
>    from a remote source URI is not possible. Current lean: `--source` is an error when combined with
>    `--lockfile` (exit 2). The `attestation_bundle` in the lockfile already contains the publisher attestation if
>    Dual-Attested content was installed; no separate `--source` flag is needed.
>
> 6. **Exit code 3 applicability.** Exit code 3 covers infrastructure failures (Rekor unreachable, registry
>    unreachable). In offline mode there are no external calls. Does exit code 3 ever apply? Current lean: yes,
>    if the `attestation_bundle` itself is structurally invalid or the cosign verification of the bundle fails for
>    a reason other than hash mismatch — treat that as exit 3 (unexpected data from a stored artifact), not exit 1
>    (clean verification failure).
>
> 7. **NOT-verified block content.** Online mode enumerates: registry trustworthiness, registry signing identity
>    legitimacy, publisher OIDC identity ownership, content safety. Offline mode has a different set. Current lean:
>    ```
>    What this script did NOT verify:
>      - Whether this content has been revoked since installation
>      - Whether a newer version supersedes this one
>      - Whether the registry's trust tier assignment has changed
>      - Whether the registry at <registry-url> is one you should trust
>      - Content safety, malicious behavior, or sandbox escape
>    ```
>
> 8. **`attestation_bundle` verification mechanics.** Online mode calls `cosign verify-blob` against a live Rekor
>    entry. Offline mode must verify the stored bundle without a live Rekor query. The correct tool invocation
>    for offline bundle verification needs to be confirmed (likely `cosign verify-blob --bundle <bundle-file>` with
>    `--offline` flag or equivalent). This must be tested against real cosign behavior before being specified.
>
> Do not add this mode to the normative spec until all eight questions are resolved and the behavior is confirmed
> against a real lockfile and real cosign invocations.

---

## Interface

```bash
moat-verify <directory> --registry <url> [--source <uri>] [--json]
```

| Argument | Required | Description |
|---|---|---|
| `<directory>` | Yes | Path to content directory to verify. |
| `--registry <url>` | Yes | Base URL of registry to verify against. The user decides which registries to trust — `moat-verify` does not evaluate registry trustworthiness. |
| `--source <uri>` | No | Source repository URI for publisher co-attestation. When absent, publisher tier is reported as `NOT REQUESTED` — not a failure. **v1 scope: GitHub repository URIs only.** Passing a non-GitHub URI produces exit code 2 with: `Error: --source URI must be a GitHub repository (https://github.com/<owner>/<repo>). GitLab and other platforms are not supported in v1.` |
| `--json` | No | Emit machine-readable JSON to stdout in addition to human-readable report. |

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | All requested verifications passed. |
| `1` | Verification failed (hash not in manifest, Rekor entry invalid, content hash mismatch). |
| `2` | Input error (directory not found, invalid arguments, unsupported `--source` URI, unknown `schema_version`). |
| `3` | Infrastructure failure (registry unreachable, Rekor unreachable, malformed manifest from remote). |

Exit code 2 indicates the user gave bad input or the tool encountered an unrecognized protocol value — the user can fix it.
Exit code 3 indicates an external system was unavailable or returned unexpected data — the user may need to retry or investigate the registry.

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

Fail with exit code 3 if: registry unreachable; HTTP status not 200; response not valid JSON; response is valid JSON but missing required fields.
Fail with exit code 2 if: `schema_version` present but unknown.

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

**Rekor unavailability MUST produce an explicit failure — never a silent pass.** Exit code 3 (infrastructure failure).

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
