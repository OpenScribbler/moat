Slice 5 test bead — TDD red phase.

Write `.ship/npm-distribution-spec/conformance/slice-5.sh`.

Asserts:
- `grep -n 'npm-distribution' website/astro.config.mjs` returns at least one match — the new sidebar entry sits alongside the existing spec/publisher-action / spec/registry-action entries.
- `test -f website/src/content/docs/spec/npm-distribution.md` exits 0; the mirror's first heading line matches the canonical sub-spec's first heading line.
- `head -40 CHANGELOG.md | grep -E '^## \[Unreleased\]'` returns exactly one match; below it, an ### Added line and a ### Changed line both appear before the next ## [<version>] heading.
- `grep -nE '\*\*specs/npm-distribution\.md\*\*' CHANGELOG.md` returns at least one match in the [Unreleased] block.
- `grep -nE '\*\*specs/github/(publisher|registry)-action\.md\*\*' CHANGELOG.md` returns at least two matches, all containing the literal phrase "no normative change".
- `awk '/^## \[Unreleased\]/,/^## \[[0-9]/' CHANGELOG.md | grep -nE '(panel|persona|five-persona|adversarial|reviewer feedback|agent consensus|SC-[0-9]|DQ-[0-9]|SB-[0-9])'` returns no matches in the [Unreleased] section per the project changelog rules.

Red phase required before close.
