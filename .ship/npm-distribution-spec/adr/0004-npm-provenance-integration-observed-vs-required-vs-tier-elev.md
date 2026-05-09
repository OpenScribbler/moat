# 0004. npm provenance integration — Observed vs Required vs Tier-elevating

Date: 2026-05-09
Status: Proposed
Feature: npm-distribution-spec

## Context

npm provenance and MOAT solve adjacent but distinct problems. npm provenance attests **build integrity** — that the artifact at `registry.npmjs.org` was produced by a particular CI workflow from a particular source commit. MOAT attests **content review** — that an attested party (Publisher and/or Registry) signed off on the canonical attestation payload `{"_version":1,"content_hash":"sha256:..."}`. Treating npm provenance as a MOAT requirement would couple MOAT to a particular registry's build-integrity feature, breaking the transport-agnostic core / transport-specific extension split this very directory move is meant to clarify. Treating npm provenance as tier-elevating would invent a fourth Trust Tier (or worse, a hidden modifier on existing tiers) that the lexicon and core spec do not authorize, fragmenting the cross-channel meaning of "Dual-Attested" and "Signed". Observing it as corroborating evidence (the sub-spec MAY recommend that Conforming Clients surface npm provenance presence to End Users alongside the Trust Tier label) gives users a richer picture without polluting the protocol semantics.

## Decision

Chose **Observed-when-present, recommended-but-not-required, orthogonal to MOAT trust tiers (D4)** over **Required (MUST be present and valid for the Verified label); Tier-elevating (presence promotes a Signed item toward Dual-Attested or a higher npm-only tier)**.

## Consequences

The Trust Tier values published in the Registry Manifest (`Dual-Attested`, `Signed`, `Unsigned`) carry the same meaning whether the Distribution Channel is GitHub or npm. An npm package with valid npm provenance and no MOAT attestation is `Unsigned` from MOAT's perspective — it has the npm-provenance corroborating signal but no content-review attestation. An npm package with a Registry MOAT attestation but no npm provenance is `Signed` and installable; the absence of npm provenance does not gate it. Conforming Clients MAY expose npm provenance presence in their UI as a separate row from the Trust Tier; they MUST NOT use it to compute or override the Trust Tier. Future registry transports (PyPI, Cargo) inherit this same orthogonality principle: build-integrity primitives in those ecosystems are observed-when-present, not required, not tier-elevating.
