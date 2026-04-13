---
title: "moat-verify"
description: "Specification for the moat-verify standalone verification tool."
---

:::note[Spec metadata]
**Version:** 0.1.0 (Draft) · **Requires:** moat-spec.md ≥ 0.5.0 · **Language:** Python 3.9+ · **Dependencies:** `reference/moat_hash.py` (imported as module), `cosign` CLI on PATH, stdlib only
:::

`moat-verify` allows any End User to verify MOAT-attested content without depending on a specific client implementation.
It makes the trust model auditable end-to-end.

---

## Interface

`moat-verify` operates in two mutually exclusive modes. `--registry` and `--lockfile` MUST NOT be combined — they answer different questions and passing both is exit 2 with the message:

> `--lockfile` verifies against your stored install snapshot; `--registry` verifies against current registry state. They answer different questions — run one at a time.

### Online mode

```bash
moat-verify <directory> --registry <url> [--source <uri>] [--json]
```

Verifies against the current live registry state. Can detect revocations, trust tier changes, and current attestation status.

| Argument           | Required | Description                                                                                                                                                                                                                                                                                                                                                                  |
|--------------------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `<directory>`      | Yes      | Path to content directory to verify.                                                                                                                                                                                                                                                                                                                                         |
| `--registry <url>` | Yes      | Manifest URL of the registry to verify against — the `manifest_uri` from the registry manifest. The End User decides which registries to trust — `moat-verify` does not evaluate registry trustworthiness.                                                                                                                                                                   |
| `--source <uri>`   | No       | Source repository URI for publisher co-attestation. When absent, publisher tier is reported as `NOT REQUESTED` — not a failure. **Current scope: GitHub repository URIs only.** Passing a non-GitHub URI produces exit code 2 with: `Error: --source URI must be a GitHub repository (https://github.com/<owner>/<repo>). GitLab and other platforms are not yet supported.` |
| `--json`           | No       | Emit machine-readable JSON to stdout in addition to human-readable report.                                                                                                                                                                                                                                                                                                   |

### Offline mode

```bash
moat-verify <directory> --lockfile <path> [--json]
```

Verifies against the stored install snapshot. Proves "this content was valid when installed" — cannot detect revocations, tier changes, or current registry state. See [Required "NOT Verified" Block](#required-not-verified-block) for the full list of what offline mode cannot cover.

| Argument            | Required | Description                                                                        |
|---------------------|----------|------------------------------------------------------------------------------------|
| `<directory>`       | Yes      | Path to content directory to verify.                                               |
| `--lockfile <path>` | Yes      | Path to the MOAT lockfile written by the conforming client at install time.        |
| `--json`            | No       | Emit machine-readable JSON to stdout in addition to human-readable report.         |

`--source` is not valid in offline mode — passing it with `--lockfile` is exit 2. Publisher attestation from install time is already captured in the lockfile's `attestation_bundle` for Dual-Attested content. If the content was installed as Signed (no publisher bundle), exit 2 MUST include: *"Content was installed as Signed — no publisher attestation bundle is available."*

---

## Exit Codes

| Code | Online mode                                                                                           | Offline mode                                                                                                                       |
|------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| `0`  | All verifications passed.                                                                             | All verifications passed.                                                                                                          |
| `1`  | Verification failed: hash not in manifest, Rekor entry invalid, content hash mismatch.               | Verification failed: hash not in lockfile, content hash mismatch, bundle signature validation failed.                              |
| `2`  | Input error: bad directory, invalid arguments, unsupported `--source` URI, unknown `schema_version`. | Input error: bad directory, lockfile not found or malformed, `--source` + `--lockfile` combined, `--registry` + `--lockfile` combined, unknown `moat_lockfile_version`. |
| `3`  | Infrastructure failure: registry unreachable, Rekor unreachable, malformed manifest from remote.     | Corrupt stored artifact: `attestation_bundle` structurally invalid, or cosign signature error not attributable to hash mismatch. Recovery: re-run with `--registry`. |

**Exit code 2** means the End User gave invalid input — they can fix it by correcting their invocation or providing valid files.

**Exit code 3** means something outside the End User's control produced bad data. In online mode, an external service failed. In offline mode, the stored attestation bundle is corrupt. Recovery requires re-verifying with `--registry`.

**Mapping cosign exit codes (offline mode):** `cosign verify-blob` returns exit 1 for both hash mismatch and invalid signature. moat-verify MUST inspect cosign's stderr to determine the correct exit code:
- `invalid signature when validating ASN.1 encoded signature` in stderr → moat-verify exit 3
- Any other non-zero cosign exit → moat-verify exit 1

---

## Online Verification Steps

### Step 1: Compute content hash

Apply the MOAT content hashing algorithm (`reference/moat_hash.py::content_hash()`) to `<directory>`.

Fail with exit code 2 if: directory does not exist or is not a directory; directory contains symlinks; directory is
empty after VCS directory exclusion.

Output:
```
Content hash: sha256:<hex>
```

### Step 2: Fetch and verify registry manifest

**Fetch:** GET the manifest at the URL provided via `--registry`. MUST be valid JSON with all required top-level
fields present: `schema_version`, `manifest_uri`, `registry_signing_profile`, `content`, `revocations`.

Fail with exit code 3 if: registry unreachable; HTTP status not 200; response not valid JSON; required top-level fields
missing. Fail with exit code 2 if: `schema_version` present but unrecognized.

If the manifest's `manifest_uri` does not match the `--registry` URL, surface as a warning but do not fail —
CDN and proxy configurations may legitimately serve a manifest from a URL that differs from its declared canonical
URI.

**Verify manifest bundle:** Fetch the bundle at `{manifest_uri}.sigstore`. Verify:
1. The bundle covers the exact bytes of the fetched manifest file
2. The signing certificate's OIDC issuer and subject match `registry_signing_profile`
3. The Rekor transparency log entry in the bundle is valid

**Rekor unavailability is a hard failure — never a silent pass.** Exit code 3 (infrastructure failure).

```
[✗] Cannot verify manifest bundle — transparency log unreachable
    Rekor URL: https://rekor.sigstore.dev
    This is a hard failure. moat-verify will never pass without Rekor verification.
```

On success:

```
[✓] Registry manifest verified
    Registry: <manifest_uri>
    Name:     <name>
    Operator: <operator>
    Updated:  <updated_at>
    Signer:   <registry_signing_profile.subject> (<registry_signing_profile.issuer>)
```

### Step 3: Look up content hash

Search manifest `content` array for an entry whose `content_hash` matches Step 1.

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

### Step 4: Verify per-item Rekor attestation

Read `rekor_log_index` from the matching manifest entry. If the entry has no `rekor_log_index`, the item is
Unsigned — skip this step and record the trust result as `UNSIGNED` (see Trust Result).

**Rekor unavailability MUST produce an explicit failure — never a silent pass.** Exit code 3 (infrastructure failure).

```
[✗] Cannot verify per-item Rekor attestation — transparency log unreachable
    Rekor URL: https://rekor.sigstore.dev
    This is a hard failure. moat-verify will never pass without Rekor verification.
```

Verification:
1. Fetch the Rekor entry at `rekor_log_index`. Fail with exit 3 if unreachable.
2. Reconstruct the canonical per-item payload: `{"_version":1,"content_hash":"<computed-hash>"}` (UTF-8,
   no whitespace, no trailing newline, keys in lexicographic order). Compute its SHA-256 and compare to the
   data hash in the Rekor entry's `hashedrekord` body. Fail with exit 1 if mismatch — the Rekor entry does
   not attest the computed content hash. Implementations SHOULD check whether the space-padded form of this
   payload matches and, if so, emit an informational hint in the failure message (does not change the exit code).
3. Reconstruct a Sigstore bundle from the Rekor entry response and write the canonical payload to a temporary file.
   Verify entry signature against the embedded certificate using `cosign verify-blob`. Fail with exit 1 if
   verification fails.
4. Extract OIDC signing identity from the verified certificate.
5. Verify the signer identity matches the manifest's `registry_signing_profile`. The signing certificate's OIDC
   issuer MUST equal `registry_signing_profile.issuer` and the subject MUST equal `registry_signing_profile.subject`.
   Fail with exit 1 if either does not match — a different signing identity means this Rekor entry was not created
   by the registry operator declared in the manifest.

```
[✓] Per-item Rekor attestation verified
    Log Index: <rekor_log_index>
    Signer:    <certificate-subject> (<certificate-issuer>)
```

### Step 5: Publisher attestation (conditional on `--source`)

If `--source` not provided:
```
Publisher attestation: NOT REQUESTED
(Pass --source <uri> to verify publisher CI attestation)
```

If `--source <uri>` provided:

Fetch `<source-uri>/raw/main/moat-attestation.json`. Current scope: GitHub repository URIs only.

Fail (exit 1) if: source URI unreachable; `moat-attestation.json` missing or malformed; no matching `content_hash` entry.

Verify the Rekor entry using the same procedure as Step 4, plus: verify certificate OIDC issuer is
`https://token.actions.githubusercontent.com` and certificate subject matches:
```
https://github.com/<owner>/<repo>/.github/workflows/moat.yml@refs/heads/<branch>
```

**`moat-verify` MUST report the actual OIDC identity found — it MUST NOT decide whether this identity is the legitimate
owner of the source repository. That decision belongs to the End User.**

```
[✓] Publisher Rekor attestation verified
    Log ID:        <rekor-log-id>
    Log Index:     <index>
    OIDC Identity: https://github.com/alice/my-skills/.github/workflows/moat.yml@refs/heads/main
```

---

## Offline Verification Steps (`--lockfile` mode)

### Step 1: Compute content hash

Identical to [online Step 1](#step-1-compute-content-hash). Apply `reference/moat_hash.py::content_hash()` to `<directory>`. Same failure conditions and output format.

### Step 2: Parse lockfile

Load and validate the lockfile at `--lockfile <path>`.

Fail with exit code 2 if: file not found or not readable; content is not valid JSON; top-level field `moat_lockfile_version` is absent or unrecognized; top-level field `entries` is absent or not an array.

Output:
```
Lockfile: <path> (version: <moat_lockfile_version>, <N> entries)
```

### Step 3: Look up content hash

Search all entries in `entries` for a matching `content_hash`.

**No match:** Exit 1.
```
[✗] Hash not found in lockfile
    Computed:  sha256:<hex>
    Lockfile:  <path>

    This means either: the content was modified after installation, or
    this lockfile does not correspond to this directory.
    moat-verify cannot distinguish between these cases.
```

**Multiple entries with the same `content_hash`** (same content attested by multiple registries): verify all matching entries (Step 4 for each). Report each separately. Exit code is the worst outcome — exit 1 if any attestation fails.

**Multiple entries with the same `name` but different `content_hash` values:** match by hash, not by name.
- Computed hash matches one entry → proceed with that entry.
- Computed hash matches no entries → exit 1 (same message as no match above).
- Two entries share identical `content_hash` values → exit 2, malformed lockfile.

On match:
```
[✓] Hash found in lockfile
    Name:       <name>
    Type:       <type>
    Registry:   <registry>
    Attested:   <attested_at>
    Trust tier: <trust_tier>
```

### Step 4: Verify attestation bundle (offline)

**If `trust_tier` is `UNSIGNED`:** Skip. Record trust result as `UNSIGNED`.

**Otherwise:**

Write the entry's `attestation_bundle` to a temporary file. Write the entry's `signed_payload` to a second temporary file. Run:

```
cosign verify-blob \
  --bundle <bundle-temp> \
  --offline \
  --certificate-identity-regexp .* \
  --certificate-oidc-issuer-regexp .* \
  <payload-temp>
```

Cleanup both temporary files regardless of outcome.

**cosign exit 0:**
```
[✓] Attestation bundle verified (offline)
    Signer: <certificate-subject> (<certificate-issuer>)
    Note:   Rekor entry logged at install time — not re-queried
```

**cosign exit non-0 with `invalid signature when validating ASN.1 encoded signature` in stderr:** Exit 3.
```
[✗] Attestation bundle is corrupt
    The attestation_bundle stored in the lockfile cannot be verified.
    This is not a content integrity failure — the stored bundle itself is damaged.
    Recovery: re-run with --registry <url> to verify against current registry state.
```

**cosign exit non-0 with any other error:** Exit 1.

**`moat-verify` MUST report the actual OIDC identity found — it MUST NOT decide whether that identity is legitimate. That decision belongs to the End User.**

---

## Trust Result

| Conditions                                                    | Result          |
|---------------------------------------------------------------|-----------------|
| Step 4 skipped (no `rekor_log_index`), Step 5 `NOT REQUESTED` | `UNSIGNED`      |
| Step 4 passed, Step 5 `NOT REQUESTED`                         | `SIGNED`        |
| Steps 4 and 5 both passed                                     | `DUAL-ATTESTED` |
| Any step failed                                               | `FAILED`        |

---

## Required "NOT Verified" Block

At the end of every run — including failures — `moat-verify` MUST output the NOT-verified block appropriate to the mode used. Implementations that omit this block do not conform. Its purpose is to prevent End Users from mistaking cryptographic verification for a safety or freshness guarantee.

### Online mode

```
What this script did NOT verify:
  - Whether the registry at <url> is one you should trust
  - Whether the registry signing identity is the legitimate operator of this registry
  - Whether the publisher OIDC identity is the legitimate owner of this source repository
  - Content safety, malicious behavior, or sandbox escape
```

### Offline mode

```
This verification reflects content state at install time only.

What this script did NOT verify:
  - Whether this content has been revoked since installation
  - Whether the registry's trust tier assignment has changed
  - Whether the registry signing identity is still the current operator
  - Whether a newer version supersedes this one
  - Whether the registry at <registry-url> is one you should trust
  - Content safety, malicious behavior, or sandbox escape
```

---

## JSON Output (`--json`)

### Online mode

```json
{
  "schema_version": 1,
  "mode": "online",
  "content_hash": "sha256:abc123...",
  "registry": "https://example.com/moat-manifest.json",
  "result": "SIGNED",
  "steps": {
    "hash_computed": true,
    "manifest_fetched": true,
    "manifest_bundle_verified": true,
    "hash_found_in_manifest": true,
    "item_rekor_verified": true,
    "publisher_rekor_verified": null
  },
  "registry_attestation": {
    "rekor_log_index": 12345678,
    "signer_subject": "repo:owner/repo:ref:refs/heads/main",
    "signer_issuer": "https://token.actions.githubusercontent.com"
  },
  "item_attestation": {
    "rekor_log_index": 87654321,
    "signer_subject": "repo:owner/repo:ref:refs/heads/main",
    "signer_issuer": "https://token.actions.githubusercontent.com"
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

`steps` values: `true` = passed, `false` = failed, `null` = not attempted. `publisher_rekor_verified` is `null` when `--source` was not provided. `manifest_bundle_verified` covers the registry-level Rekor check (Step 2); `item_rekor_verified` covers the per-item Rekor check (Step 4).

### Offline mode

```json
{
  "schema_version": 1,
  "mode": "offline",
  "content_hash": "sha256:abc123...",
  "lockfile": "/path/to/moat.lock",
  "result": "SIGNED",
  "steps": {
    "hash_computed": true,
    "lockfile_parsed": true,
    "hash_found_in_lockfile": true,
    "bundle_verified": true
  },
  "bundle_attestation": {
    "signer_subject": "repo:owner/repo:ref:refs/heads/main",
    "signer_issuer": "https://token.actions.githubusercontent.com",
    "verified_offline": true
  },
  "not_verified": [
    "revocation status since installation",
    "registry trust tier changes since installation",
    "registry signing identity currency",
    "superseding versions",
    "registry trustworthiness",
    "content safety"
  ],
  "error": null
}
```

`steps` values: `true` = passed, `false` = failed, `null` = not attempted. `bundle_verified` is `null` when `trust_tier` in the lockfile entry is `UNSIGNED`. `mode` field distinguishes online and offline runs in automated pipelines.
