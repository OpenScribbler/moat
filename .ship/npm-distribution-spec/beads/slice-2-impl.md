Slice 2 impl bead — TDD green phase.

Create `specs/npm-distribution.md` with the house-style metadata header (H1 # npm Distribution Specification; Version: 0.1.0 (Draft); Requires: moat-spec.md ≥ 0.7.1; Part of: link to ../moat-spec.md; one-line blockquote; trailing ---).

Then write the two normative-spine sections:
1. ## Content Hash Domain (normative) — names the unpacked Distribution Tarball's Content Directory as the input domain; cites `reference/moat_hash.py` for the algorithm; explains the relationship to npm's tarball SHA-512 (npm's own integrity primitive, not the MOAT Content Hash).
2. ## Revocation at the Materialization Boundary (normative) — anchors MUSTs at resolve/fetch/unpack; cites moat-spec.md (lockfile revoked_hashes semantics) without redefinition; specifies the MOAT_ALLOW_REVOKED per-hash escape hatch (env var with comma-separated sha256 hashes); requires resolve-time skip-logging when a Conforming Client skips a revoked hash.

Green phase: `.ship/npm-distribution-spec/conformance/slice-2.sh` exits 0.

Checkpoint: a manual read against the four MOAT design tests in CLAUDE.md:121-127 confirms each MUST is enforceable at the materialization boundary.
