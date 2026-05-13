# 0013. Where the new `distribution_uri` field lives in the package.json moat-block schema

Date: 2026-05-12
Status: Accepted
Feature: npm-distribution-spec

## Context

An npm Distribution Tarball is exactly one tarball with exactly one canonical npm-tarball URL — there is no `content[]` array inside a `package.json` moat-block to host a per-item field, and even if a single tarball ships multiple content items (allowed by the channel), they all share the same tarball URL. Top-level placement matches the artifact's one-tarball-one-URL identity. Nesting under `publisherSigning` would entangle a distribution-channel field with a signing-identity block, violating the lexicon's separation of **Distribution Channel** (`lexicon.md:83`) from **Signing Identity** (`lexicon.md:69`). Top-level placement also matches how the Registry-side analog appears in the Registry Manifest under `moat-spec.md` §Registry Manifest — the npm sub-spec's job is to populate the inverse half (the publisher's declared tarball URL), not to override the registry's schema.

## Decision

Chose **Top-level `moat.distribution_uri` (sibling of `moat.tarballContentRoot`, `moat.attestations`, `moat.publisherSigning` in the schema table at `specs/npm-distribution.md:88–98`).** over **`moat.content[].distribution_uri` (per Content Item, mirroring `content[].source_uri` in the core Registry Manifest at `moat-spec.md:783`); `moat.publisherSigning.distribution_uri` (nested under the publisher block).**.

## Consequences

A new row is added to the schema table at `specs/npm-distribution.md:88–98`. The row is REQUIRED for Publisher-cooperative items (the Publisher knows their own tarball URL at publish time), and the Registry-side `distribution_uri` in the Manifest entry is what a Conforming Client reads when consuming. `lexicon.md` may need a new glossary entry under §Distribution Channels naming `distribution_uri` and disambiguating it from `source_uri` (the lexicon's only existing tarball-URL prose is the overload note at `:62`). Worked-example JSON at `specs/npm-distribution.md:117–122` gains one line. **This Disambiguation triggers ADR-0013 (proposed) to record the field's placement and the `source_uri` vs `distribution_uri` separation.**
