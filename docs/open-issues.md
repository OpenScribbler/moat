# MOAT Open Issues

Issues requiring resolution before `--lockfile` offline mode can be promoted to normative spec in `specs/moat-verify.md`.

**Status values:** Open · Resolved · Deferred

---

## Issue 1 — `--lockfile` + `--registry` mutual exclusivity

**Status:** Resolved  
**File:** `specs/moat-verify.md`

If both `--lockfile` and `--registry` are passed, is that exit 2 (input error) or does one silently take precedence?

**Resolution:** Exit 2. They answer fundamentally different questions — `--registry` verifies against current live registry state (can detect revocations, tier changes); `--lockfile` verifies against the stored install snapshot (proves "this was valid when installed"). Combining them silently produces ambiguous output that answers neither question clearly. Precedence rules hide the mode that wasn't invoked; exit 2 forces the End User to be explicit.

**Error message guidance:** The error message is load-bearing. A bare "incompatible flags" message will generate confusion. The message MUST explain why they are mutually exclusive, not just that they are. Suggested: *"`--lockfile` verifies against your stored install snapshot; `--registry` verifies against current registry state. They answer different questions — run one at a time."*

**Spec language needed:** When `--lockfile` is promoted to normative, the Interface section MUST include a prose explanation of the mode distinction — not just a flag listing. The current spec has no such language because `--lockfile` is not yet normative.

---

## Issue 2 — Exit code when computed hash is not in lockfile

**Status:** Resolved  
**File:** `specs/moat-verify.md`

If the computed hash is not found in the lockfile, is that exit 1 (verification failure) or exit 2 (input error — wrong lockfile for this directory)?

**Resolution:** Exit 1. The tool cannot distinguish "wrong lockfile" from "content was modified since installation" — both produce a hash that isn't in the lockfile. Returning exit 2 would frame a potential security signal as user error, which is exactly backwards for a security verification tool. Consistent with online mode (Step 3: hash not in manifest → exit 1).

The one genuine exit 2 case is if the lockfile file itself doesn't exist or is malformed — that's bad input. A well-formed lockfile that doesn't contain the hash is a verification outcome.

**Error message guidance:** The output MUST acknowledge both interpretations without claiming to know which applies:
```
[✗] Hash not found in lockfile
    Computed:  sha256:<hex>
    Lockfile:  <path>

    This means either: the content was modified after installation, or
    this lockfile does not correspond to this directory.
    moat-verify cannot distinguish between these cases.
```

---

## Issue 3 — Multiple lockfile entries with the same content hash

**Status:** Resolved  
**File:** `specs/moat-verify.md`

If the lockfile has two entries with identical `content_hash` values (same content attested by two different registries), should the tool report both matches or just the first?

**Resolution:** Report all matches. Suppressing duplicates hides meaningful trust signal — multiple independent attestations is stronger than one. "First match" behavior also depends on lockfile ordering, which is an implementation artifact, not a trust property. In practice, multiple entries for the same hash will be common (aggregators re-index content across registries without coordination), so output must remain legible for three or more matches.

**Partial failure rule:** If one registry's attestation passes and another's fails, exit code is determined by worst outcome — exit 1 if any attestation fails. Output MUST include a per-registry breakdown so the End User can see which passed and which failed. "Some attestations verified" is not verified. This also closes a bypass: an attacker cannot launder a failed attestation through a passing one by publishing to multiple registries.

---

## Issue 4 — Multiple lockfile entries with the same name but different hashes

**Status:** Resolved  
**File:** `specs/moat-verify.md`

If the lockfile has two entries with the same `name` but different `content_hash` values (two installed versions), which entry does the tool use?

**Resolution:** Verify by hash match — check all entries with the matching name and use whichever one's `content_hash` matches the computed hash. Name is display metadata, not identity; picking by name alone would risk verifying the wrong entry and producing a false positive.

- If neither entry matches: exit 1 (same two-interpretation error message as Issue 2 — wrong lockfile or content modified)
- If both entries match: exit 2 — malformed lockfile (two different `content_hash` values cannot both equal the same computed hash; this is a lockfile integrity problem, not a verification outcome)

**Output guidance:** The spec MUST require that output identifies all entries found for the name, which one matched, and that others were skipped due to hash mismatch. Silently picking one result with no indication of alternatives causes confusion when lockfile ordering changes between runs.

---

## Issue 5 — `--source` combined with `--lockfile`

**Status:** Resolved  
**File:** `specs/moat-verify.md`

Publisher attestation in online mode re-fetches `moat-attestation.json` from the source URI. In offline mode there is no network call, so `--source` cannot reach a remote URI.

**Resolution:** Exit 2. Publisher attestation for Dual-Attested content is already captured in the `attestation_bundle` stored in the lockfile at install time — no separate `--source` flag is needed or possible in offline mode.

**Error message guidance:** The message MUST do three things:
1. Explain why `--source` doesn't apply in offline mode (no network calls)
2. Explain that publisher attestation from install time is verified automatically from the bundle if present
3. Tell the End User that `--registry` (online mode) is the path if current publisher state is needed

**Signed content case:** If the content was installed as Signed (no publisher attestation bundle in the lockfile entry), the error MUST state this explicitly: *"Content was installed as Signed — no publisher attestation bundle is available."* A generic flag conflict message is insufficient when the user may not know the trust tier of the installed content.

---

## Issue 6 — Exit code 3 applicability in offline mode

**Status:** Resolved  
**File:** `specs/moat-verify.md`

Exit code 3 covers infrastructure failures (Rekor unreachable, registry unreachable). In offline mode there are no external calls. Does exit code 3 ever apply?

**Resolution:** Yes. Exit 3 applies in offline mode for:
1. **Structurally invalid `attestation_bundle`** in the lockfile — the bundle was written at install time by the conforming client, not by the End User. The End User cannot fix this by changing their invocation; exit 2 would be misleading.
2. **cosign verification errors that are not hash mismatches** — cosign itself or the bundle is broken, not fixable by re-running with different flags.

The key distinction: exit 2 means the End User made a mistake they can fix; exit 3 means something outside their control produced bad data. A corrupt bundle falls into exit 3 because the End User didn't author it.

**Exit code table update needed:** The current table describes exit 3 only in terms of remote failures (registry unreachable, Rekor unreachable). It MUST be expanded to clarify that exit 3 also covers corrupt stored artifacts in offline mode. A two-column format (online triggers / offline triggers) makes this unambiguous.

**Recovery guidance:** Exit 3 in offline mode MUST suggest re-running with `--registry` (online mode) as the recovery path — a corrupt offline bundle means stored attestation state is lost and must be re-verified from source.

**Implementation note (from Issue 8 testing):** Cosign returns exit 1 for both hash mismatch and corrupt/invalid signature. moat-verify must inspect cosign's stderr to determine which case applies before mapping to its own exit code. `invalid signature when validating ASN.1 encoded signature` in stderr → moat-verify exit 3.

---

## Issue 7 — NOT-verified block content for offline mode

**Status:** Resolved  
**File:** `specs/moat-verify.md`

Online mode's NOT-verified block covers: registry trustworthiness, registry signing identity legitimacy, publisher OIDC identity ownership, content safety. Offline mode has a different set of non-verifiable claims.

**Resolution:** Add a framing sentence before the list to communicate that offline verification is historical, not current — this is the most important thing users miss when skimming bullet points. Add registry signing identity (gap in the original proposal). Reorder so revocation leads as the most security-relevant omission.

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

## Issue 8 — `attestation_bundle` verification mechanics in offline mode

**Status:** Resolved  
**File:** `specs/moat-verify.md`

Online mode calls `cosign verify-blob` against a live Rekor entry. Offline mode must verify the stored bundle without a live Rekor query. The correct invocation is not confirmed.

**Resolution (empirically verified — cosign v2.5.2):** Tested via `reference/test_offline_verify.py` against three real scenarios. See `reference/test_artifacts/` for test artifacts.

Normative invocation:
```
cosign verify-blob \
  --bundle <bundle-path> \
  --offline \
  --certificate-identity-regexp <expected-identity> \
  --certificate-oidc-issuer-regexp <expected-issuer> \
  <content-file>
```

**Scenario results:**
1. **Fresh bundle (cert valid):** exit 0, `Verified OK`. `--offline` flag is supported.
2. **Aged bundle (cert expired):** exit 0, `Verified OK`. Cosign validates against the Rekor timestamp in the bundle, not the cert validity window. Expired certs are accepted. Offline verification of aged bundles is viable.
3. **Corrupt bundle (signature modified):** exit 1, `Error: invalid signature when validating ASN.1 encoded signature`. Rejected with a distinguishable error message.

**Critical spec obligation (surfaces from scenario 3):** Cosign returns exit 1 for both hash mismatch and corrupt bundle — moat-verify MUST NOT pass cosign's exit code through directly. It must inspect cosign's stderr to distinguish:
- `invalid signature when validating ASN.1 encoded signature` → moat-verify exit 3 (corrupt stored artifact, not fixable by End User)
- Hash mismatch error → moat-verify exit 1 (clean verification failure)

This obligation must be written into the normative moat-verify spec when `--lockfile` is promoted.
