# 0001. Hash domain — Tarball Content Directory vs Source-Repo Content Directory vs Dual

Date: 2026-05-09
Status: Proposed
Feature: npm-distribution-spec

## Context

The npm Distribution Channel materializes content from a tarball, not from a source repo. A Conforming Client only ever has the tarball at install time — it does not (and the protocol does not require it to) clone the source repo. Hashing the source repo would force every install to perform an out-of-band fetch the npm ecosystem does not perform, fail copy-survival (a tarball copied to a different repo cannot reproduce the source-repo hash), and fail the day-one test (existing npm packages have no published source-repo hash). Dual hashes double the schema surface and the ways a Publisher can produce mismatching attestations without buying meaningful trust beyond what the lone tarball hash already provides — the source repo's contribution is captured by `source_uri` plus the Publisher Rekor entry's signing identity, which already binds the tarball back to its origin. The Tarball Content Directory hash is also the only domain a backfill-only Registry can compute: it has the tarball, it does not have privileged access to the Publisher's source layout.

## Decision

Chose **Tarball Content Directory (`reference/moat_hash.py:166-198` applied to the unpacked `.tgz`)** over **Source-Repo Content Directory (the directory at `source_uri`); Dual hashes (both source-repo and tarball recorded)**.

## Consequences

A Publisher whose source-repo content directory is identical byte-for-byte to the tarball Content Directory (after npm's `files`/`.npmignore` filtering) will see the same Content Hash on both channels, which is the intended cross-channel identity. A Publisher whose npm build step transforms files (TypeScript compilation, bundling) will produce a different Content Hash on npm than in the source repo, and the npm sub-spec MUST acknowledge this — the tarball hash is the npm-channel identity, distinct from the source-channel identity. The hashing algorithm itself (the `reference/moat_hash.py` walk, NFC normalization, exclusion list) is unchanged; only the input directory differs. Tombstones and `revoked_hashes` keyed by Content Hash continue to work because the hash domain is a property of the input bytes, not of the channel — once a tarball hash is revoked, republishing identical bytes under a new version yields the same hash and remains blocked.
