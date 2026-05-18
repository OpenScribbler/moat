# 0015. Format of the new §Conformance error-code table

Date: 2026-05-12
Status: Accepted
Feature: npm-distribution-spec

## Context

No existing sub-spec has a conformance error-code table (research Q8 finding) — Round 3 is establishing the pattern. A separate JSON file would split the spec surface across two files and break the "one normative document per channel" property; a Conforming Client implementer would have to read both. The POSIX-exit-code scheme from `moat-verify.md` is the wrong shape: exit codes are end-of-process aggregates, while error codes need to identify *which* MUST was violated mid-process so logs and structured error events (see `specs/npm-distribution.md:51`, `:71`) can carry them. Inline embedding next to each MUST would scatter the table and prevent a reader from getting a one-screen map of conformance obligations. The chosen form — a single table in a single new section, with stable `NPM-<SECTION>-<NN>` codes — matches how the existing slice-script anchors work (one section per concern, grep-able) and gives every MUST/MUST NOT a stable identifier external auditors and CI scripts can cite.

## Decision

Chose **A markdown table with columns `Error Code | Triggering MUST/MUST NOT (file:line) | Description`, embedded in a new `## Conformance (normative)` section at the end of `specs/npm-distribution.md` (after §Compatibility Notes around `:200`). Error codes use the form `NPM-<SECTION>-<NN>` (e.g., `NPM-VERIFY-01`, `NPM-REVOKE-03`).** over **A separate machine-readable file (`specs/conformance/npm-distribution/error-codes.json`) referenced from the spec; reusing `specs/moat-verify.md`'s POSIX exit-code numbering scheme (research Q8 shows it uses `0`/`1`/`2`/`3` exit codes); embedding the error codes inline next to each MUST/MUST NOT in the body.**.

## Consequences

A new `## Conformance (normative)` section is added at the end of `specs/npm-distribution.md` (insertion point near `:200` in the current file, after §Compatibility Notes). The table has approximately 40 rows mapped from the MUST/MUST NOT inventory at research Q8. Slice scripts under `specs/conformance/npm-distribution/` can be extended to assert that emitted error codes match the table (F-C-07 + F-G-01 default treatments). Each error code is stable forever: once `NPM-VERIFY-01` is assigned, the obligation it names cannot be renumbered even if the surrounding section is reorganized; obsolete codes are kept in the table marked `Reserved (was: <description>)` rather than reused. **This Disambiguation triggers ADR-0015 (proposed) to record the error-code naming scheme and stability guarantee.**

Round 4 reinforces this guarantee on the spec surface itself. The §Conformance intro paragraph at `specs/npm-distribution.md:219` now carries three normative sentences that hold conformers to the same stability contract this ADR establishes: code spelling and meaning MUST NOT change after first ship; obsolete codes MUST be retained as `Reserved (was: <description>)` rows rather than reused; and Conforming Clients SHOULD surface codes verbatim. The `slice-8-error-codes.sh` conformance script enforces the citation-anchor half of this guarantee on every CI run (A6 checks every cited line still carries a MUST/MUST NOT token; the slice-8 A7 lint asserts the intro paragraph itself remains in place across spec edits).

## R5 addendum — code-stability lock and split-suffix codes

Round 5 closes two gaps left open by the earlier rounds.

**Code-stability lock file.** `specs/conformance/npm-distribution/error-codes.lock` now lists every code the spec has committed to. Slice-8 assertion A10 verifies that every locked code still appears in the §Conformance table — either as a live row or as `Reserved (was: <description>)`. The table may grow beyond the lock (additions are allowed without a lock entry), but rename or removal of a locked code fails CI. This is the programmatic enforcement of the stability contract the intro paragraph asserts in prose. The lock file is grown only when the spec is cut to a release tag; new codes added between releases sit in the table without lock entries until they ship.

**Split-suffix codes (`NPM-<SECTION>-<NN>-<X>`).** The original `NPM-<SECTION>-<NN>` shape assumed each MUST/MUST NOT corresponds to exactly one failure mode. The R3 `NPM-SCOPE-01` code violated this — it covered both "wrongly attested" and "wrongly refused" failure modes under a single identifier — which forced operators reading logs to disambiguate by context rather than by code. R5 splits it into `NPM-SCOPE-01-A` (wrongly attested) and `NPM-SCOPE-01-B` (wrongly refused), introducing a single-letter split-suffix as a permitted extension to the code-format pattern. The slice-8 A3 regex accepts `NPM-<SECTION>-<NN>(-<X>)?` for codes that need to split a single MUST/MUST NOT into co-adjacent failure-mode variants. The stability contract still holds — once an `-A`/`-B` code is shipped, its spelling is locked. Because `NPM-SCOPE-01` was never tagged into a release, the split was performed without a `Reserved (was: ...)` alias row; future splits of already-shipped codes will require the alias.
