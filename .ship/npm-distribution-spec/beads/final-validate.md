Run the full check suite across all 5 slices (slice-1.sh through slice-5.sh) and verify the feature acceptance.

Verify:
- specs/npm-distribution.md is feature-complete and passes the four MOAT design tests in CLAUDE.md:121-127
- specs/github/{publisher,registry}-action.md exist with correct Part of: link depth
- CHANGELOG.md [Unreleased] passes the project changelog rules pre-save checklist
- website mirror renders via the Astro build

ADRs 0001-0004 flip Proposed->Accepted on close.
