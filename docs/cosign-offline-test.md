# cosign Offline Bundle Verification — Implementer Test Guide

This guide documents the empirical tests that established the normative behavior of `moat-verify`'s `--lockfile` offline mode. Run these tests before implementing offline bundle verification to confirm cosign behaves as the spec requires on your platform and version.

**Why this matters:** The offline verification spec depends on two cosign behaviors that are not guaranteed by documentation alone:
1. The `--offline` flag is supported and suppresses Rekor network calls
2. Expired signing certificates are accepted when the bundle contains a valid Rekor entry

Both were verified empirically before being written into the normative spec. If either behavior differs on your platform, the spec design may need revision.

---

## Prerequisites

- **cosign** v2.x installed and on PATH (`cosign version` to confirm)
- **Python** 3.9+
- **Browser** and a GitHub or Google account (for the OIDC authentication step)
- **~15 minutes** (10 of which are just waiting for a cert to expire)

---

## Test script

All three scenarios are implemented in [`reference/test_offline_verify.py`](../reference/test_offline_verify.py). The script creates test artifacts in `reference/test_artifacts/` (gitignored).

---

## Scenario 1: Fresh bundle (cert valid)

Signs a test blob with cosign keyless, then immediately verifies offline. Confirms the `--offline` flag works and that basic bundle verification succeeds.

**Run:**

```bash
python3 reference/test_offline_verify.py fresh
```

This step requires interactive OIDC authentication. cosign will print a URL — open it in your browser and sign in. The signing completes automatically once you authenticate. You will be asked to type `y` to acknowledge the Sigstore terms before the browser flow begins.

**Expected output:**

```
[PASS] cosign verify-blob (fresh cert) (--offline)
exit code: 0 (expected 0)
stderr: Verified OK

FINDING — --offline flag supported: True
FINDING — fresh bundle verification: PASS
```

**If `--offline` flag is not recognized:** The script retries without it and reports `FINDING — --offline flag supported: False`. This means your cosign version verifies the bundle without an explicit offline flag — note this for your implementation. The spec's normative invocation uses `--offline`; confirm whether omitting it still suppresses Rekor on your version.

**If verification fails entirely:** Do not proceed to Scenario 2. Investigate why cosign cannot verify the bundle before testing offline behavior with an aged cert.

---

## Scenario 2: Aged bundle (cert expired)

Re-verifies the bundle from Scenario 1 after the signing certificate has expired. This is the critical test. Sigstore certificates are valid for approximately 10 minutes. Verification with an expired cert confirms that cosign validates against the Rekor timestamp in the bundle rather than the certificate validity window.

**Wait:** At least 10 minutes after Scenario 1 completed.

**Run:**

```bash
python3 reference/test_offline_verify.py aged
```

**Expected output:**

```
[PASS] cosign verify-blob (aged cert) (--offline)
exit code: 0 (expected 0)
stderr: Verified OK

FINDING — expired cert accepted: YES
Cosign validates against the Rekor timestamp, not the cert validity window.
--lockfile offline verification is viable for aged bundles.
```

**If the aged cert is rejected (exit non-0):** The `--lockfile` mode as designed is not viable. Offline verification of real-world bundles (where certs are always expired by verification time) will always fail. The spec design must be revised — likely to a different verification approach that does not require re-running `cosign verify-blob` against the original payload. File an issue before proceeding with implementation.

---

## Scenario 3: Corrupt bundle

Modifies a valid bundle (flipping bytes in the signature field) and confirms cosign rejects it with a distinguishable error message. This validates the exit code mapping in the spec: corrupt bundle → moat-verify exit 3, not exit 1.

**Run (any time after Scenario 1):**

```bash
python3 reference/test_offline_verify.py corrupt
```

**Expected output:**

```
[PASS] Corrupt bundle rejected
exit code: 1
stderr: Error: invalid signature when validating ASN.1 encoded signature
        error during command execution: invalid signature when validating ASN.1 encoded signature

FINDING — corrupt bundle exit code: 1
FINDING — error distinguishable from hash mismatch: review stderr above
```

**Key observation:** cosign returns exit code 1 for both corrupt bundles and hash mismatches — the exit code alone does not distinguish the two. moat-verify MUST inspect stderr:

- `invalid signature when validating ASN.1 encoded signature` → moat-verify exit 3 (corrupt stored artifact)
- Other non-zero cosign exit → moat-verify exit 1 (verification failure)

**If the error string differs on your cosign version:** Update your implementation's stderr matching logic accordingly. The spec states the normative behavior; the exact error string used to detect it is an implementation detail that may vary by cosign version.

---

## Running all scenarios

```bash
# Scenario 1 + 3 (fresh and corrupt — no waiting required)
python3 reference/test_offline_verify.py all

# Then wait 10+ minutes and run:
python3 reference/test_offline_verify.py aged
```

---

## Interpreting results

| Scenario | Expected | If unexpected |
|---|---|---|
| Fresh | exit 0, `Verified OK` | Do not proceed — investigate cosign setup |
| Aged | exit 0, `Verified OK` | Offline mode design is not viable — file issue |
| Corrupt | exit 1, `invalid signature...` error | Update stderr matching logic for your cosign version |

All three scenarios must pass before implementing `--lockfile` mode. The aged bundle test is the gate. Everything else in the spec is design judgment; that one is empirical.

---

## Reference

- Normative spec: [`specs/moat-verify.md`](../specs/moat-verify.md) — Offline Verification Steps section
- Issue resolutions: [`docs/open-issues.md`](open-issues.md)
- Test script: [`reference/test_offline_verify.py`](../reference/test_offline_verify.py)
- Verified against: cosign v2.5.2, linux/amd64, April 2026
