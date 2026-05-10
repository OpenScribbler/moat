# 0003. Revocation framing — Pre/post-materialization vs Resolve/install/activation trichotomy

Date: 2026-05-09
Status: Accepted
Feature: npm-distribution-spec

## Context

MOAT's protocol boundary stops at the install step — once content is on disk, MOAT is done (CLAUDE.md "What 'Conforming Client' Means"). A trichotomy that names "activation" as a normative phase implicitly extends MOAT into AI Agent Runtime territory: it suggests there is a MUST to enforce at activation time, which the protocol cannot enforce because activation happens inside Claude Code / Cursor / Windsurf and friends, not inside a Conforming Client. A pre/post-materialization split places the boundary exactly where the protocol's authority ends. Pre-materialization (resolve, fetch, unpack) is where a Conforming Client MUST refuse a revoked hash; post-materialization (file exists on disk, AI Agent Runtime may or may not load it) is where the protocol MAY observe but MUST NOT mandate. The trichotomy also fails the enforcement test: there is no enforcement mechanism a Conforming Client can apply at "activation" because the Conforming Client has finished its job by then.

## Decision

Chose **Pre-materialization vs post-materialization, with MUSTs anchored at the materialization boundary** over **A three-phase trichotomy (resolve / install / activation) with separate normative obligations at each phase**.

## Consequences

The sub-spec's normative MUSTs land cleanly: pre-materialization checks (resolve-time logging when a revoked hash is skipped per D6, install-time hard-block per the lockfile `revoked_hashes` model) carry MUST/MUST NOT; post-materialization is `(informative)` and explicitly says "out of MOAT's protocol boundary." This matches the existing core spec — `moat-spec.md:635` ("MUST be added to revoked_hashes") and `moat-spec.md:663` ("hard-block continues") both fire at install time, not at runtime. Implementers writing an npm-aware Conforming Client get a single clear question to answer ("am I about to materialize this hash on disk?") rather than three overlapping ones. The `MOAT_ALLOW_REVOKED` escape hatch (Q2 below) lives entirely in the pre-materialization side because that is where the block is enforced. AI Agent Runtimes that want to apply runtime gating MAY do so as a separate concern, and the sub-spec is silent about how — that is correct, because that is a different protocol than MOAT.
