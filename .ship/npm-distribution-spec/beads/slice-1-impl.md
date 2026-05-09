Slice 1 impl bead — TDD green phase.

Move and update cross-references for the GitHub-specific sub-specs.

Files:
- Move `specs/publisher-action.md` -> `specs/github/publisher-action.md`
- Move `specs/registry-action.md` -> `specs/github/registry-action.md`
- Update `Part of:` link depth in both moved files (one extra `../`)
- Update cross-references in: moat-spec.md (lines 9, 103, 143, 148, 218, 281, 286, 681, 682, 1068), lexicon.md (lines 43, 44), README.md (lines 35, 36), RELEASING.md (line 99), docs/guides/publisher.md (line 248), reference/moat-publisher.yml (lines 260, 482), reference/moat-registry.yml (line 759), .github/workflows/moat-publisher.yml (lines 260, 482), .github/workflows/moat-registry.yml (line 759)

Panel artifacts under `panel/` are intentionally untouched per the project tooling-only changelog rule.

Green phase required before close: `.ship/npm-distribution-spec/conformance/slice-1.sh` exits 0.

Checkpoint: `find specs -name '*.md' | sort` lists exactly the three target files; the broad grep returns no spec-content hits outside historical entries.
