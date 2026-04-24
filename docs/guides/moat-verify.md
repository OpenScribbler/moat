# Testing moat-verify

**Covers:** `reference/moat_verify.py` — both offline (`--lockfile`) and online (`--registry`) modes.

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

All three must be on PATH. `cosign` installers: https://docs.sigstore.dev/cosign/system_config/installation/

---

## Offline mode tests

Offline mode uses a lockfile written at install time. No network calls are required except for the
initial `cosign verify-blob --offline` call — that call itself is air-gapped but the test artifacts
were created with a real Sigstore signing flow.

### Set up test content

Create a content directory with known contents:

```bash
mkdir -p /tmp/moat-test-content
echo "hello from moat test" > /tmp/moat-test-content/hello.txt
```

Compute its content hash:

```bash
python3 reference/moat_hash.py /tmp/moat-test-content
# sha256:<hex>  — note this value, call it CONTENT_HASH
```

### Build a lockfile with a real bundle

The existing test bundle (`reference/test_artifacts/test_bundle.sigstore.json`) was created by
`test_offline_verify.py` using a real `cosign sign-blob` operation. Use it to build a synthetic
lockfile:

```python
import json
import moat_hash
from pathlib import Path

content_hash = moat_hash.content_hash("/tmp/moat-test-content")

bundle  = json.loads(Path("reference/test_artifacts/test_bundle.sigstore.json").read_text())
payload = Path("reference/test_artifacts/test_blob.txt").read_text()

lockfile = {
    "moat_lockfile_version": 1,
    "entries": [{
        "name":               "test-skill",
        "type":               "skill",
        "registry":           "https://example.com/moat-manifest.json",
        "content_hash":       content_hash,
        "trust_tier":         "SIGNED",
        "attested_at":        "2026-04-01T00:00:00Z",
        "pinned_at":          "2026-04-09T00:00:00Z",
        "attestation_bundle": bundle,
        "signed_payload":     payload,
    }],
    "revoked_hashes": [],
}
Path("/tmp/moat-test.lock").write_text(json.dumps(lockfile, indent=2))
print("lockfile written:", content_hash)
```

> **Note:** This test bundle signs `test_blob.txt` (an arbitrary JSON payload). In production, the
> `signed_payload` is the canonical per-item payload `{"_version":1,"content_hash":"sha256:<hex>"}`. The bundle
> used here pre-dates the format definition — see [Building a conforming lockfile](#building-a-conforming-lockfile).

### Run the tests

**Happy path — SIGNED:**
```bash
python3 reference/moat_verify.py /tmp/moat-test-content --lockfile /tmp/moat-test.lock
# Expected: exit 0, Trust result: SIGNED
```

**Happy path — JSON output:**
```bash
python3 reference/moat_verify.py /tmp/moat-test-content --lockfile /tmp/moat-test.lock --json
# Expected: JSON block at end of output, "result": "SIGNED"
```

**Hash mismatch (content modified):**
```bash
mkdir -p /tmp/moat-modified && echo "tampered" > /tmp/moat-modified/hello.txt
python3 reference/moat_verify.py /tmp/moat-modified --lockfile /tmp/moat-test.lock
# Expected: exit 1, "Hash not found in lockfile"
```

**Corrupt bundle (exit 3):**
```python
# Build lockfile with corrupt bundle
import json, moat_hash
from pathlib import Path

content_hash = moat_hash.content_hash("/tmp/moat-test-content")
corrupt = json.loads(Path("reference/test_artifacts/test_bundle_corrupt.sigstore.json").read_text())
payload = Path("reference/test_artifacts/test_blob.txt").read_text()

lf = {
    "moat_lockfile_version": 1,
    "entries": [{
        "name": "test-skill", "type": "skill",
        "registry": "https://example.com/moat-manifest.json",
        "content_hash": content_hash, "trust_tier": "SIGNED",
        "attested_at": "2026-04-01T00:00:00Z", "pinned_at": "2026-04-09T00:00:00Z",
        "attestation_bundle": corrupt, "signed_payload": payload,
    }],
    "revoked_hashes": [],
}
Path("/tmp/moat-corrupt.lock").write_text(json.dumps(lf, indent=2))
```

```bash
python3 reference/moat_verify.py /tmp/moat-test-content --lockfile /tmp/moat-corrupt.lock
# Expected: exit 3, "Attestation bundle is corrupt"
```

**UNSIGNED content:**
```python
import json, moat_hash
from pathlib import Path

lf = {
    "moat_lockfile_version": 1,
    "entries": [{
        "name": "unsigned-skill", "type": "skill",
        "registry": "https://example.com/moat-manifest.json",
        "content_hash": moat_hash.content_hash("/tmp/moat-test-content"),
        "trust_tier": "UNSIGNED",
        "attested_at": "2026-04-01T00:00:00Z", "pinned_at": "2026-04-09T00:00:00Z",
        "attestation_bundle": None, "signed_payload": None,
    }],
    "revoked_hashes": [],
}
Path("/tmp/moat-unsigned.lock").write_text(json.dumps(lf, indent=2))
```

```bash
python3 reference/moat_verify.py /tmp/moat-test-content --lockfile /tmp/moat-unsigned.lock
# Expected: exit 0, Trust result: UNSIGNED
```

### Input error paths (all exit 2)

```bash
# Both modes combined
python3 reference/moat_verify.py /tmp/moat-test-content --registry http://x --lockfile /tmp/moat-test.lock
# Expected: mutual exclusion error

# --source not valid in offline mode
python3 reference/moat_verify.py /tmp/moat-test-content --lockfile /tmp/moat-test.lock --source https://github.com/x/y
# Expected: "--source is not valid in offline mode"

# Non-GitHub --source
python3 reference/moat_verify.py /tmp/moat-test-content --registry http://x --source https://gitlab.com/x/y
# Expected: "must be a GitHub repository"

# Directory does not exist
python3 reference/moat_verify.py /nonexistent --lockfile /tmp/moat-test.lock
# Expected: "Directory does not exist"

# Lockfile not found
python3 reference/moat_verify.py /tmp/moat-test-content --lockfile /nonexistent.lock
# Expected: "Lockfile not found"
```

---

## Online mode tests

Online mode requires a live registry serving a signed manifest and `.sigstore` bundle. It also
requires Rekor connectivity.

### What you need

1. A MOAT-conforming registry manifest served at a stable URL
2. The manifest signed with `cosign sign-blob`, bundle served at `<manifest-url>.sigstore`
3. Each Signed/Dual-Attested item in the manifest must have:
   - A `rekor_log_index` pointing to the item's per-item Rekor entry
   - That entry created by signing `{"_version":1,"content_hash":"sha256:<hex>"}` (canonical payload format)

### Quick integration test with a local registry

```bash
# 1. Create a content directory and compute its hash
mkdir -p /tmp/registry-test-skill
echo "# My Test Skill" > /tmp/registry-test-skill/SKILL.md

python3 -c "
import moat_hash
h = moat_hash.content_hash('/tmp/registry-test-skill')
print('content_hash:', h)
"
# Note the content_hash → CONTENT_HASH
```

```bash
# 2. Sign the per-item canonical payload
CONTENT_HASH="sha256:<your-hash-here>"
echo -n "{\"_version\":1,\"content_hash\":\"$CONTENT_HASH\"}" > /tmp/item-payload.json
cosign sign-blob --bundle /tmp/item-bundle.sigstore.json /tmp/item-payload.json
# Note the logIndex from cosign output → ITEM_LOG_INDEX
```

```bash
# 3. Build a minimal registry manifest
cat > /tmp/moat-manifest.json << EOF
{
  "schema_version": 1,
  "manifest_uri": "file:///tmp/moat-manifest.json",
  "name": "Test Registry",
  "operator": "Test Operator",
  "updated_at": "2026-04-09T00:00:00Z",
  "registry_signing_profile": {
    "issuer": "<your-oidc-issuer>",
    "subject": "<your-oidc-subject>"
  },
  "content": [
    {
      "name": "test-skill",
      "display_name": "Test Skill",
      "type": "skill",
      "content_hash": "$CONTENT_HASH",
      "source_uri": "https://github.com/example/test-skills",
      "attested_at": "2026-04-09T00:00:00Z",
      "private_repo": false,
      "rekor_log_index": $ITEM_LOG_INDEX
    }
  ],
  "revocations": []
}
EOF
```

```bash
# 4. Sign the manifest
cosign sign-blob --bundle /tmp/moat-manifest.json.sigstore /tmp/moat-manifest.json
```

```bash
# 5. Serve the files (simple HTTP server)
cd /tmp && python3 -m http.server 8080 &

# 6. Run moat-verify
python3 reference/moat_verify.py /tmp/registry-test-skill \
  --registry http://localhost:8080/moat-manifest.json
```

> **Note on `manifest_uri`:** The test above sets `manifest_uri` to `file:///tmp/...` which won't
> match the HTTP URL. moat-verify will warn but not fail — CDN/proxy mismatches are allowed. For a
> clean test, set `manifest_uri` to `http://localhost:8080/moat-manifest.json`.

### Publisher co-attestation (`--source`)

To test `--source`, the publisher must have run the Publisher Action and the `moat-attestation.json`
must exist on the `moat-attestation` branch of the source repository.

```bash
python3 reference/moat_verify.py /tmp/registry-test-skill \
  --registry http://localhost:8080/moat-manifest.json \
  --source https://github.com/<owner>/<repo>
```

Expected output when attestation found:
```
[✓] Publisher Rekor attestation verified
    Log ID:        <rekor-log-id>
    Log Index:     <index>
    OIDC Identity: https://github.com/<owner>/<repo>/.github/workflows/moat-publisher.yml@refs/heads/main
```

Expected when `--source` is provided but the publisher has not run the Publisher Action:
- Exit 1: `Publisher moat-attestation.json not found or unreachable`

---

## Building a conforming lockfile

A lockfile produced by a conforming client captures everything needed for offline verification.
Here is the per-item attestation flow a client must implement:

```python
import json, subprocess, tempfile
from pathlib import Path
import moat_hash

def build_lockfile_entry(content_dir: str, manifest_entry: dict, registry_url: str) -> dict:
    """
    Build a lockfile entry for a manifest item at install time.
    Called after moat-verify (online) passes for this item.
    """
    content_hash = moat_hash.content_hash(content_dir)
    trust_tier   = manifest_entry.get("trust_tier", "UNSIGNED")
    log_index    = manifest_entry.get("rekor_log_index")

    if trust_tier == "UNSIGNED" or log_index is None:
        return {
            "name":               manifest_entry["name"],
            "type":               manifest_entry["type"],
            "registry":           registry_url,
            "content_hash":       content_hash,
            "trust_tier":         "UNSIGNED",
            "attested_at":        manifest_entry["attested_at"],
            "pinned_at":          "<client-clock-now>",
            "attestation_bundle": None,
            "signed_payload":     None,
        }

    # Canonical per-item payload (must match what the registry signed)
    payload_bytes = json.dumps(
        {"content_hash": content_hash},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    # Fetch the Rekor entry to get the bundle
    import urllib.request
    url = f"https://rekor.sigstore.dev/api/v1/log/entries?logIndex={log_index}"
    with urllib.request.urlopen(url) as resp:
        rekor_data = json.loads(resp.read())
    entry_uuid = next(iter(rekor_data))
    rekor_entry = rekor_data[entry_uuid]

    # Confirm data hash before storing (normative MUST in moat-spec.md §Lockfile)
    import base64
    body = json.loads(base64.b64decode(rekor_entry["body"]))
    rekor_data_hash = body["spec"]["data"]["hash"]["value"]
    payload_hash = hashlib.sha256(payload_bytes).hexdigest()
    if rekor_data_hash != payload_hash:
        raise ValueError(
            f"Rekor entry data hash mismatch — do not write lockfile entry.\n"
            f"  Expected: {payload_hash}\n"
            f"  Rekor:    {rekor_data_hash}"
        )

    # Build a Sigstore bundle from the Rekor entry
    # (see _build_bundle() in reference/moat_verify.py for the reconstruction logic)
    bundle = build_bundle_from_rekor_entry(rekor_entry)  # your implementation

    return {
        "name":               manifest_entry["name"],
        "type":               manifest_entry["type"],
        "registry":           registry_url,
        "content_hash":       content_hash,
        "trust_tier":         trust_tier,
        "attested_at":        manifest_entry["attested_at"],
        "pinned_at":          "<client-clock-now>",
        "attestation_bundle": bundle,
        "signed_payload":     payload_bytes.decode("utf-8"),
    }
```

**Key invariant:** `sha256(signed_payload.encode("utf-8"))` must equal the `data.hash.value` in the
Rekor entry at `rekor_log_index`. Conforming clients MUST verify this before writing the lockfile entry —
do not store a `signed_payload` you haven't confirmed against the Rekor record. If it does not match,
`cosign verify-blob --offline` will fail on re-verification.

---

## Per-item payload format summary

| Field            | Value                                                                  |
|------------------|------------------------------------------------------------------------|
| Encoding         | UTF-8, no BOM                                                          |
| JSON form        | `{"_version":1,"content_hash":"sha256:<hex>"}`                         |
| Trailing newline | None                                                                   |
| Whitespace       | None (compact serialization)                                           |
| Key order        | `sort_keys=True` (`_version` sorts before `content_hash`)              |

Python canonical form:
```python
payload = json.dumps(
    {"_version": 1, "content_hash": content_hash},
    separators=(",", ":"),
    sort_keys=True,
).encode("utf-8")
# → b'{"_version":1,"content_hash":"sha256:<hex>"}'
```

This is the exact byte sequence the registry signs with `cosign sign-blob` and the exact byte
sequence `moat-verify` reconstructs to verify the per-item Rekor entry.

### Test vector

Use this to validate your canonical payload implementation:

| Field              | Value                                                                                        |
|--------------------|----------------------------------------------------------------------------------------------|
| Input hash         | `sha256:3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b`                  |
| Payload bytes      | `{"_version":1,"content_hash":"sha256:3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b"}` |
| SHA-256 of payload | `b7d70330da474c9d32efe29dd4e23c4a0901a7ca222e12bdbc84d17e4e5f69a4`                          |

Quick verification:
```python
import json, hashlib
h = "sha256:3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b"
payload = json.dumps({"_version": 1, "content_hash": h}, separators=(",", ":"), sort_keys=True).encode("utf-8")
assert hashlib.sha256(payload).hexdigest() == "b7d70330da474c9d32efe29dd4e23c4a0901a7ca222e12bdbc84d17e4e5f69a4"
print("Test vector OK")
```

---

## Exit code reference

| Code | Meaning                          | Example triggers                                       |
|------|----------------------------------|--------------------------------------------------------|
| 0    | All verifications passed         | Successful SIGNED, DUAL-ATTESTED, or UNSIGNED verify   |
| 1    | Verification failed              | Hash not in lockfile, bundle mismatch, Rekor entry wrong hash |
| 2    | Bad input                        | Combined flags, missing lockfile, unknown schema version |
| 3    | Infrastructure / corrupt data    | Rekor unreachable, corrupt ASN.1 in `attestation_bundle` |
