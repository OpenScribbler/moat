# 0005. Default Content Directory — Tarball root with exclusion vs Publisher-required field vs Heuristic search

Date: 2026-05-09
Status: Accepted
Feature: npm-distribution-spec

## Context

The day-one test (`CLAUDE.md:121`) is the deciding lens. On day one, thousands of npm packages exist with no `moat` block. A Publisher-required field means backfill is impossible without Publisher cooperation — every backfilled package needs a Publisher to land a `moat.tarballContentRoot` field, which kills the backfill goal stated in the original ticket ("Sub-spec defines a backfill path so registries can attest pre-existing npm packages without publisher cooperation"). A heuristic search introduces ecosystem-wide ambiguity: two Conforming Clients with different probe orders can compute different Content Hashes for the same tarball, breaking the copy-survival test (`CLAUDE.md:123`) and violating the protocol's hash-as-identity invariant. A fixed default — tarball root with a single named exclusion — is the only choice that lets a Registry compute a canonical hash from the published tarball alone, with no Publisher cooperation, and that no two Conforming Clients can disagree about. The exclusion of `package.json` is forced by C-6a's identity-disclosure-in-package.json design: if `package.json` were inside the canonical hash, mutating it (to write the Rekor log index after signing) would change the hash and invalidate the signature — the chicken-and-egg the C-6 family was designed to break.

## Decision

Chose **Tarball root as default, with a fixed single-file exclusion list (`package.json`) when `moat.tarballContentRoot` is absent (C-1 + C-6b)** over **Publisher-required `moat.tarballContentRoot` field with no default (Round 1's effective behavior — a Publisher had to set the field to participate); Heuristic search (Conforming Client probes for common layouts: `src/`, `dist/`, `lib/`, `skill/`, falling back to root)**.

## Consequences

Backfill becomes a real capability — a Registry Operator can run a backfill workflow over arbitrary npm packages and produce canonical hashes that any other Conforming Client can independently reproduce by fetching the same tarball. Publishers who want to scope the canonical hash to a subdirectory (e.g., `src/`) set `moat.tarballContentRoot: "src"` and the exclusion list does not apply (because the subdirectory case has no chicken-and-egg — `package.json` lives at tarball root, outside any subdirectory). The default mode's exclusion list is exactly one entry; the spec MUST forbid future expansion of this list without a sub-spec version bump (extending the exclusion list silently would change the canonical hash for every default-mode package). The npm Registry's tarball SHA-512 covers `package.json` independently, so excluding it from the MOAT canonical hash does not reduce the consumer's ability to detect tarball-level tampering — it only narrows MOAT's normative scope to the bytes a Publisher and Registry can both control identically.
