#!/usr/bin/env python3
"""
test_offline_verify.py — Empirical test of cosign offline bundle verification.

Resolves Issue 8 in docs/open-issues.md before --lockfile mode can be written
into normative spec. Three scenarios test what moat-verify's offline mode can
actually rely on from cosign.

Scenarios
---------
  fresh   -- Sign a test blob, immediately verify with --offline (cert valid)
  aged    -- Re-verify the same saved bundle after the cert has expired (~10 min)
  corrupt -- Corrupt a valid bundle, confirm cosign rejects it with identifiable error

Usage
-----
  python3 test_offline_verify.py fresh    # requires browser for OIDC sign-in
  python3 test_offline_verify.py aged     # run 10+ minutes after fresh
  python3 test_offline_verify.py corrupt  # uses bundle saved by fresh
  python3 test_offline_verify.py all      # fresh + corrupt (aged requires waiting)

Artifacts
---------
Saved to reference/test_artifacts/ (gitignored):
  test_blob.txt              -- the content that was signed
  test_bundle.sigstore.json  -- the cosign bundle from fresh
  test_identity.json         -- signing timestamp and cert metadata

Findings
--------
Each scenario prints the exact cosign invocation, exit code, stdout, and
stderr. Record findings in docs/open-issues.md Issue 8 resolution.
"""

import json
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

ARTIFACTS = Path(__file__).parent / "test_artifacts"
BLOB = ARTIFACTS / "test_blob.txt"
BUNDLE = ARTIFACTS / "test_bundle.sigstore.json"
CORRUPT_BUNDLE = ARTIFACTS / "test_bundle_corrupt.sigstore.json"
IDENTITY = ARTIFACTS / "test_identity.json"

# Minimal MOAT-style payload — realistic test content, not a real attestation.
BLOB_CONTENT = json.dumps(
    {
        "content_hash": "sha256:test_only_not_a_real_hash",
        "source_uri": "https://github.com/test/test-skills",
        "content_type": "skill",
        "note": "test artifact for cosign offline verification — not a real attestation",
    },
    indent=2,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    print(f"\n  $ {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True)


def report(label: str, result: subprocess.CompletedProcess, expected_exit: int) -> bool:
    passed = result.returncode == expected_exit
    status = "PASS" if passed else "FAIL"
    print(f"\n  [{status}] {label}")
    print(f"  exit code: {result.returncode} (expected {expected_exit})")
    if result.stdout.strip():
        print(f"  stdout:\n{textwrap.indent(result.stdout.strip(), '    ')}")
    if result.stderr.strip():
        print(f"  stderr:\n{textwrap.indent(result.stderr.strip(), '    ')}")
    return passed


def verify(bundle: Path, extra_flags: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run cosign verify-blob. Uses regexp wildcards — test only, not production."""
    cmd = [
        "cosign", "verify-blob",
        "--bundle", str(bundle),
        "--certificate-identity-regexp", ".*",
        "--certificate-oidc-issuer-regexp", ".*",
    ]
    if extra_flags:
        cmd.extend(extra_flags)
    cmd.append(str(BLOB))
    return run(cmd)


def try_verify_with_offline_fallback(label_prefix: str, bundle: Path, expected_exit: int) -> tuple[bool, bool]:
    """
    Try cosign verify-blob --offline. If --offline is an unknown flag, retry
    without it. Returns (passed, offline_flag_supported).
    """
    result = verify(bundle, ["--offline"])
    offline_supported = "unknown flag" not in result.stderr.lower()

    if not offline_supported:
        print(f"\n  Note: --offline flag not recognized by this cosign version. Retrying without it.")
        result = verify(bundle)

    passed = report(
        f"{label_prefix} ({'--offline' if offline_supported else 'no --offline flag'})",
        result,
        expected_exit,
    )
    return passed, offline_supported


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def test_fresh() -> bool:
    """Sign test blob and immediately verify offline. Cert is still valid."""
    print("\n" + "=" * 60)
    print("SCENARIO 1: FRESH BUNDLE (cert valid)")
    print("=" * 60)
    print(
        "\nThis step requires browser-based OIDC authentication.\n"
        "cosign will open a browser window — sign in to continue.\n"
    )

    ARTIFACTS.mkdir(exist_ok=True)
    BLOB.write_text(BLOB_CONTENT)
    print(f"Test blob written to: {BLOB}")

    result = run([
        "cosign", "sign-blob",
        "--bundle", str(BUNDLE),
        "--yes",
        str(BLOB),
    ])

    if result.returncode != 0:
        print(f"\n[FAIL] Signing failed (exit {result.returncode})")
        print(result.stderr)
        return False

    print(f"\n[OK] Bundle written to: {BUNDLE}")

    # Save signing timestamp and cert metadata for the aged test.
    try:
        bundle_data = json.loads(BUNDLE.read_text())
        cert_b64 = None
        vm = bundle_data.get("verificationMaterial", {})
        if "certificate" in vm:
            cert_b64 = vm["certificate"].get("rawBytes")
        elif "x509CertificateChain" in vm:
            chain = vm["x509CertificateChain"].get("certificates", [])
            if chain:
                cert_b64 = chain[0].get("rawBytes")

        IDENTITY.write_text(json.dumps({
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "cert_b64": cert_b64,
            "note": "Sigstore certs are valid ~10 min. Run 'aged' scenario after expiry.",
        }, indent=2))
        print(f"Identity metadata saved to: {IDENTITY}")
    except Exception as exc:
        print(f"  Warning: could not extract identity metadata: {exc}")

    passed, offline_supported = try_verify_with_offline_fallback(
        "cosign verify-blob (fresh cert)", BUNDLE, expected_exit=0
    )

    print(f"\n  FINDING — --offline flag supported: {offline_supported}")
    print(f"  FINDING — fresh bundle verification: {'PASS' if passed else 'FAIL'}")
    return passed


def test_aged() -> bool:
    """
    Verify the saved bundle after the signing cert has expired.
    This is the critical test: does cosign accept an expired cert
    when verification is grounded by the bundled Rekor entry?
    """
    print("\n" + "=" * 60)
    print("SCENARIO 2: AGED BUNDLE (cert expired)")
    print("=" * 60)

    if not BUNDLE.exists():
        print("\n[ERROR] No saved bundle found. Run the 'fresh' scenario first.")
        return False

    if IDENTITY.exists():
        identity = json.loads(IDENTITY.read_text())
        print(f"\n  Bundle signed at: {identity.get('signed_at', 'unknown')}")
        print("  Sigstore certs are valid ~10 minutes. If less time has passed,")
        print("  the cert may still be valid — results will match the fresh test.\n")

    passed, offline_supported = try_verify_with_offline_fallback(
        "cosign verify-blob (aged cert)", BUNDLE, expected_exit=0
    )

    print(f"\n  FINDING — --offline flag supported: {offline_supported}")
    if passed:
        print("  FINDING — expired cert accepted: YES")
        print("  Cosign validates against the Rekor timestamp, not the cert validity window.")
        print("  --lockfile offline verification is viable for aged bundles.")
    else:
        print("  FINDING — expired cert accepted: NO")
        print("  Cosign rejects bundles with expired certs even in offline mode.")
        print("  --lockfile mode as designed is NOT viable — spec must be revised.")

    return passed


def test_corrupt() -> bool:
    """
    Corrupt a valid bundle and confirm cosign rejects it with an identifiable
    error. Maps to exit 3 (unexpected data from stored artifact) per Issue 6.
    """
    print("\n" + "=" * 60)
    print("SCENARIO 3: CORRUPT BUNDLE")
    print("=" * 60)

    if not BUNDLE.exists():
        print("\n[ERROR] No saved bundle found. Run the 'fresh' scenario first.")
        return False

    bundle_data = json.loads(BUNDLE.read_text())
    corrupted = False

    # Handle multiple cosign bundle formats — flip last 4 chars of signature.
    # Format 1 (cosign v2 new): messageSignature.signature
    # Format 2 (cosign v2 old): base64Signature (top-level)
    # Format 3 (DSSE):          dsseEnvelope.signature
    sig_locations = [
        ("messageSignature", "signature"),
        (None, "base64Signature"),          # top-level field
        ("dsseEnvelope", "signature"),
    ]
    for parent, field in sig_locations:
        target = bundle_data.get(parent, bundle_data) if parent else bundle_data
        if target.get(field):
            original = target[field]
            target[field] = original[:-4] + "XXXX"
            corrupted = True
            print(f"\n  Corrupted field: {parent + '.' if parent else ''}{field}")
            break

    if not corrupted:
        print(f"\n  Could not find signature field. Top-level keys: {list(bundle_data.keys())}")
        print("  Falling back to appending garbage to the raw bundle file.")
        CORRUPT_BUNDLE.write_text(BUNDLE.read_text() + "\nCORRUPTED_GARBAGE")
    else:
        CORRUPT_BUNDLE.write_text(json.dumps(bundle_data, indent=2))
        print(f"  Corrupt bundle written to: {CORRUPT_BUNDLE}")
        print("  (last 4 chars of signature replaced with 'XXXX')")

    result = verify(CORRUPT_BUNDLE, ["--offline"])
    offline_supported = "unknown flag" not in result.stderr.lower()
    if not offline_supported:
        result = verify(CORRUPT_BUNDLE)

    rejected = result.returncode != 0
    status = "PASS" if rejected else "FAIL"
    print(f"\n  [{status}] Corrupt bundle {'rejected' if rejected else 'ACCEPTED — unexpected'}")
    print(f"  exit code: {result.returncode}")
    if result.stdout.strip():
        print(f"  stdout:\n{textwrap.indent(result.stdout.strip(), '    ')}")
    if result.stderr.strip():
        print(f"  stderr:\n{textwrap.indent(result.stderr.strip(), '    ')}")

    print(f"\n  FINDING — corrupt bundle exit code: {result.returncode}")
    print(f"  FINDING — error distinguishable from hash mismatch: review stderr above")
    print(f"  FINDING — maps to exit 3 (unexpected stored artifact data): {'YES — record exit code' if rejected else 'INCONCLUSIVE'}")

    return rejected


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    modes = {"fresh", "aged", "corrupt", "all"}
    if len(sys.argv) < 2 or sys.argv[1] not in modes:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]
    results: dict[str, bool] = {}

    if mode in ("fresh", "all"):
        results["fresh"] = test_fresh()

    if mode == "aged":
        results["aged"] = test_aged()

    if mode in ("corrupt", "all"):
        results["corrupt"] = test_corrupt()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for scenario, passed in results.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {scenario}")

    if mode in ("fresh", "all"):
        print(
            "\nNext step — aged bundle test:\n"
            "  Wait 10+ minutes for the Sigstore cert to expire, then run:\n"
            "  python3 test_offline_verify.py aged"
        )

    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
