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
