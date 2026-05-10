# 0009. Hash exclusion list — Single fixed file in default mode vs No exclusions vs Configurable exclusion list

Date: 2026-05-09
Status: Accepted
Feature: npm-distribution-spec

## Context

The chicken-and-egg between `publisherSigning.rekorLogIndex` and the canonical hash is the binding constraint. Without an exclusion, writing the log index back into `package.json` after Sigstore signing changes the canonical hash, invalidating the signature — the C-6c reference workflow's two-pack design becomes impossible without the exclusion. "No exclusions" is rejected on this ground alone. A configurable exclusion list (the second alternative) opens a far larger attack surface: a malicious Publisher could set `moat.hashExclude: ["malicious-payload.js"]` and have the canonical hash cover only the benign files, attesting bytes the Conforming Client never executes. The exclusion list itself would have to live inside `package.json` and would also need to be inside the canonical hash (otherwise it's the same chicken-and-egg again at one remove), which forces a circular schema. A fixed single-file exclusion ties exactly to the protocol's needs and admits no Publisher-driven expansion. The exclusion is forced to `package.json` specifically because that is the file the C-6c reference workflow mutates between the two `npm pack` calls — no other file in a normal npm package is npm-injected metadata that the Publisher both signs and then needs to mutate post-signing. The npm Registry's tarball SHA-512 covers `package.json` independently of MOAT (`specs/npm-distribution.md:21`), so a consumer who wants tarball-level integrity over `package.json` already has the npm primitive — MOAT does not lose meaningful security by excluding it. The subdirectory mode does not need the exclusion: when `moat.tarballContentRoot: "src"`, the canonical hash domain is `src/`'s contents, and `package.json` (at tarball root, outside `src/`) is outside the hash domain by construction.

## Decision

Chose **Default-mode-only exclusion of exactly one file (`package.json`); subdirectory mode applies no exclusions (C-6b)** over **No exclusions (default mode hashes the entire tarball root including `package.json`); Configurable exclusion list (Publisher declares `moat.hashExclude: ["package.json", ...]`)**.

## Consequences

The Round 2 sub-spec MUST state that the default-mode exclusion list contains exactly one entry (`package.json` at tarball root) and MUST forbid future Publisher-driven extension of this list without a sub-spec version bump. The subdirectory-mode rule "no exclusions apply" MUST be stated explicitly to prevent a Conforming Client from carrying the default-mode exclusion through into subdirectory mode. The exclusion targets `package.json` at tarball root only — a `package.json` file inside a subdirectory (e.g., `src/package.json` for a workspace member) is hashed normally in subdirectory mode and is not excluded in default mode either (the exclusion is path-anchored to the tarball root, mirroring `reference/moat_hash.py:60`'s root-level-only exclusion of `moat-attestation.json`). A new ADR (proposed 0007) is warranted because this exclusion rule is a normative, security-relevant constraint that will be referenced repeatedly by Conforming Client implementers and Registry Operators running backfill.
