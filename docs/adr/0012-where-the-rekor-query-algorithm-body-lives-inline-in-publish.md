# 0012. Where the Rekor-query algorithm body lives — inline in §Publisher Verification vs in a new §Rekor Query subsection vs only in the reference workflow

Date: 2026-05-12
Status: Accepted
Feature: npm-distribution-spec

## Context

Path 2 was already partly inline at `specs/npm-distribution.md:144`; with Path 1 dropped (D2), there is exactly one verification path and exactly one place a reader looks for it. A new §Rekor Query subsection would split the algorithm from its only call site, forcing every conformance script and ADR cross-reference to chase the heading rename. Leaving the algorithm only in the reference workflow would violate the "Requirements must be enforceable" principle in `CLAUDE.md` — the spec's MUSTs about query semantics, `logIndex` tiebreaker, and anti-rollback would have no normative home. Inlining keeps the normative obligation co-located with the trigger condition, matches the existing single-paragraph-per-clause style at `:142`/`:144`, and lets slice-script grep anchors stay on the §Publisher Verification heading.

## Decision

Chose **Inline in §Publisher Verification (`specs/npm-distribution.md:136`).** over **A new §Rekor Query subsection (sibling to §Publisher Verification); leaving the algorithm only in `reference/moat-npm-publisher.yml`.**.

## Consequences

§Publisher Verification grows by roughly the span of the current Path 2 paragraph plus the tiebreaker and anti-rollback clauses; the existing two-paragraph Path 1/Path 2 split collapses into one normative paragraph + one tiebreaker paragraph + one anti-rollback paragraph. The slice script anchor (currently absent for this section per research Q8) can be added without a heading change. Future amendments that introduce a second verification path (e.g., for a private-registry backfill, see D10) will need to revisit whether the section should be split — that is a future decision, not this round's. **This Disambiguation triggers ADR-0012 (proposed) to record the verification-path consolidation.**
