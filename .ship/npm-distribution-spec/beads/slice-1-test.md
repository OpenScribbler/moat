Slice 1 test bead — TDD red phase.

Write `.ship/npm-distribution-spec/conformance/slice-1.sh` (a bash check script).

Asserts:
- `grep -rn "specs/publisher-action.md"` outside `panel/`, `CHANGELOG.md`, and `.ship/` returns zero matches.
- `grep -rn "specs/registry-action.md"` with same exclusions returns zero matches.
- `test -f specs/github/publisher-action.md && test -f specs/github/registry-action.md && test -f specs/moat-verify.md && ! test -e specs/publisher-action.md && ! test -e specs/registry-action.md` exits 0.
- Cross-reference resolution: every Markdown link in moat-spec.md, lexicon.md, README.md, RELEASING.md, docs/guides/publisher.md whose target was the old path now resolves under specs/github/.
- `grep -n 'specs/github' lexicon.md` returns at least the two updated rows.

Red phase required before close: the script must run and fail (exits non-zero) before Slice 1 impl lands.
