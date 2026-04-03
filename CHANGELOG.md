# MOAT Specification Changelog

All notable changes to the MOAT specification are documented in this file.

## [0.2.0] — 2026-04-03

Source binding, delegated publishing, and naming. Renamed from ACP (Agent Content Provenance) to MOAT (Metadata for Origin, Authorship, and Trust). Domain separator updated from `ACP-V1:` to `MOAT-V1:`.

### Added

- Source binding verification (Section 9.2 steps 6–7) — normative `source_repo` binding via Fulcio OID extension `1.3.6.1.4.1.57264.1.12`
- `publisher_identity` field (Section 6.3.15) — REQUIRED when signing identity differs from `source_repo` owner
- `repository_owner_id` field (Section 6.3.16) — RECOMMENDED numeric platform identifier for account resurrection protection
- `sigstore_trust_root` field (Section 6.3.17) — OPTIONAL TUF root reference for enterprise/private Sigstore deployments
- First-publish trust (TOFU) semantics (Section 11.19)
- Source binding residual risks (Section 11.17) — repo takeover, transfer, org multi-committer, workflow manipulation, self-hosted OIDC trust
- Version rollback considerations (Section 11.18)
- Appendix D — Provider OIDC certificate extension values, enterprise self-hosted Sigstore, sigstore-a2a related work
- TV-MH4 test vector for `publisher_identity` and `repository_owner_id` in meta hash computation

### Changed

- `publisher_identity` and `repository_owner_id` added to Section 8.1 hashed fields allowlist
- Section 8.2 type mapping table updated with new fields
- Section 6.4 distribution scope table updated with new field requirements
- Appendix C Forgejo entry corrected — cannot participate in Sigstore keyless signing
- Section 9.2 Forgejo removed from supported platforms list
- Section 9.2 step 5: identity verification demoted from MUST to SHOULD; strict consumers MUST document their algorithm
- Section 9.2 step 4: added Fulcio certificate expiry guidance (verify against Rekor timestamp, not current time)

### Fixed

- `publisher_identity` (Section 6.3.15): added normative text that field is self-reported, MUST NOT be treated as verified identity
- `sigstore_trust_root` (Section 6.3.17): added normative verification behavior and integrity warning
- TV-MH4: fixed `source_repo` to 3-segment path, recomputed hash
- Section 6.3.15: moved "differs" definition from informative Note to normative text body
- Section 11.18: downgraded latest-version manifest recommendation to non-normative
- Section 11.19 + 5.3: demoted TOFU MUST to SHOULD; added first-publish policy requirement to registry conformance
- Section 9.2 step 6: added normative behavior when Source Repository URI OID is absent from certificate
- Section 5.2.2: added strict consumer source binding requirement

## [0.1.0] — 2026-04-02

Initial draft release.

### Added

- Sidecar format (`meta.yaml`) with 12 metadata fields across 3 distribution scopes (local, team, public)
- Content hash algorithm (Section 7) — directory tree hashing with SHA-256, NFC path normalization, symlink resolution
- Meta hash algorithm (Section 8) — explicit field allowlist per `meta_version`, JCS canonicalization, normative YAML-to-JSON type mapping
- Cryptographic signatures (Section 9) — Sigstore and SSH methods with `MOAT-V1:` domain separator
- Lineage model (Section 10) — `derived_from` with fork/convert/adapt relations and version reset
- Conformance classes (Section 5) — publishers, consumers (strict/permissive), and registries
- Security considerations (Section 11) — 16 subsections covering trust model through ecosystem security
- 22 test vectors (Appendix B) — content hash, meta hash, signing input, error cases, VCS exclusion
- VCS directory exclusions (`.git/`, `.svn/`, `_svn/`, `.hg/`, `CVS/`)
- Implementation note on CRLF/cross-platform verification (Section 7.6)
