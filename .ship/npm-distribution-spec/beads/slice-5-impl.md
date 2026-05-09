Slice 5 impl bead — TDD green phase.

Files:
- Create `website/src/content/docs/spec/npm-distribution.md` with Starlight YAML frontmatter and a body mirroring `specs/npm-distribution.md` (frontmatter top, body below).
- Update `website/src/content/docs/spec/core.md` line 9's **Sub-specs:** header to add [npm Distribution](/spec/npm-distribution) alongside the existing three slug entries. No other lines in core.md change (other links use slug form and are unaffected by the directory move).
- Update `website/astro.config.mjs` Specification sidebar group (lines 87–94) to add { label: 'npm Distribution', slug: 'spec/npm-distribution' }; existing slugs preserved.
- Run the audit `grep -rln 'specs/publisher-action.md\|specs/registry-action.md' website/src/` and update any path-form references found to specs/github/...; expected result is zero matches (the website uses slug form throughout).
- Add the [Unreleased] block to `CHANGELOG.md`: one ### Added bullet for **specs/npm-distribution.md** describing the new sub-spec; one ### Changed bullet for **specs/github/publisher-action.md** and **specs/github/registry-action.md** documenting the directory move with the explicit "no normative change" phrase. Both bullets follow the bold-label form.

Green phase: `.ship/npm-distribution-spec/conformance/slice-5.sh` exits 0.

Checkpoint: running the website's local preview command renders the Starlight sidebar with the new /spec/npm-distribution entry and the existing four spec entries; the new page loads with the canonical sub-spec body; `head -30 CHANGELOG.md` shows an [Unreleased] section whose two bullets pass the project changelog pre-save checklist (no panel/persona/finding-ID/count language).
