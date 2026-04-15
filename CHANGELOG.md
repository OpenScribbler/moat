# MOAT Specification Changelog

All notable changes to the MOAT specification are documented in this file.

## [Unreleased]

### Fixed

- **`moat-spec.md` non-interactive client subsection** — the forward-reference to a deferred pre-approval mechanism now links to [`ROADMAP.md#non-interactive-trust-onboarding`](ROADMAP.md#non-interactive-trust-onboarding) (a new Deferred item) instead of an internal tracking ID. Editorial clarification; no normative change.

## [0.6.0] — 2026-04-14 (Draft)

Breaking release: content type rename, field renames, new required lockfile fields, staleness model redesign. Publishers and conforming-client implementers will need updates.

### Added

- **Version Transition section** — content hash checked before `_version`; 6-month grace period for schema version bumps
- **Non-interactive client behavior** — normative exit-non-zero table for TOFU, signing profile change, revocation, staleness in CI/CD environments
- **Undiscovered content detection** — Publisher Action MUST warn about content-like directories not covered by discovery
- **Revocation archival** — 180-day recommended retention, lockfile authority for pruned revocations, tombstone rule via `revocation-tombstones.json`
- **Namespace uniqueness** — `(name, type)` compound key MUST be unique within a manifest; Registry Action rejects duplicates
- **TUF staleness model** — registry-set `expires` field with 72-hour client default; replaces fixed 24-hour threshold
- **`fetched_at` lockfile field** — per-registry tracking for staleness enforcement, with upgrade path for pre-staleness lockfiles
- **Security Considerations section** — 96-hour worst-case revocation propagation, replay attack scope, TOFU attack surface, lockfile integrity precision note
- **Crawl optimization guidance** — informative section in Registry Action for Rekor entry reuse with OIDC identity check
- **Manifest size guidance** — informative section on ETag caching, jitter, and deferred delta-sync
- **`test_normalization.py`** — integration tests TV-17 through TV-22 for BOM stripping, CRLF normalization, binary classification, chunk boundary, lone CR
- **Cross-validation** — `generate_test_vectors.py` now validates against `moat_hash.py` on every run
- **VERSION file + `scripts/bump-version.py`** — single-source version propagation to all spec files

### Changed

- **`subagent` renamed to `agent`** — content type, canonical directory `agents/`, all spec files updated
- **`expires_at` renamed to `expires`** — manifest field table updated
- **Hash mismatch is normative downgrade** — Registry Action MUST downgrade from Dual-Attested to Signed on hash mismatch; `attestation_hash_mismatch` client behavior defined
- **Test vectors are normative authority** — `generate_test_vectors.py` declared normative; `moat_hash.py` demoted to informative reference
- **`generate_test_vectors.py` aligned to sha256sum format** — manifest format changed from `{path}\x00{hash}\n` to `{hash}  {path}\n` matching `moat_hash.py`
- **TV-09, TV-10 rewritten as error cases** — reject-all symlink policy; both now `must_error=True`
- **Staleness bullet updated** — Conforming Clients section now references `fetched_at + 72 hours` instead of configurable 24-hour threshold

### Removed

- **Meta hash code** — `meta_hash()`, `vector_meta_hash()`, `vector_meta_hash_derived()` removed from `generate_test_vectors.py` (vestigial v0.3.0)
- **`import json`** — unused after meta hash removal

---

## [0.5.3] — 2026-04-11 (Draft)

Removed redundant `## Publisher Action` and `## moat-verify` top-level summary sections. Both were duplicating content already present in `## Conforming specs` (descriptions and links) and the respective sub-specs (operational details). No normative content removed.

### Removed

- `## Publisher Action` — summary and link duplicated by `## Conforming specs`; operational details belong in `specs/publisher-action.md`
- `## moat-verify` — summary and link duplicated by `## Conforming specs`; usage flags, verification flow, and output requirements belong in `specs/moat-verify.md`

---

## [0.5.2] — 2026-04-11 (Draft)

Structural reorganization: move Attestation Payload out of Trust Model and into Data Formats. No normative content changed.

### Changed

- `moat-spec.md` §Trust Model — `### Signature Envelope`: per-item attestation payload block (canonical format, serialization rules, Python canonical form, test vector, field notes) extracted to new `### Attestation Payload` section in Data Formats. Replaced with a short summary paragraph and cross-reference. Trust Model section now contains only policy and procedure content, consistent with all other Trust Model subsections.
- `moat-spec.md` §Data Formats — added `### Attestation Payload` section with the canonical payload format, serialization rules, Python canonical form, test vector, and field notes for `rekor_log_index`, `_version`, and the publisher/registry shared-format rationale.

---

## [0.5.1] — 2026-04-10

Spec fixes and implementation hardening following end-to-end testing of the Publisher Action and Registry Action workflows. Editorial cleanup: broken links repaired, missing cross-references added.

### Added

- `moat-attestation.json` — `publisher_workflow_ref` (OPTIONAL): workflow path and ref recorded by the Publisher Action from `GITHUB_WORKFLOW_REF` at signing time (e.g., `.github/workflows/moat.yml@refs/heads/main`). Registry Actions read this field to derive the expected OIDC subject for publisher Rekor verification — no hardcoded filename assumption required. Absent means the attestation predates this field; conforming registries MUST fall back to `.github/workflows/moat.yml@refs/heads/main`.
- `moat-spec.md` §Per-item attestation payload: clarified that the Publisher Action uses the same canonical payload format (`{"_version":1,"content_hash":"sha256:<hex>"}`) as the Registry Action. Both are distinguished by OIDC subject in the Rekor certificate, not by payload content. Added rationale: the canonical format is required because `hashedrekord` Rekor entries store only the payload hash, so verifiers must reconstruct exact payload bytes independently.
- `specs/publisher-action.md`: `publisher_workflow_ref` field documentation; updated step 5 of "What It Does" to explain that workflow path is auto-recorded in `moat-attestation.json`; updated "Workflow filename and branch" section to reflect configurable filename with `moat.yml` as the recommended default.
- `specs/registry-action.md`: Updated publisher Rekor verification step 4 to describe reading `publisher_workflow_ref` from `moat-attestation.json` with fallback to `moat.yml` default.

### Fixed

- Publisher Action: was signing a richer payload (`_type`, `item_name`, `source_ref`, `attested_at`) that the Registry Action cannot verify at crawl time because `source_ref` and `attested_at` are unknowable when crawling. Fixed to sign the same canonical payload as the Registry Action. Both publisher-action.md and the reference workflow (`reference/moat.yml`) updated.
- Registry Action: `git show origin/moat-attestation:moat-attestation.json` fails in a shallow clone because `git fetch origin moat-attestation` updates `FETCH_HEAD` but does not set up the remote-tracking ref. Fixed to use `git show FETCH_HEAD:moat-attestation.json` immediately after the fetch.
- Publisher Action and Registry Action reference workflows: hardcoded `moat.yml` workflow filename in OIDC subject verification replaced with `publisher_workflow_ref` read from `moat-attestation.json`.
- `moat-spec.md`: OWASP alignment links updated from `docs/guides/owasp-alignment.md` to `docs/owasp-alignment.md` following file move (two locations: header and OWASP Alignment section).
- `moat-spec.md`: `specs/registry-action.md` added to Sub-specs header; was missing despite the spec existing since v0.5.0.
- `moat-spec.md`: Reference implementation cross-reference listings (under Conforming Specs and What the Spec Defines) updated to include `moat_verify.py`, `moat.yml`, and `moat-registry.yml`; only `moat_hash.py` and `generate_test_vectors.py` were listed previously.
- `README.md`: Added Reference Implementations and Guides sections; `docs/guides/cosign-offline.md` was missing entirely; guides were previously only listed as inline links in the repo structure table.

## [0.5.0] — 2026-04-10

Registry Action specification and manifest format additions. Introduces the normative mechanism for producing a MOAT registry manifest and adds four new manifest fields. Standardizes all timestamp formats to RFC 3339 UTC.

### Added

- `specs/registry-action.md` — Registry Action specification: the normative GitHub Actions workflow for producing MOAT registry manifests. Covers `registry.yml` config format, trust tier determination procedure (including publisher Rekor verification algorithm), per-item signing, revocation handling, self-publishing mechanics, and private repository guard.
- Actors section: informative note on role combinations — publisher-only, registry-operator-only, self-publishing (publisher + registry operator), and closed-ecosystem (publisher + registry operator + client).
- Conforming Specs section: Registry Action entry.
- Manifest format — `expires_at` (OPTIONAL): RFC 3339 UTC timestamp; conforming clients MUST reject manifests past their declared expiry when the field is present. Making `expires_at` REQUIRED for all registries remains deferred pending infrastructure maturity.
- Manifest format — `self_published` (OPTIONAL): `true` when the registry operator and publisher are the same entity. Conforming clients SHOULD surface this to End Users.
- Manifest format — `revocations[].source` (OPTIONAL): `"registry"` or `"publisher"`; absent defaults to `"registry"` (fail-closed). Machine-readable discriminant for the hard-block vs. warning behavioral distinction.
- Manifest format — `content[].attestation_hash_mismatch` (OPTIONAL): `true` when the registry's computed hash differed from the publisher's `moat-attestation.json` hash. Surfaces publisher attestation/content divergence to clients.
- Revocation section: reason code meanings table — describes what `malicious`, `compromised`, `deprecated`, and `policy_violation` mean in practice and the urgency signal each carries for End User display.

### Changed

- Signing identity trust model: manual-add registry path now explicitly named as trust-on-first-use (TOFU). Added normative requirement that conforming clients MUST store the accepted `registry_signing_profile` and apply re-approval on all subsequent fetches.
- Freshness section: `expires_at` moved from "deferred to a future version" to an opt-in OPTIONAL field with normative enforcement semantics. Deferral is now specifically scoped to making the field REQUIRED.
- All protocol timestamp fields standardized to RFC 3339 UTC (previously inconsistent — some fields used "ISO 8601 UTC", others used "RFC 3339 UTC"). Fields affected: manifest `updated_at`, `attested_at`, `expires_at`, registry index `updated_at`, `scan_status.scanned_at`, publisher-action `attested_at`.
- Publisher Action Conforming Specs entry: completed truncated sentence ("MUST be able to consume attestations produced by the Publisher Action").
- Actor count: corrected "six distinct actors" to "five distinct actors".

## [0.4.0] — 2026-04-06 (Draft)

Complete architectural rewrite. MOAT is redefined from a per-item sidecar metadata format (`meta.yaml`) to a registry distribution protocol. The v0.3.0 spec is archived; this version is not backwards-compatible with any prior version.

### Changed

- **Core architecture:** The registry manifest replaces `meta.yaml` as the core artifact. Registries produce provenance; publishers do nothing by default.
- **Trust unit:** Shifted from per-item creator signing to registry-level signing. The registry is now the trust anchor conforming clients verify.
- **Content hashing algorithm:** JCS canonical JSON + meta_hash replaced by dirhash-style algorithm — sort → hash → concatenate → hash. Defined by normative reference implementation (`moat_hash.py`).
- **Signing model:** Registry signs the manifest; publisher co-signing is optional (produces Dual-Attested tier). SSH signing profile removed entirely.
- **Identity semantics:** Version is now an optional display label; content hash is the normative identity. `attested_at` replaces `published_at` for freshness semantics.
- **Name fields:** `name` is now an ASCII machine identifier; `display_name` (optional) is the UTF-8 human label. Prior 128-character Unicode `name` limit dropped.
- **Source field:** `source_repo` (git-specific format) replaced by `source_uri` (any valid URI).
- **Name expansion:** "Metadata for Origin, Authorship, and Trust" → "Model for Origin Attestation and Trust" (MOAT acronym preserved).

### Added

- Registry manifest format — signed JSON document: registry identity, `registry_signing_profile`, `content` array with per-item hashes, `revocations` array.
- Three-tier trust model: `Dual-Attested` (registry + independent publisher Rekor entry), `Signed` (registry + Rekor), `Unsigned`.
- Publisher Action — optional GitHub Actions workflow for source-repo co-signing; produces Dual-Attested content with no key management.
- Registry index format — discovery mechanism for listing known registries.
- Content type taxonomy — `skill`, `subagent`, `rules`, `command`; canonical category directories; two-tier discovery (`moat.yml` override).
- Revocation mechanism — `revocations` array in manifest with reason codes.
- Fork and lineage model — `derived_from` field for forks and adaptations.
- Lockfile concept — conforming client artifact for recording installed content hashes.
- `reference/moat_hash.py` — Python reference implementation of the content hashing algorithm.

### Removed

- `meta.yaml` per-item sidecar format (archived as `moat-spec-v0.3.0-archived.md`).
- JCS canonical JSON / meta_hash algorithm and YAML-to-JSON type mapping.
- `generated_by` field — unverifiable, ages poorly.
- `source_commit` field — git-specific, redundant with content hash.
- 64-character hash length limit — replaced by `<algorithm>:<hex>` prefixed format with no length constraint.

---

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
