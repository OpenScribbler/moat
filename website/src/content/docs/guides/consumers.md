---
title: Consumer guide
description: How to verify AI agent content using moat-verify.
---

`moat-verify` is a standalone script that lets you verify MOAT-attested content without depending on any particular client implementation. It is the reference implementation of the [moat-verify spec](/spec/moat-verify).

The source is at [`reference/moat_verify.py`](https://github.com/OpenScribbler/moat/blob/main/reference/moat_verify.py).

---

## Prerequisites

```bash
# Python 3.9+
python3 --version

# cosign (Sigstore) — used for signature verification
cosign version

# openssl — used to extract OIDC identity from certificates
openssl version
```

All three must be on PATH. `cosign` installation: https://docs.sigstore.dev/cosign/system_config/installation/

You also need [`reference/moat_hash.py`](https://github.com/OpenScribbler/moat/blob/main/reference/moat_hash.py) in the same directory as `moat_verify.py`, or importable on your Python path — `moat-verify` imports it as a module.

---

## Two modes

`moat-verify` operates in two mutually exclusive modes. Use `--registry` or `--lockfile`, not both.

### Online mode — verify against current registry state

```bash
python3 moat_verify.py <directory> --registry <url>
```

Fetches the registry manifest, verifies its signature, then checks whether the content directory's hash is in the manifest and has a valid Rekor attestation. Can detect revocations and trust tier changes.

| Argument | Required | Description |
|---|---|---|
| `<directory>` | Yes | Path to the content directory to verify |
| `--registry <url>` | Yes | The manifest URL for the registry you want to verify against |
| `--source <uri>` | No | GitHub source repository URI, for publisher co-attestation |
| `--json` | No | Emit machine-readable JSON output in addition to the human-readable report |

### Offline mode — verify against install-time snapshot

```bash
python3 moat_verify.py <directory> --lockfile <path>
```

Verifies against the lockfile written by a conforming install tool at the time the content was installed. Does not require Rekor connectivity. Proves "this content was valid when installed" — cannot detect revocations or changes that occurred after installation.

| Argument | Required | Description |
|---|---|---|
| `<directory>` | Yes | Path to the content directory to verify |
| `--lockfile <path>` | Yes | Path to the MOAT lockfile written at install time |
| `--json` | No | Emit machine-readable JSON output |

---

## Online mode walkthrough

Given a content directory and a registry manifest URL:

```bash
python3 moat_verify.py ~/my-skills/summarizer \
  --registry https://raw.githubusercontent.com/alice/my-registry/moat-registry/registry.json
```

moat-verify runs five steps:

1. **Computes the content hash** of the directory using the MOAT hashing algorithm
2. **Fetches and verifies the registry manifest** — fetches the `.sigstore` bundle alongside it, verifies the manifest signature against Rekor, and confirms the signer matches the manifest's declared `registry_signing_profile`
3. **Looks up the content hash** in the manifest's `content` array
4. **Verifies the per-item Rekor attestation** — fetches the Rekor entry at `rekor_log_index`, reconstructs the canonical payload, and confirms the entry covers the computed content hash
5. **Verifies publisher attestation** (only if `--source` is provided)

### Adding publisher verification

If the publisher has run the Publisher Action, you can optionally verify their independent attestation:

```bash
python3 moat_verify.py ~/my-skills/summarizer \
  --registry https://raw.githubusercontent.com/.../registry.json \
  --source https://github.com/alice/skills-repo
```

This fetches `moat-attestation.json` from the publisher's `moat-attestation` branch and verifies the Rekor entry it contains. If `--source` is omitted, publisher attestation is reported as `NOT REQUESTED` — this is not a failure.

### Reading the output

A successful run looks like:

```
Content hash: sha256:abc123...

[✓] Registry manifest verified
    Registry: https://raw.githubusercontent.com/.../registry.json
    Name:     alice-registry
    Operator: Alice
    Updated:  2026-04-11T04:48:55Z
    Signer:   https://github.com/alice/my-registry/.github/workflows/moat-registry.yml@refs/heads/main

[✓] Hash found in registry manifest
    Name:    summarizer
    Type:    skill

[✓] Per-item Rekor attestation verified
    Log Index: 12345678
    Signer:    https://github.com/alice/my-registry/.github/workflows/moat-registry.yml@refs/heads/main

Publisher attestation: NOT REQUESTED
(Pass --source <uri> to verify publisher CI attestation)

Trust result: SIGNED

What this script did NOT verify:
  - Whether the registry at <url> is one you should trust
  - Whether the registry signing identity is the legitimate operator of this registry
  - Whether the publisher OIDC identity is the legitimate owner of this source repository
  - Content safety, malicious behavior, or sandbox escape
```

The "NOT Verified" block is always printed. MOAT verifies provenance and integrity — it does not evaluate content safety or decide whether a registry is trustworthy. Those decisions remain yours.

---

## Offline mode walkthrough

If a conforming install tool wrote a lockfile when you installed the content:

```bash
python3 moat_verify.py ~/my-skills/summarizer --lockfile ~/.moat/moat.lock
```

moat-verify looks up the content hash in the lockfile and verifies the stored attestation bundle offline using `cosign verify-blob --offline`. No Rekor connectivity required.

Offline mode cannot detect:
- Revocations issued after installation
- Trust tier changes
- Whether the registry signing identity is still current
- Whether a newer version supersedes this one

Use online mode (`--registry`) to check current registry state.

---

## Trust results

| Result | What it means |
|---|---|
| `DUAL-ATTESTED` | Registry attestation verified + publisher co-attestation verified |
| `SIGNED` | Registry attestation verified; publisher attestation not requested or not available |
| `UNSIGNED` | Content found in manifest but no Rekor entry was present (`Unsigned` tier) |
| `FAILED` | One or more verification steps failed |

---

## Exit codes

| Code | Meaning | Common causes |
|---|---|---|
| `0` | All verifications passed | Successful SIGNED, DUAL-ATTESTED, or UNSIGNED result |
| `1` | Verification failed | Hash not in manifest or lockfile; Rekor entry doesn't match; bundle mismatch |
| `2` | Input error | Invalid arguments, missing lockfile, unsupported `--source` URI, unrecognized schema version |
| `3` | Infrastructure or corrupt data | Registry or Rekor unreachable (online); corrupt attestation bundle (offline) |

Exit code 3 in offline mode means the stored bundle is damaged — not that the content is bad. Recovery: re-run with `--registry` to verify against current registry state.

---

## JSON output

Add `--json` to get machine-readable output alongside the human-readable report. Useful for scripting or CI pipelines.

Online mode JSON structure:

```json
{
  "schema_version": 1,
  "mode": "online",
  "content_hash": "sha256:abc123...",
  "registry": "https://example.com/registry.json",
  "result": "SIGNED",
  "steps": {
    "hash_computed": true,
    "manifest_fetched": true,
    "manifest_bundle_verified": true,
    "hash_found_in_manifest": true,
    "item_rekor_verified": true,
    "publisher_rekor_verified": null
  },
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

---

## What MOAT verifies — and what it doesn't

Running `moat-verify` successfully tells you:

- The content directory matches the hash the registry attested
- The registry's attestation is logged in the Rekor transparency ledger
- The attestation was signed by the identity declared in the registry manifest
- (With `--source`) The publisher independently attested the same content hash from their CI

It does not tell you:

- Whether the registry operator is acting in good faith
- Whether the publisher OIDC identity is the legitimate owner of the repository
- Whether the content is safe to run
- Whether external dependencies (MCP servers, remote URLs referenced in skill files) are trustworthy

Choosing which registries to trust is your decision. MOAT gives you the tools to verify what those registries claim.
