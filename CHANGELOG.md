# MOAT Specification Changelog

All notable changes to the MOAT specification are documented in this file.

## [0.3.0] — 2026-04-04

Security hardening release based on 5-agent adversarial review (31 findings, 29 revision items). Elevates multiple informative recommendations to normative requirements and adds 7 new security considerations.

### Added

- Section 7.3 step 1: regular-file-only enumeration — FIFOs, device files, sockets, and block devices MUST be excluded
- Section 7.3 step 1: hard link detection guidance — SHOULD verify no file has link count > 1 with external links
- Section 8.2: YAML merge key (`<<`) prohibition — MUST NOT be used in `meta.yaml`
- Section 8.2: YAML timestamp coercion prohibition — MUST NOT auto-parse unquoted timestamps
- Section 8.2: SHOULD use YAML 1.2 parser; expanded boolean coercion MUST NOT list (`yes`, `no`, `on`, `off`, `y`, `n`, case-insensitive)
- Section 8.2: SHOULD set alias expansion limits (billion laughs mitigation)
- Section 8.2: SHOULD reject multi-document YAML
- Section 9.1: future `meta_version` signing input formats MUST use incompatible prefix
- Section 9.2 step 3: Rekor entry content verification — MUST verify `data.hash.value`, `signature.content`, and `signature.publicKey.content` match the MOAT artifact (ref: CVE-2026-22703)
- Section 9.2 step 6: `repository_owner_id` verification against OID `1.3.6.1.4.1.57264.1.17`
- Section 11.14: fd-based TOCTOU mitigation guidance (ref: CVE-2024-23651, CVE-2024-21626)
- Section 11.17: verification pipeline composition guidance (fail-closed) and publisher tooling validation
- Section 11.20: Trust Root Substitution — full identity substitution attack via `sigstore_trust_root` + signature replacement
- Section 11.21: Hard Link Integrity Bypass
- Section 11.22: FIFO and Special File Denial of Service
- Section 11.23: YAML Parser Differential Risks
- Section 11.24: Content Transparency and Registry-Served Content Divergence
- Section 11.25: Trust Laundering via False Derivation Claims
- Section 11.26: OIDC Token Exfiltration and Reusable Workflow Confusion
- Appendix D: Build Signer URI (OID `.8`), Build Signer Digest (`.9`), Runner Environment (`.10`)
- TV-YAML-01: YAML 1.1/1.2 boolean coercion divergence test vector
- TV-YAML-02: Unquoted timestamp handling test vector

### Changed

- Section 5.3.16: `repository_owner_id` elevated from RECOMMENDED to REQUIRED for Sigstore-signed content
- Section 5.3.17: `sigstore_trust_root` reframed as "discovery hint" — MUST NOT be used as sole basis for trust
- Section 9.2 step 3: Rekor inclusion proof verification elevated from SHOULD to MUST
- Section 9.2 step 7: `publisher_identity` MUST be displayed alongside verified signing identity; MUST NOT be presented as verified
- Section 9.2 step 8: trust root pinning strengthened — public-good Sigstore is RECOMMENDED default; all others require explicit configuration
- Section 11.10: `type` field MUST NOT be used for access control without independent content analysis
- Section 11.11: added SSL-stripping analogy; registries SHOULD maintain per-publisher signing expectations
- Section 11.16: Rekor verification elevated to MUST for both inclusion proofs and entry content matching
- Section 11.18: version rollback — "encouraged" elevated to SHOULD for signed latest-version manifests
- Section 11.19: TOFU — SHOULD elevated to MUST for first-publish claim treatment; added challenge-response authorization guidance

## [0.2.1] — 2026-04-03

Readability improvements based on reviewer feedback.

### Changed

- Reordered sections: meta.yaml format (Section 5) now precedes conformance (Section 6)
- Simplified Document Status paragraph — removed implementation details about test vector generation
- Removed all references to specific software implementations
- Replaced branded examples with generic ones in prose and TV-MH4 (recomputed meta_hash)

### Added

- Rationale block in Section 5.1 explaining why identity and descriptive metadata are combined in a single sidecar

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
