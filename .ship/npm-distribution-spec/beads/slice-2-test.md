Slice 2 test bead — TDD red phase.

Write `.ship/npm-distribution-spec/conformance/slice-2.sh`.

Asserts:
- `head -9 specs/npm-distribution.md` matches the house-style header pattern (H1 ending in "Specification", Version, Requires, Part of: [MOAT Specification](../moat-spec.md), blockquote, trailing ---).
- Every section heading in the file ends in (normative), (normative — MUST), (normative — SHOULD), (informative), or (optional).
- `grep -E 'def content_hash|rglob|NFC' specs/npm-distribution.md` returns zero matches (the algorithm is cited from reference/moat_hash.py, not redefined).
- `grep -n 'revoked_hashes' specs/npm-distribution.md` matches are all references (no field definitions).

Red phase required before close: the script runs and fails before Slice 2 impl lands.
