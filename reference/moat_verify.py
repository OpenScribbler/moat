#!/usr/bin/env python3
"""
moat-verify — MOAT Content Verification Reference Implementation

Verifies MOAT-attested content in online (--registry) or offline (--lockfile) mode.

Usage:
    Online:  moat-verify <directory> --registry <url> [--source <uri>] [--json]
    Offline: moat-verify <directory> --lockfile <path> [--json]

Language: Python 3.9+
Dependencies: moat_hash.py (same directory), cosign CLI on PATH, stdlib only

See: specs/moat-verify.md for the normative specification.

Per-item registry attestation payload (normative, moat-spec.md §Signature Envelope):
  The registry signs a canonical JSON payload for each content item:
    {"content_hash":"sha256:<hex>"}
  UTF-8, no trailing newline, no extra whitespace. This is reproducible from the
  manifest entry alone — moat-verify reconstructs it from the computed content_hash.
  The Rekor entry's hashedrekord data hash must equal sha256(canonical_payload).
"""

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

# ── Import moat_hash from same directory ─────────────────────────────────────
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import moat_hash  # noqa: E402

REKOR_BASE_URL = "https://rekor.sigstore.dev"
KNOWN_SCHEMA_VERSIONS: frozenset[int] = frozenset({1})
KNOWN_LOCKFILE_VERSIONS: frozenset[int] = frozenset({1})
GITHUB_URI_PREFIX = "https://github.com/"

# ── Exit codes ────────────────────────────────────────────────────────────────
EXIT_OK    = 0  # all verifications passed
EXIT_FAIL  = 1  # verification failed
EXIT_INPUT = 2  # bad input / invalid arguments
EXIT_INFRA = 3  # infrastructure failure / corrupt stored artifact


# ── Internal exception ────────────────────────────────────────────────────────

class _Exit(Exception):
    """Raised to unwind and exit with a specific code and optional message."""
    def __init__(self, code: int, message: str = ""):
        self.code = code
        self.message = message
        super().__init__(message)


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _fetch_url(url: str, label: str) -> bytes:
    """GET url → raw bytes. Raises _Exit(3) on network or HTTP failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "moat-verify/0.4.0"})
        with urllib.request.urlopen(req) as resp:
            if resp.status != 200:
                raise _Exit(EXIT_INFRA, f"{label} returned HTTP {resp.status}: {url}")
            return resp.read()
    except urllib.error.HTTPError as e:
        raise _Exit(EXIT_INFRA, f"{label} returned HTTP {e.code}: {url}") from e
    except urllib.error.URLError as e:
        raise _Exit(EXIT_INFRA, f"{label} unreachable: {url}\n  {e.reason}") from e
    except _Exit:
        raise
    except Exception as e:
        raise _Exit(EXIT_INFRA, f"{label} failed: {url}\n  {e}") from e


def _fetch_json(url: str, label: str) -> dict:
    raw = _fetch_url(url, label)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise _Exit(EXIT_INFRA, f"{label} returned invalid JSON: {url}\n  {e}") from e


# ── cosign helpers ────────────────────────────────────────────────────────────

def _run_cosign(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["cosign"] + args, capture_output=True, text=True)


def _extract_oidc(stdout: str, stderr: str) -> tuple[str, str]:
    """
    Parse (subject, issuer) from cosign verify-blob output.
    Returns ("unknown", "unknown") if not parseable (cosign does not always print these).
    """
    subject = "unknown"
    issuer  = "unknown"
    for line in (stdout + "\n" + stderr).splitlines():
        l = line.strip().lower()
        if l.startswith("certificate subject:"):
            subject = line.split(":", 1)[1].strip()
        elif l.startswith("certificate issuer uri:"):
            issuer = line.split(":", 1)[1].strip()
    return subject, issuer


def _oidc_from_bundle(bundle: dict | str) -> tuple[str, str]:
    """
    Extract (OIDC subject, OIDC issuer) by parsing the signing certificate
    embedded in a Sigstore bundle (modern v0.1+ or legacy format).
    Falls back to ("unknown", "unknown") on any parse failure.
    """
    b: dict
    if isinstance(bundle, str):
        try:
            b = json.loads(bundle)
        except Exception:
            return "unknown", "unknown"
    else:
        b = bundle

    cert_pem: str | None = None

    # Modern bundle: verificationMaterial.x509CertificateChain or .certificate
    vm = b.get("verificationMaterial", {})
    chain = vm.get("x509CertificateChain", {}).get("certificates", [])
    if chain:
        raw = chain[0].get("rawBytes", "")
        if raw:
            cert_pem = _rawbytes_to_pem(raw)
    if not cert_pem:
        raw = vm.get("certificate", {}).get("rawBytes", "")
        if raw:
            cert_pem = _rawbytes_to_pem(raw)

    # Legacy bundle: .cert is base64(PEM)
    if not cert_pem:
        cert_b64 = b.get("cert", "")
        if cert_b64:
            try:
                cert_pem = base64.b64decode(cert_b64).decode("utf-8")
            except Exception:
                pass

    if not cert_pem:
        return "unknown", "unknown"
    return _oidc_from_cert_pem(cert_pem)


def _rawbytes_to_pem(raw_bytes_b64: str) -> str:
    """Convert base64(DER) to PEM format."""
    try:
        der = base64.b64decode(raw_bytes_b64)
        b64 = base64.b64encode(der).decode()
        lines = [b64[i:i + 64] for i in range(0, len(b64), 64)]
        return "-----BEGIN CERTIFICATE-----\n" + "\n".join(lines) + "\n-----END CERTIFICATE-----\n"
    except Exception:
        return ""


def _oidc_from_cert_pem(cert_pem: str) -> tuple[str, str]:
    """
    Extract (OIDC subject, OIDC issuer) from a PEM certificate using the openssl CLI.
    OIDC subject: SubjectAltName URI (workload identity) or email (interactive login).
    OIDC issuer:  Fulcio OID 1.3.6.1.4.1.57264.1.1 or .1.8.
    Returns ("unknown", "unknown") on any failure.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".pem", mode="w", delete=False) as f:
            f.write(cert_pem)
            fname = f.name
        result = subprocess.run(
            ["openssl", "x509", "-text", "-noout", "-in", fname],
            capture_output=True, text=True,
        )
        Path(fname).unlink(missing_ok=True)
        if result.returncode != 0:
            return "unknown", "unknown"
        return _parse_openssl_text(result.stdout)
    except Exception:
        return "unknown", "unknown"


def _parse_openssl_text(text: str) -> tuple[str, str]:
    """Parse (subject, issuer) from openssl x509 -text output."""
    subject = "unknown"
    issuer  = "unknown"
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        # SubjectAltName URI (workload identity) or email (interactive)
        if "Subject Alternative Name" in stripped and i + 1 < len(lines):
            san = lines[i + 1].strip()
            for part in san.split(","):
                part = part.strip()
                if part.startswith("URI:"):
                    subject = part[4:].strip()
                    break
                if part.startswith("email:"):
                    subject = part[6:].strip()
                    break
        # Fulcio OIDC issuer OIDs (v1 = .1.1, v2 = .1.8 with DER prefix bytes)
        if ("1.3.6.1.4.1.57264.1.1:" in stripped or "1.3.6.1.4.1.57264.1.8:" in stripped) \
                and i + 1 < len(lines):
            val = lines[i + 1].strip().lstrip(".")
            if val.startswith("http"):
                issuer = val
    return subject, issuer


# ── Rekor helpers ─────────────────────────────────────────────────────────────

def _fetch_rekor_entry(log_index: int) -> dict:
    """
    Fetch a Rekor log entry by index.
    Returns the entry dict (UUID key stripped).
    Raises _Exit(3) with the spec-required error message on failure.
    """
    url = f"{REKOR_BASE_URL}/api/v1/log/entries?logIndex={log_index}"
    try:
        data = _fetch_json(url, "Rekor transparency log")
    except _Exit:
        raise _Exit(
            EXIT_INFRA,
            f"[✗] Cannot verify per-item Rekor attestation — transparency log unreachable\n"
            f"    Rekor URL: {REKOR_BASE_URL}\n"
            f"    This is a hard failure. moat-verify will never pass without Rekor verification.",
        )
    if not data:
        raise _Exit(EXIT_INFRA, f"Rekor returned empty response for log index {log_index}")
    entry_uuid = next(iter(data))
    return data[entry_uuid]


def _decode_rekor_body(entry: dict) -> dict:
    """Base64-decode and JSON-parse the Rekor entry body."""
    try:
        return json.loads(base64.b64decode(entry["body"]))
    except Exception as e:
        raise _Exit(EXIT_INFRA, f"Rekor entry body is malformed: {e}") from e


def _build_bundle(entry: dict, body: dict) -> dict:
    """
    Reconstruct a Sigstore bundle (v0.1) from a Rekor API log entry.
    Used for online Step 4 cosign verify-blob.

    Rekor hashedrekord body layout:
      body.spec.data.hash.value           — hex SHA-256 of signed content
      body.spec.signature.content         — base64 DER signature
      body.spec.signature.publicKey.content — base64(PEM cert)
    """
    kind = body.get("kind", "")
    if kind != "hashedrekord":
        raise _Exit(EXIT_INFRA, f"Unexpected Rekor entry kind '{kind}'; expected 'hashedrekord'")

    spec      = body.get("spec", {})
    sig_block = spec.get("signature", {})
    sig_b64   = sig_block.get("content", "")

    # cert: base64(PEM) → decode → strip header/footer → get base64(DER) = rawBytes
    cert_b64_pem = sig_block.get("publicKey", {}).get("content", "")
    try:
        pem = base64.b64decode(cert_b64_pem).decode("utf-8")
        raw_bytes_b64 = (
            pem
            .replace("-----BEGIN CERTIFICATE-----", "")
            .replace("-----END CERTIFICATE-----", "")
            .replace("\n", "")
            .strip()
        )
    except Exception as e:
        raise _Exit(EXIT_INFRA, f"Failed to parse certificate from Rekor entry: {e}") from e

    data_hash_hex = spec.get("data", {}).get("hash", {}).get("value", "")
    data_hash_b64 = base64.b64encode(bytes.fromhex(data_hash_hex)).decode() if data_hash_hex else ""

    tlog: dict = {
        "logIndex":        str(entry.get("logIndex", "")),
        "logId":           {"keyId": entry.get("logID", "")},
        "kindVersion":     {"kind": kind, "version": body.get("apiVersion", "0.0.1")},
        "integratedTime":  str(entry.get("integratedTime", "")),
        "canonicalizedBody": entry.get("body", ""),
    }
    verification = entry.get("verification", {})
    if set_b64 := verification.get("signedEntryTimestamp", ""):
        tlog["inclusionPromise"] = {"signedEntryTimestamp": set_b64}
    if proof := verification.get("inclusionProof", {}):
        tlog["inclusionProof"] = proof

    return {
        "mediaType": "application/vnd.dev.sigstore.bundle+json;version=0.1",
        "verificationMaterial": {
            "x509CertificateChain": {"certificates": [{"rawBytes": raw_bytes_b64}]},
            "tlogEntries": [tlog],
        },
        "messageSignature": {
            "messageDigest": {"algorithm": "SHA2_256", "digest": data_hash_b64},
            "signature": sig_b64,
        },
    }


# ── Step 1: content hash (shared) ─────────────────────────────────────────────

def _step1_compute_hash(directory: str) -> str:
    """Compute MOAT content hash. Returns 'sha256:<hex>'."""
    path = Path(directory)
    if not path.exists():
        raise _Exit(EXIT_INPUT, f"Directory does not exist: {directory}")
    if not path.is_dir():
        raise _Exit(EXIT_INPUT, f"Not a directory: {directory}")
    try:
        h = moat_hash.content_hash(path)
    except ValueError as e:
        msg = str(e)
        if "Symlink" in msg:
            raise _Exit(EXIT_INPUT, f"Directory contains symlinks: {directory}\n  {msg}")
        raise _Exit(EXIT_INPUT, f"Hash computation failed: {msg}")
    print(f"Content hash: {h}")
    return h


# ── Online verification steps ─────────────────────────────────────────────────

def _online_step2(registry_url: str) -> tuple[bytes, dict]:
    """
    Fetch registry manifest, fetch bundle, verify with cosign.
    Returns (manifest_bytes, manifest_dict).
    """
    manifest_bytes = _fetch_url(registry_url, "Registry manifest")
    try:
        manifest = json.loads(manifest_bytes)
    except json.JSONDecodeError as e:
        raise _Exit(EXIT_INFRA, f"Registry manifest is not valid JSON: {registry_url}\n  {e}")

    # Required top-level fields
    required = {"schema_version", "manifest_uri", "registry_signing_profile", "content", "revocations"}
    if missing := required - set(manifest.keys()):
        raise _Exit(EXIT_INFRA, f"Registry manifest missing required fields: {', '.join(sorted(missing))}")

    schema_version = manifest.get("schema_version")
    if schema_version not in KNOWN_SCHEMA_VERSIONS:
        raise _Exit(EXIT_INPUT, f"Unknown manifest schema_version: {schema_version!r}")

    declared_uri = manifest.get("manifest_uri", "")
    if declared_uri and declared_uri != registry_url:
        print(f"Warning: manifest_uri ({declared_uri}) does not match --registry URL ({registry_url})")
        print(f"  (CDN/proxy configurations may legitimately serve from a different URL)")

    bundle_url   = f"{declared_uri or registry_url}.sigstore"
    bundle_bytes = _fetch_url(bundle_url, "Registry manifest bundle")

    try:
        json.loads(bundle_bytes)  # validate bundle is JSON
    except json.JSONDecodeError as e:
        raise _Exit(EXIT_INFRA, f"Manifest bundle is not valid JSON: {bundle_url}\n  {e}")

    signing_profile = manifest.get("registry_signing_profile", {})
    issuer  = signing_profile.get("issuer", "")
    subject = signing_profile.get("subject", "")

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_tmp = Path(tmpdir) / "manifest.json"
        bundle_tmp   = Path(tmpdir) / "manifest.sigstore"
        manifest_tmp.write_bytes(manifest_bytes)
        bundle_tmp.write_bytes(bundle_bytes)

        cosign_args = ["verify-blob", "--bundle", str(bundle_tmp)]
        if issuer:
            cosign_args += ["--certificate-oidc-issuer", issuer]
        if subject:
            cosign_args += ["--certificate-identity", subject]
        cosign_args.append(str(manifest_tmp))

        result = _run_cosign(cosign_args)

    if result.returncode != 0:
        combined = (result.stdout + result.stderr).lower()
        if "rekor" in combined and any(w in combined for w in ("unreachable", "connection", "timeout", "dial")):
            raise _Exit(
                EXIT_INFRA,
                f"[✗] Cannot verify manifest bundle — transparency log unreachable\n"
                f"    Rekor URL: {REKOR_BASE_URL}\n"
                f"    This is a hard failure. moat-verify will never pass without Rekor verification.",
            )
        raise _Exit(EXIT_FAIL, f"Manifest bundle verification failed:\n  {result.stderr.strip()}")

    signer_subject, signer_issuer = _extract_oidc(result.stdout, result.stderr)

    print(f"[✓] Registry manifest verified")
    print(f"    Registry: {manifest.get('manifest_uri', registry_url)}")
    print(f"    Name:     {manifest.get('name', '')}")
    print(f"    Operator: {manifest.get('operator', '')}")
    print(f"    Updated:  {manifest.get('updated_at', '')}")
    print(f"    Signer:   {signer_subject} ({signer_issuer})")

    return manifest_bytes, manifest


def _online_step3(manifest: dict, content_hash: str) -> dict:
    """Look up content_hash in manifest.content[]. Returns matching item."""
    for item in manifest.get("content", []):
        if item.get("content_hash") == content_hash:
            version = item.get("version") or "unset"
            print(f"[✓] Hash found in registry manifest")
            print(f"    Name:    {item.get('name', '')}")
            print(f"    Version: {version}")
            print(f"    Type:    {item.get('type', '')}")
            return item

    registry_url = manifest.get("manifest_uri", "")
    print(f"[✗] Hash not found in registry manifest")
    print(f"    Computed: {content_hash}")
    print(f"    Registry: {registry_url}")
    raise _Exit(EXIT_FAIL)


def _canonical_payload(content_hash: str) -> bytes:
    """
    The normative per-item attestation payload (moat-spec.md §Signature Envelope).
    Format: {"content_hash":"sha256:<hex>"}  — UTF-8, no whitespace, no trailing newline.
    """
    return json.dumps({"content_hash": content_hash}, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _verify_rekor_entry(log_index: int, content_hash: str) -> tuple[str, str]:
    """
    Shared Rekor verification logic used by online Step 4 and Step 5.

    1. Fetch the Rekor entry at log_index.
    2. Reconstruct canonical payload, compute sha256, compare to Rekor data hash.
    3. Reconstruct bundle, run cosign verify-blob with the canonical payload file.
    4. Return (subject, issuer) from the verified certificate.
    """
    entry = _fetch_rekor_entry(log_index)
    body  = _decode_rekor_body(entry)

    kind = body.get("kind", "")
    if kind != "hashedrekord":
        raise _Exit(EXIT_INFRA, f"Unexpected Rekor entry kind: {kind!r}")

    spec          = body.get("spec", {})
    data_hash_hex = spec.get("data", {}).get("hash", {}).get("value", "")
    if not data_hash_hex:
        raise _Exit(EXIT_INFRA, "Rekor entry missing data.hash.value")

    # Reconstruct the canonical payload and verify its hash matches the Rekor entry
    payload_bytes = _canonical_payload(content_hash)
    expected = hashlib.sha256(payload_bytes).hexdigest()
    if data_hash_hex != expected:
        raise _Exit(
            EXIT_FAIL,
            f"[✗] Rekor entry data hash does not match computed content hash\n"
            f"    Log index:     {log_index}\n"
            f"    Computed hash: {content_hash}\n"
            f"    Rekor payload: sha256:{data_hash_hex}",
        )

    bundle = _build_bundle(entry, body)

    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_tmp  = Path(tmpdir) / "item.sigstore.json"
        payload_tmp = Path(tmpdir) / "payload"
        bundle_tmp.write_text(json.dumps(bundle))
        payload_tmp.write_bytes(payload_bytes)

        result = _run_cosign([
            "verify-blob",
            "--bundle", str(bundle_tmp),
            "--certificate-identity-regexp", ".*",
            "--certificate-oidc-issuer-regexp", ".*",
            str(payload_tmp),
        ])

    if result.returncode != 0:
        combined = (result.stdout + result.stderr).lower()
        if "rekor" in combined and any(w in combined for w in ("unreachable", "connection", "timeout")):
            raise _Exit(
                EXIT_INFRA,
                f"[✗] Cannot verify per-item Rekor attestation — transparency log unreachable\n"
                f"    Rekor URL: {REKOR_BASE_URL}\n"
                f"    This is a hard failure. moat-verify will never pass without Rekor verification.",
            )
        raise _Exit(EXIT_FAIL, f"Rekor attestation verification failed:\n  {result.stderr.strip()}")

    return _extract_oidc(result.stdout, result.stderr)


def _online_step4(item: dict, content_hash: str) -> tuple[str, str, int | None]:
    """
    Verify per-item Rekor attestation.
    Returns (subject, issuer, log_index). subject="UNSIGNED" if no rekor_log_index.
    """
    log_index: int | None = item.get("rekor_log_index")
    if log_index is None:
        return "UNSIGNED", "", None

    subject, issuer = _verify_rekor_entry(log_index, content_hash)

    print(f"[✓] Per-item Rekor attestation verified")
    print(f"    Log Index: {log_index}")
    print(f"    Signer:    {subject} ({issuer})")

    return subject, issuer, log_index


def _online_step5(source_uri: str | None, content_hash: str) -> tuple[str | None, str | None, int | None]:
    """
    Publisher attestation.
    Returns (subject, issuer, log_index) or (None, None, None) if not requested.
    """
    if source_uri is None:
        print("Publisher attestation: NOT REQUESTED")
        print("(Pass --source <uri> to verify publisher CI attestation)")
        return None, None, None

    # Derive moat-attestation.json URL.
    # Note: moat-verify.md spec says /raw/main/ but publisher-action pushes to
    # the `moat-attestation` branch. Using the correct branch here.
    owner_repo = source_uri.replace("https://github.com/", "").rstrip("/")
    attestation_url = f"https://raw.githubusercontent.com/{owner_repo}/moat-attestation/moat-attestation.json"

    try:
        attestation_bytes = _fetch_url(attestation_url, "Publisher moat-attestation.json")
    except _Exit as e:
        if e.code == EXIT_INFRA:
            print(f"[✗] Publisher moat-attestation.json not found or unreachable")
            print(f"    Source URI: {source_uri}")
            raise _Exit(EXIT_FAIL, "") from e
        raise

    try:
        attestation = json.loads(attestation_bytes)
    except json.JSONDecodeError as e:
        raise _Exit(EXIT_FAIL, f"Publisher moat-attestation.json is not valid JSON: {e}") from e

    matching = next(
        (item for item in attestation.get("items", []) if item.get("content_hash") == content_hash),
        None,
    )
    if matching is None:
        print(f"[✗] Publisher attestation does not include this content hash")
        print(f"    Computed: {content_hash}")
        raise _Exit(EXIT_FAIL)

    log_index = matching.get("rekor_log_index")
    log_id    = matching.get("rekor_log_id", "")
    if log_index is None:
        raise _Exit(EXIT_FAIL, "Publisher attestation entry missing rekor_log_index")

    # Same procedure as Step 4, plus verify OIDC issuer is GitHub Actions
    subject, issuer = _verify_rekor_entry(log_index, content_hash)

    expected_issuer = "https://token.actions.githubusercontent.com"
    if issuer != expected_issuer:
        print(f"[✗] Publisher attestation: unexpected OIDC issuer")
        print(f"    Expected: {expected_issuer}")
        print(f"    Found:    {issuer}")
        raise _Exit(EXIT_FAIL)

    print(f"[✓] Publisher Rekor attestation verified")
    print(f"    Log ID:        {log_id}")
    print(f"    Log Index:     {log_index}")
    print(f"    OIDC Identity: {subject}")

    return subject, issuer, log_index


# ── Offline verification steps ────────────────────────────────────────────────

def _offline_step2(lockfile_path: str) -> dict:
    """Parse and validate lockfile. Returns lockfile dict."""
    path = Path(lockfile_path)
    if not path.exists():
        raise _Exit(EXIT_INPUT, f"Lockfile not found: {lockfile_path}")
    if not path.is_file():
        raise _Exit(EXIT_INPUT, f"Not a file: {lockfile_path}")

    try:
        lockfile = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise _Exit(EXIT_INPUT, f"Lockfile is not valid JSON: {lockfile_path}\n  {e}")
    except OSError as e:
        raise _Exit(EXIT_INPUT, f"Cannot read lockfile: {lockfile_path}\n  {e}")

    version = lockfile.get("moat_lockfile_version")
    if version is None:
        raise _Exit(EXIT_INPUT, "Lockfile missing required field: moat_lockfile_version")
    if version not in KNOWN_LOCKFILE_VERSIONS:
        raise _Exit(EXIT_INPUT, f"Unknown moat_lockfile_version: {version!r}")

    if "entries" not in lockfile:
        raise _Exit(EXIT_INPUT, "Lockfile missing required field: entries")
    if not isinstance(lockfile["entries"], list):
        raise _Exit(EXIT_INPUT, "Lockfile field 'entries' must be an array")

    n = len(lockfile["entries"])
    print(f"Lockfile: {lockfile_path} (version: {version}, {n} entries)")
    return lockfile


def _offline_step3(lockfile: dict, lockfile_path: str, content_hash: str) -> list[dict]:
    """
    Look up content_hash in lockfile entries.
    Returns list of matching entries (multiple = same content, multiple registries).
    """
    entries = lockfile.get("entries", [])
    matching = [e for e in entries if e.get("content_hash") == content_hash]

    if not matching:
        print(f"[✗] Hash not found in lockfile")
        print(f"    Computed:  {content_hash}")
        print(f"    Lockfile:  {lockfile_path}")
        print()
        print(f"    This means either: the content was modified after installation, or")
        print(f"    this lockfile does not correspond to this directory.")
        print(f"    moat-verify cannot distinguish between these cases.")
        raise _Exit(EXIT_FAIL)

    # Duplicate detection: same hash AND same name → malformed lockfile
    if len(matching) > 1:
        seen: set[tuple] = set()
        for e in matching:
            key = (e.get("name"), e.get("content_hash"))
            if key in seen:
                raise _Exit(EXIT_INPUT, "Malformed lockfile: duplicate entries with identical name and content_hash")
            seen.add(key)

    entry = matching[0]
    print(f"[✓] Hash found in lockfile")
    print(f"    Name:       {entry.get('name', '')}")
    print(f"    Type:       {entry.get('type', '')}")
    print(f"    Registry:   {entry.get('registry', '')}")
    print(f"    Attested:   {entry.get('attested_at', '')}")
    print(f"    Trust tier: {entry.get('trust_tier', '')}")

    if len(matching) > 1:
        print(f"    Note: {len(matching)} entries share this hash (same content, multiple registries)")

    return matching


def _offline_step4(entry: dict) -> tuple[str, str]:
    """
    Verify attestation bundle offline via cosign verify-blob --offline.
    Returns (subject, issuer).
    """
    trust_tier = entry.get("trust_tier", "")

    if trust_tier == "UNSIGNED":
        return "UNSIGNED", ""

    attestation_bundle = entry.get("attestation_bundle")
    signed_payload     = entry.get("signed_payload")

    if attestation_bundle is None or signed_payload is None:
        raise _Exit(EXIT_INFRA, "Lockfile entry missing attestation_bundle or signed_payload")

    # Serialise bundle and payload to temp files
    if isinstance(attestation_bundle, dict):
        bundle_content = json.dumps(attestation_bundle)
    else:
        bundle_content = str(attestation_bundle)

    if isinstance(signed_payload, dict):
        payload_content = json.dumps(signed_payload)
    elif isinstance(signed_payload, str):
        payload_content = signed_payload
    else:
        payload_content = str(signed_payload)

    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_tmp  = Path(tmpdir) / "bundle.sigstore.json"
        payload_tmp = Path(tmpdir) / "payload"
        bundle_tmp.write_text(bundle_content)
        payload_tmp.write_text(payload_content)

        result = _run_cosign([
            "verify-blob",
            "--bundle", str(bundle_tmp),
            "--offline",
            "--certificate-identity-regexp", ".*",
            "--certificate-oidc-issuer-regexp", ".*",
            str(payload_tmp),
        ])
        # Temp files are cleaned up by TemporaryDirectory context manager

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "invalid signature when validating ASN.1 encoded signature" in stderr:
            registry = entry.get("registry", "<registry>")
            print(f"[✗] Attestation bundle is corrupt")
            print(f"    The attestation_bundle stored in the lockfile cannot be verified.")
            print(f"    This is not a content integrity failure — the stored bundle itself is damaged.")
            print(f"    Recovery: re-run with --registry {registry} to verify against current registry state.")
            raise _Exit(EXIT_INFRA)
        raise _Exit(EXIT_FAIL, f"Bundle verification failed:\n  {stderr}")

    # cosign verify-blob outputs minimal info; extract OIDC from the bundle cert
    subject, issuer = _oidc_from_bundle(attestation_bundle)

    print(f"[✓] Attestation bundle verified (offline)")
    print(f"    Signer: {subject} ({issuer})")
    print(f"    Note:   Rekor entry logged at install time — not re-queried")

    return subject, issuer


# ── NOT Verified blocks ───────────────────────────────────────────────────────

def _print_not_verified_online(registry_url: str) -> None:
    print(f"\nWhat this script did NOT verify:")
    print(f"  - Whether the registry at {registry_url} is one you should trust")
    print(f"  - Whether the registry signing identity is the legitimate operator of this registry")
    print(f"  - Whether the publisher OIDC identity is the legitimate owner of this source repository")
    print(f"  - Content safety, malicious behavior, or sandbox escape")


def _print_not_verified_offline(registry_url: str) -> None:
    print(f"\nThis verification reflects content state at install time only.")
    print(f"\nWhat this script did NOT verify:")
    print(f"  - Whether this content has been revoked since installation")
    print(f"  - Whether the registry's trust tier assignment has changed")
    print(f"  - Whether the registry signing identity is still the current operator")
    print(f"  - Whether a newer version supersedes this one")
    print(f"  - Whether the registry at {registry_url} is one you should trust")
    print(f"  - Content safety, malicious behavior, or sandbox escape")


# ── Mode runners ──────────────────────────────────────────────────────────────

def _run_online(directory: str, registry_url: str, source_uri: str | None, json_out: bool) -> int:
    state: dict = {
        "schema_version": 1,
        "mode":           "online",
        "content_hash":   None,
        "registry":       registry_url,
        "result":         "FAILED",
        "steps": {
            "hash_computed":           False,
            "manifest_fetched":        False,
            "manifest_bundle_verified": False,
            "hash_found_in_manifest":  False,
            "item_rekor_verified":     None,
            "publisher_rekor_verified": None,
        },
        "registry_attestation": None,
        "item_attestation":     None,
        "publisher_attestation": None,
        "not_verified": [
            "registry trustworthiness",
            "registry signing identity legitimacy",
            "publisher OIDC identity ownership",
            "content safety",
        ],
        "error": None,
    }

    def _finish(code: int, error: str = "") -> int:
        state["error"] = error or None
        _print_not_verified_online(registry_url)
        if json_out:
            print()
            print(json.dumps(state, indent=2))
        return code

    try:
        content_hash = _step1_compute_hash(directory)
        state["content_hash"] = content_hash
        state["steps"]["hash_computed"] = True

        _, manifest = _online_step2(registry_url)
        state["steps"]["manifest_fetched"] = True
        state["steps"]["manifest_bundle_verified"] = True

        item = _online_step3(manifest, content_hash)
        state["steps"]["hash_found_in_manifest"] = True

        # Step 4
        log_index: int | None = item.get("rekor_log_index")
        if log_index is None:
            trust = "UNSIGNED"
            state["steps"]["item_rekor_verified"] = None
        else:
            state["steps"]["item_rekor_verified"] = False
            i_subject, i_issuer, i_idx = _online_step4(item, content_hash)
            state["steps"]["item_rekor_verified"] = True
            state["item_attestation"] = {
                "rekor_log_index": i_idx,
                "signer_subject":  i_subject,
                "signer_issuer":   i_issuer,
            }
            trust = "SIGNED"

        # Step 5
        if source_uri is None:
            state["steps"]["publisher_rekor_verified"] = None
        else:
            state["steps"]["publisher_rekor_verified"] = False
        p_subject, p_issuer, p_idx = _online_step5(source_uri, content_hash)
        if p_subject is not None:
            state["steps"]["publisher_rekor_verified"] = True
            state["publisher_attestation"] = {
                "rekor_log_index": p_idx,
                "signer_subject":  p_subject,
                "signer_issuer":   p_issuer,
            }
            if trust == "SIGNED":
                trust = "DUAL-ATTESTED"

        state["result"] = trust
        print(f"\nTrust result: {trust}")
        return _finish(EXIT_OK)

    except _Exit as e:
        state["result"] = "FAILED"
        if e.message:
            print(e.message, file=sys.stderr)
        return _finish(e.code, e.message)


def _run_offline(directory: str, lockfile_path: str, json_out: bool) -> int:
    registry_url = "unknown"

    state: dict = {
        "schema_version": 1,
        "mode":           "offline",
        "content_hash":   None,
        "lockfile":       lockfile_path,
        "result":         "FAILED",
        "steps": {
            "hash_computed":         False,
            "lockfile_parsed":       False,
            "hash_found_in_lockfile": False,
            "bundle_verified":       None,
        },
        "bundle_attestation": None,
        "not_verified": [
            "revocation status since installation",
            "registry trust tier changes since installation",
            "registry signing identity currency",
            "superseding versions",
            "registry trustworthiness",
            "content safety",
        ],
        "error": None,
    }

    def _finish(code: int, error: str = "") -> int:
        state["error"] = error or None
        _print_not_verified_offline(registry_url)
        if json_out:
            print()
            print(json.dumps(state, indent=2))
        return code

    try:
        content_hash = _step1_compute_hash(directory)
        state["content_hash"] = content_hash
        state["steps"]["hash_computed"] = True

        lockfile = _offline_step2(lockfile_path)
        state["steps"]["lockfile_parsed"] = True

        matching = _offline_step3(lockfile, lockfile_path, content_hash)
        state["steps"]["hash_found_in_lockfile"] = True
        registry_url = matching[0].get("registry", "unknown")

        # Step 4 for each matching entry
        worst = EXIT_OK
        trust = "UNSIGNED"
        for entry in matching:
            tier = entry.get("trust_tier", "UNKNOWN")
            if tier == "UNSIGNED":
                state["steps"]["bundle_verified"] = None
                continue

            state["steps"]["bundle_verified"] = False
            try:
                subject, issuer = _offline_step4(entry)
            except _Exit as e:
                worst = max(worst, e.code)
                if e.message:
                    print(e.message, file=sys.stderr)
                continue

            state["steps"]["bundle_verified"] = True
            state["bundle_attestation"] = {
                "signer_subject":  subject,
                "signer_issuer":   issuer,
                "verified_offline": True,
            }
            trust = tier  # SIGNED or DUAL-ATTESTED

        if worst != EXIT_OK:
            state["result"] = "FAILED"
            print(f"\nTrust result: FAILED")
            return _finish(worst)

        state["result"] = trust
        print(f"\nTrust result: {trust}")
        return _finish(EXIT_OK)

    except _Exit as e:
        state["result"] = "FAILED"
        if e.message:
            print(e.message, file=sys.stderr)
        return _finish(e.code, e.message)


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="moat-verify",
        description="Verify MOAT-attested content (reference implementation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Online:  moat-verify <directory> --registry <url> [--source <uri>] [--json]\n"
            "Offline: moat-verify <directory> --lockfile <path> [--json]"
        ),
    )
    parser.add_argument("directory",   help="Path to content directory to verify")
    parser.add_argument("--registry",  metavar="<url>",  help="Registry manifest URL (online mode)")
    parser.add_argument("--lockfile",  metavar="<path>", help="MOAT lockfile path (offline mode)")
    parser.add_argument("--source",    metavar="<uri>",  help="Source repo URI for publisher co-attestation (online only)")
    parser.add_argument("--json",      action="store_true", help="Emit machine-readable JSON output")

    args = parser.parse_args()

    # Mutual exclusion
    if args.registry and args.lockfile:
        print(
            "--lockfile verifies against your stored install snapshot; "
            "--registry verifies against current registry state. "
            "They answer different questions — run one at a time.",
            file=sys.stderr,
        )
        sys.exit(EXIT_INPUT)

    if not args.registry and not args.lockfile:
        parser.print_help(sys.stderr)
        sys.exit(EXIT_INPUT)

    # --source not valid in offline mode
    if args.lockfile and args.source:
        print("Error: --source is not valid in offline mode.", file=sys.stderr)
        # Check if content was installed as Signed to emit spec-required message
        lf_path = Path(args.lockfile)
        if lf_path.exists():
            try:
                lf = json.loads(lf_path.read_text())
                tiers = {e.get("trust_tier") for e in lf.get("entries", [])}
                if tiers & {"SIGNED", "UNSIGNED"} and "DUAL-ATTESTED" not in tiers:
                    print(
                        "Content was installed as Signed — no publisher attestation bundle is available.",
                        file=sys.stderr,
                    )
            except Exception:
                pass
        sys.exit(EXIT_INPUT)

    # Validate --source is a GitHub URI
    if args.source and not args.source.startswith(GITHUB_URI_PREFIX):
        print(
            "Error: --source URI must be a GitHub repository "
            "(https://github.com/<owner>/<repo>). "
            "GitLab and other platforms are not yet supported.",
            file=sys.stderr,
        )
        sys.exit(EXIT_INPUT)

    if args.registry:
        sys.exit(_run_online(args.directory, args.registry, args.source, args.json))
    else:
        sys.exit(_run_offline(args.directory, args.lockfile, args.json))


if __name__ == "__main__":
    main()
