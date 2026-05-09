Slice 4 test bead — TDD red phase.

Write `.ship/npm-distribution-spec/conformance/slice-4.sh`.

Asserts:
- `grep -nE '^## Backfill.+\(normative' specs/npm-distribution.md` returns one match.
- `grep -nE '^## npm Provenance \(informative\)' specs/npm-distribution.md` returns one match.
- `grep -n -E 'Verified|Dual-Attested|Signed|Unsigned' specs/npm-distribution.md` finds all four labels used consistently with their moat-spec.md definitions; no fourth tier is invented.
- `grep -n 'registry_backfill_signing_profile' specs/npm-distribution.md` returns zero matches.
- The closing ## Scope section exists with both **Current version:** and **Planned future version:** bold-label one-liners.

Red phase required before close.
