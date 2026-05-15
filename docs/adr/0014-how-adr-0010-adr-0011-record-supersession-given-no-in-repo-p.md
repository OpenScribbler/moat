# 0014. How ADR-0010 / ADR-0011 record supersession given no in-repo precedent for `Supersedes:` / `Status: Superseded`

Date: 2026-05-12
Status: Accepted
Feature: npm-distribution-spec

## Context

In-place amendment loses the audit trail — both adversarial reviewers (Remy, SpecPurist) called out that ADR-0007 and ADR-0008 were not refined but reversed (content removed, not edited), and an in-place rewrite would erase the historical reasoning. Status-flip-only (no new ADR) is the minimum but leaves no new prose explaining the reversal rationale; future readers would see "Superseded" with no pointer to where to read why. The Nygard/MADR convention used implicitly by the existing nine ADRs is "one ADR per decision," and reversing a decision is itself a decision — it warrants its own ADR. Symmetric headers (`Superseded-by:` on the old + `Supersedes:` on the new) duplicate the relationship in two places; consolidating the cross-link in the new ADR's `Supersedes:` header and putting the back-pointer inline in the old ADR's `Status:` value (`Superseded by ADR-0010`) gives one canonical link from the new file and one machine-grep-able status string on the old file, with no template-wide header-key churn.

## Decision

Chose **Add a new `Supersedes:` header line to ADR-0010 and ADR-0011 (between `Feature:` and the blank line), and flip ADR-0007 and ADR-0008 to `Status: Superseded by ADR-NNNN` (inline value, not a new header key on the older ADRs).** over **In-place amendment to ADR-0007/ADR-0008 (no new ADR; rewrite Decision and Consequences); only flip the Status on the old ADRs with no new ADR; add a `Superseded-by:` header to the old ADRs and a `Supersedes:` header to the new ADRs (symmetric, two new header keys).**.

## Consequences

Two new ADR files are added (`docs/adr/0010-…md`, `docs/adr/0011-…md`) following the existing five-line header + `Context`/`Decision`/`Consequences` body shape, with one extra header line `Supersedes: ADR-NNNN`. Two existing ADRs are edited at one line each: `docs/adr/0007-…md:4` and `docs/adr/0008-…md:4` change from `Status: Accepted` to `Status: Superseded by ADR-0010` and `Status: Superseded by ADR-0011` respectively. No other ADR template field is introduced. Future supersession follows this same pattern, which is now established by ADR-0010/0011. **This Disambiguation triggers ADR-0014 (proposed) — a meta-ADR that records the supersession convention itself, so the next reversal does not have to re-derive it.**
