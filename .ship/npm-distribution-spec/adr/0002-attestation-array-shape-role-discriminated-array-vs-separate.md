# 0002. Attestation array shape — Role-discriminated array vs Separate slots vs Provenance enum

Date: 2026-05-09
Status: Proposed
Feature: npm-distribution-spec

## Context

Backfill is a load-bearing concept of the npm sub-spec — a Registry can attest an existing npm package without Publisher cooperation, and a Publisher can attest without a Registry having indexed them yet. Four states must be representable: publisher-only, registry-only, both, neither. Separate slots represent both-and-neither cleanly but force an asymmetric schema (the consumer reads two different field names for two attestations of the same canonical payload); they also make it awkward to ever add a third role. A provenance enum compresses the four states into one tag but loses the ability to carry both attestations side-by-side and forces every reader to branch on the enum before they can find the data. A role-discriminated array is symmetric (both entries carry the same shape modulo the discriminator), grows naturally if a third role is ever needed, and represents all four states with the array's natural cardinality (length 0 / 1 / 2). It also matches the Registry Manifest's existing precedent of using arrays with role-bearing fields — `revocations[].source: "registry" | "publisher"` (`moat-spec.md:792-796`) and the per-item Rekor-entry-vs-signing_profile pairing (`moat-spec.md:786, 790`).

## Decision

Chose **Role-discriminated `attestations: [...]` array (each entry carries `role: "publisher" | "registry"`)** over **Separate top-level slots (`moat.publisher_attestation`, `moat.registry_attestation`); a `provenance: { type: "publisher" | "registry" | "both" | "neither" }` enum with mode-specific payload**.

## Consequences

A Conforming Client reading the `package.json` `moat` block walks `attestations[]` and, for each entry, dispatches on `role`. A length-zero array represents the "neither" state explicitly — the Publisher has reserved the `moat` block (declaring intent to participate) but no attestation is yet present; this is a Day-One legitimate state, not an error. Tooling that wants to find "the publisher attestation" performs a single-pass filter rather than a field lookup. The schema MUST forbid duplicate roles within one array (two entries with `role: "publisher"` is malformed) — the analog of the manifest's `(name, type)` uniqueness constraint. Adding a future role (e.g., a third-party scanner) is a schema-additive change rather than a structural rewrite. A Publisher attestation in this array points at the same canonical Attestation Payload signed by the Publisher Action — the npm sub-spec MUST NOT introduce a second canonical payload format.
