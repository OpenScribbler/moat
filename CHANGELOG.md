# MOAT Specification Changelog

All notable changes to the MOAT specification are documented in this file.

## [Unreleased]

Breaking change: the cosign bundle format is now pinned to Sigstore protobuf bundle v0.3. Conforming Publisher Actions and Registry Actions MUST invoke `cosign sign-blob --new-bundle-format`. The legacy JSON bundle layout (top-level `base64Signature` / `cert` / `rekorBundle`) is no longer supported. Strict consumers (e.g., sigstore-go) reject legacy bundles, so any registry that emitted them is unverifiable by modern clients and MUST republish. New sub-spec: `specs/npm-distribution.md` defines how MOAT attestations travel via the npm Registry. The two GitHub-specific sub-specs have moved into `specs/github/` with no normative change.

### Added

- **`reference/moat-npm-publisher.yml` reference Publisher workflow added** — a canonical end-to-end GitHub Actions workflow that realizes the seven-step npm Publisher sequence (`npm pack` v1 → compute canonical Content Directory hash → sign canonical attestation payload with Sigstore keyless → capture Rekor log index → write `moat.publisherSigning` back into `package.json` → `npm pack` v2 → `npm publish`). The two-pack pattern demonstrates that the default Content Directory rule (root `package.json` excluded from the hash domain) makes Publisher signing identity disclosable inside `package.json` without invalidating the signature. Cited from `specs/npm-distribution.md` `## Reference Implementations`. Concurrent edits: `moat-spec.md` Sub-specs line gains `specs/npm-distribution.md`; `.claude/rules/changelog.md` example path swapped from `specs/publisher-action.md` to `specs/github/publisher-action.md` (post-reorg cleanup).
- **specs/npm-distribution.md** — new sub-spec at version 0.1.0 (Draft) defining the npm transport binding for MOAT. Specifies the Content Hash input domain (the unpacked tarball's Content Directory, named by `moat.contentDirectory`), the `package.json` `moat` block schema with a role-discriminated `attestations[]` array (`publisher` and `registry` entries signing the same Canonical Attestation Payload), pre-materialization revocation MUSTs anchored at the install boundary (lockfile-authoritative, structured resolve-time logging, per-hash `MOAT_ALLOW_REVOKED` operator override), Registry-side backfill semantics (same `registry_signing_profile`, no second profile field), and the orthogonality between npm provenance and the MOAT Trust Tier. Companion website mirror added at `website/src/content/docs/spec/npm-distribution.md` and Specification sidebar updated.

### Changed

- **`specs/npm-distribution.md` four-state (npm provenance × MOAT attestation) disagreement table added (informative)** — the `## npm Provenance` section gains a four-row table enumerating the observable states (both present, MOAT-only, provenance-only, neither) with the Conforming Client's recommended display rule and the resulting Trust Tier impact for each. The table reinforces the existing `Orthogonal to MOAT Trust Tier (normative — MUST)` rule by making each state's display behavior concrete: npm provenance is always surfaced as a separate observation, never folded into the Trust Tier computation. Informative addition only — the normative orthogonality rule is unchanged.
- **`specs/npm-distribution.md` Publisher signing identity disclosed via `publisherSigning` block (Draft-status breaking change)** — the Publisher's signing identity moves out of `moat.attestations[].bundle` (the v0.1.0 role-discriminated array shape) into a top-level `moat.publisherSigning` object with REQUIRED `issuer`, REQUIRED `subject`, and OPTIONAL `rekorLogIndex`. The Publisher's Sigstore bundle is no longer embedded in `package.json`; it lives in the Rekor transparency log, and `publisherSigning` is the metadata a Conforming Client uses to locate it. `moat.attestations[]` is now scoped to Registry attestations only. A new `## Publisher Verification (normative)` section enumerates the two verification paths: when `rekorLogIndex` is present the Client fetches the Rekor entry directly by index; when absent the Client queries Rekor by canonical Content Hash and filters by `{issuer, subject}`. In both paths the `{issuer, subject}` identity match is the trust anchor — `rekorLogIndex` alone is a hint, not a verification result. The v0.1.0 "duplicate role is malformed" rule is replaced by structural JSON schema enforcement (Publisher cardinality is now structural: `publisherSigning` is a single object). Sub-spec is Draft and has no adopters; no migration scaffolding is provided.
- **`specs/npm-distribution.md` materialization-boundary anchor sharpened (normative clarification)** — the Revocation at the Materialization Boundary intro is rephrased to anchor the rule at a precise point: before any byte of the tarball is written outside the package manager's content cache. The three operations a Conforming Client MAY refuse at (`resolve`, `fetch`, `unpack`) are named explicitly; the choice of sub-operation is implementation matter as long as no extracted bytes land outside the cache. An informative paragraph maps the rule onto `pacote`, Yarn Plug'n'Play, and the pnpm content-addressable store. Normative clarification only — the materialization MUSTs are unchanged in scope.
- **`specs/npm-distribution.md` MOAT_ALLOW_REVOKED Operator Override hardened (normative — MUST)** — promotes the v0.1.0 paragraph bullet to its own H2 section and fixes four normative MUSTs: process-scope read-once (the variable and its REQUIRED co-variable `MOAT_ALLOW_REVOKED_REASON` are read exactly once at process start; mid-process re-reads are non-conformant); REQUIRED `MOAT_ALLOW_REVOKED_REASON` co-variable with hard-fail enforcement (a non-empty reason string is a precondition; missing reason is a structured error, not a silent skip); per-entry encoding `<sha256-hex>:<RFC3339-timestamp>` (the colon delimiter is mandatory; entries without a timestamp are malformed and MUST be ignored — no permanent overrides); structured override-applied event with the field names `package`, `content_hash`, `reason`, `expires_at`. Expired entries are treated as if absent (no warning, no log) and global wildcards are not honored.
- **`specs/npm-distribution.md` `moat.contentDirectory` renamed to `moat.tarballContentRoot`** — the field-name rename realizes the lexicon's **Content Directory** concept inside the npm Distribution Channel: the lexicon term remains the source of truth, and `tarballContentRoot` names the tarball-relative subdirectory that maps to it. Renamed in the field table, JSON examples, and prose throughout the sub-spec. The field is now OPTIONAL (the default Content Directory rule applies when absent). The Description column for `moat.tarballContentRoot` cross-references the lexicon Content Directory entry rather than redefining the concept inline. `lexicon.md`'s Content Directory entry gains a one-line realization note pointing at `tarballContentRoot`. No migration scaffolding is provided; the sub-spec is Draft with zero adopters.
- **`specs/npm-distribution.md` Content Directory section (normative — MUST)** — defines the default Content Directory rule for npm-distributed Content Items: when `moat.tarballContentRoot` is absent from the published `package.json`, the canonical Content Directory is the unpacked tarball root with `package.json` excluded from the hash domain. The exclusion is path-anchored to the tarball root; nested `package.json` files at deeper paths MUST remain in the hash domain. Subdirectory mode (`moat.tarballContentRoot` set) applies no exclusions. The exclusion list is fixed at exactly one file; Publishers MUST NOT extend it via `package.json` metadata or any other mechanism. The default rule lets a Registry compute the canonical Content Hash for any published version by fetching the Distribution Tarball, with no Publisher cooperation required. Sub-spec version bumped to 0.2.0 (Draft).
- **Bundle format pinned to v0.3 (`moat-spec.md` §Signature Envelope)** — new normative MUST: all cosign signatures produced by conforming signers MUST be Sigstore protobuf bundle v0.3 (`mediaType: application/vnd.dev.sigstore.bundle.v0.3+json`). Conforming signers invoking `cosign sign-blob` MUST pass `--new-bundle-format`. The Rekor log identity is located at `verificationMaterial.tlogEntries[].logId.keyId` and the log index at `verificationMaterial.tlogEntries[].logIndex`. Conforming clients MAY refuse to parse legacy bundles.
- **Publisher Action signing step (`specs/github/publisher-action.md`)** — step 5 now requires `--new-bundle-format`; step 6 reflects v0.3 bundle parsing paths for `rekor_log_id` and `rekor_log_index`. Reference implementation (`reference/moat-publisher.yml`) updated accordingly.
- **Registry Action signing steps (`specs/github/registry-action.md`)** — steps 6 and 8 now require `--new-bundle-format` for both per-item canonical-payload signing and manifest signing. Reference implementation (`reference/moat-registry.yml`) updated accordingly.
- **specs/github/publisher-action.md** — moved from `specs/publisher-action.md` into the new `specs/github/` directory to make the transport-agnostic-core / transport-specific-extension split visible in the directory layout. Filename is unchanged; cross-references in `moat-spec.md`, README, RELEASING, guides, and the reference workflows updated to the new path — no normative change, content is byte-identical to the prior location.
- **specs/github/registry-action.md** — moved from `specs/registry-action.md` into the new `specs/github/` directory alongside the Publisher Action sub-spec. Filename is unchanged; cross-references updated — no normative change, content is byte-identical to the prior location.
- **`moat-verify` reference (`reference/moat_verify.py`)** — removed the legacy `.cert` (top-level base64-PEM) fallback in `_oidc_from_bundle`; v0.3 paths are the only supported sources for the signing certificate. `_build_bundle` (used to reconstruct a bundle from a Rekor entry for online `cosign verify-blob`) now emits `mediaType: application/vnd.dev.sigstore.bundle.v0.3+json` and uses the v0.3 `verificationMaterial.certificate` shape.

### Removed

- **Legacy cosign bundle support** — the legacy JSON bundle layout (top-level `base64Signature`, `cert`, `rekorBundle.Payload.{logID,logIndex}`) is no longer accepted by reference tooling and is not permitted for conforming signers. Registries serving legacy bundles at `{manifest_uri}.sigstore` will fail verification by strict clients.

## [0.7.1] — 2026-04-24 (Draft)

Editorial and dogfooding release. One new normative SHOULD (`workflow_run` self-bootstrap for the Registry Action); two sub-spec MINOR bumps consolidating v0.7.0 normative changes; website spec mirrors re-synced from canonical; this repo's live workflows hard-synced from `reference/` so the advertised reference is what actually runs here. No breaking changes.

### Added

- **`workflow_run` trigger as self-bootstrap pattern (`specs/registry-action.md`, `reference/moat-registry.yml`)** — when the registry repository is also a Publisher (self-publishing) or when the operator wants a compliant registry to bootstrap from two workflow files alone, the Registry Action SHOULD include a `workflow_run` trigger chaining this action after `moat-publisher.yml` completes. The `update-registry` job MUST then guard on `github.event.workflow_run.conclusion == 'success'` so the registry does not crawl after a failed publisher build. Reference implementation updated to include the chain by default.

### Changed

- **Sub-spec version bumps** — `specs/publisher-action.md` and `specs/registry-action.md` both bumped from 0.1.0 → 0.2.0 to reflect the v0.7.0 normative changes (`.moat/` reservation MUST, actionable-error-message SHOULD, OIDC legacy-path fallback removal) and this release's `workflow_run` SHOULD. `specs/moat-verify.md` stays at 0.1.0 — no normative changes. Reference implementation version strings (`reference/moat-publisher.yml`, `reference/moat-registry.yml`) bumped to v0.2.0 to match.
- **Live workflows re-synced from reference (`.github/workflows/moat-publisher.yml`, `.github/workflows/moat-registry.yml`)** — the repo's live workflows had drifted from `reference/` and were missing `agents`/`agent` category rename, tier-3 undiscovered-content detection, `TOOLING_DIRS` exclusion, tombstone logic, `get_existing_registry_state()`, `workflow_dispatch` inputs, and the new `workflow_run` trigger. Now byte-identical to `reference/`. No normative change — reference was already authoritative.

### Fixed

- **Website spec mirror drift (`website/src/content/docs/spec/core.md`, `website/src/content/docs/spec/registry-action.md`)** — both mirrors were stale against their canonical sources (228 and 32 lines short, respectively). Re-synced: core mirror now reflects the full v0.7.0 spec body including Trusted-Root Acquisition, Trust State Error Vocabulary, Version Transition, signing_profile v2 with repo-ID pinning, and Security Considerations. Registry-action mirror now includes Crawl Optimization and Manifest Size sections, the `(name, type)` uniqueness check, and the new workflow_run SHOULD. No normative change — editorial alignment with canonical specs.

---

## [0.7.0] — 2026-04-24 (Draft)

Two-track release: (1) filename and directory disambiguation for publisher and registry config files, and (2) normative hardening of signing-identity verification against repository rename attacks. No output-file format or wire-format changes. Publishers and registry operators migrate the rename in a single commit; see migration steps below. Clients that already pin `signing_profile` by Fulcio certificate extensions will pick up the rename-attack binding with no code changes.

### Changed

- **Config file paths — filename rename for disambiguation (`specs/publisher-action.md`, `specs/registry-action.md`, `moat-spec.md`)** — publisher tier-2 discovery config moves from `moat.yml` at repo root to `.moat/publisher.yml`; registry operator config moves from `registry.yml` at repo root to `.moat/registry.yml`; publisher workflow template renames from `.github/workflows/moat.yml` to `.github/workflows/moat-publisher.yml`. Output artifacts (`moat-attestation.json`, `registry.json`) and the Registry Action workflow filename (`.github/workflows/moat-registry.yml`) are unchanged. This is a hard cut — no dual-read, no grace period, no legacy-path OIDC fallback.

### Added

- **`.moat/` directory reservation (`specs/publisher-action.md`)** — normative MUST: publishers reserve `.moat/` at the repo root for MOAT protocol files. Currently defined files are `.moat/publisher.yml` (tier-2 discovery) and `.moat/registry.yml` (registry operator config). Publisher Action MUST warn on any file under `.moat/` matching `^[^.].*\.(yml|yaml)$` that is not a defined config file; non-YAML files (e.g., `README.md`, `.gitkeep`) MUST NOT trigger the warning. Files under `.moat/` MUST NOT be included in the attestation payload.
- **Actionable error messages for migration (`specs/publisher-action.md §Actionable Error Messages`)** — Publisher Action SHOULD emit diagnostics for two common misconfigurations: (1) legacy `moat.yml` present at repo root without a `.moat/publisher.yml` sibling, and (2) workflow renamed to `.github/workflows/moat-publisher.yml` but a `paths:` allow-list trigger still references `moat.yml`. Messages are log-only, not failure gates.
- **`.moat` in Undiscovered Content Detection exclusion list (`specs/publisher-action.md`)** — detection rule exclusion set now includes `.moat` alongside `.git`, `.github`, `node_modules`, `.venv`, `__pycache__`. Prevents the reservation directory from being reported as potentially undiscovered content.
- **Trusted-Root Acquisition subsection (`moat-spec.md §Trust Model`)** — three normative modes for obtaining the Sigstore trusted root: bundled default (staleness-gated, 90/180/365-day cliff), per-registry override via manifest/index `trusted_root` pointer, and invocation-time override via client flag. Defines precedence (invocation > per-registry > bundled) and rationale for exempting operator-supplied roots from the staleness cliff. Unblocks conforming clients shipping a bundled public-good trusted root while still permitting private Sigstore deployments.
- **Rename-attack binding (normative for GitHub Actions issuer)** — upgrades the prior informative risk note into a normative MUST for clients verifying manifests signed by GitHub Actions. Clients MUST match the Fulcio certificate's `sourceRepositoryIdentifier` (OID `1.3.6.1.4.1.57264.1.15`) and `sourceRepositoryOwnerIdentifier` (OID `1.3.6.1.4.1.57264.1.17`) against the pinned numeric IDs in `signing_profile`. Includes correction table calling out that OIDs `.1.12` / `.1.13` (URI / digest) are rename-mutable and NOT sufficient for this binding.
- **`signing_profile` schema extension (`moat-spec.md §Data Formats`)** — adds `repository_id` and `repository_owner_id` (REQUIRED for GitHub Actions issuer, OPTIONAL otherwise), plus optional `profile_version`, `subject_regex`, `issuer_regex`. Back-compat rule: absent `profile_version` is treated as v1. Regex fields constrain fuzzy identity matching but MUST NOT relax the numeric-ID binding above.
- **Trust State Error Vocabulary (`moat-spec.md §Trust Model`)** — normative classification of per-fetch trust decisions: `MOAT_SIGNED`, `MOAT_UNSIGNED`, `MOAT_INVALID`, `MOAT_IDENTITY_MISMATCH`, `MOAT_IDENTITY_UNPINNED`, `MOAT_TRUSTED_ROOT_STALE`. Reserves `MOAT_REVOKED` for a future revocation-propagation extension. Gives tooling, telemetry, and UI surfaces a common vocabulary without mandating a wire format.

### Removed

- **OIDC legacy-path fallback clauses (`specs/publisher-action.md`, `specs/registry-action.md`)** — deleted the fallback text that instructed Registry Actions to verify pre-v0.7.0 attestations against `.github/workflows/moat.yml@refs/heads/main` when `publisher_workflow_ref` was absent. Registries now MUST downgrade items missing `publisher_workflow_ref` to `Signed` rather than falling back to a legacy path.

### Migration (publishers)

On a clean working tree, perform all edits in a single commit:

1. `git mv .github/workflows/moat.yml .github/workflows/moat-publisher.yml`
2. If a tier-2 `moat.yml` exists: `mkdir -p .moat && git mv moat.yml .moat/publisher.yml`
3. If the workflow has a custom `paths:` allow-list referencing `moat.yml`, update it to `.moat/publisher.yml`. (The reference workflow does not need this edit — it uses `paths-ignore`, not `paths:`.)
4. Commit and push.

### Migration (registry operators)

On a clean working tree, perform all edits in a single commit:

1. `mkdir -p .moat && git mv registry.yml .moat/registry.yml`
2. Update the `paths:` trigger in `.github/workflows/moat-registry.yml` from `['registry.yml']` to `['.moat/registry.yml']`. (If using the reference workflow, replace it with the v0.7.0 version from `reference/moat-registry.yml`.)
3. Commit and push.

Emergency revocation path is unchanged: editing `.moat/registry.yml` with a new entry continues to trigger an immediate rebuild on the `moat-registry` branch.

## [0.6.1] — 2026-04-17 (Draft)

Reference template parity release. `reference/moat.yml` and `reference/moat-registry.yml` now implement the v0.6.0 normative requirements for revocation tombstones, undiscovered content detection, discovery summary logging, `(name, type)` uniqueness rejection, and the auto-populated `expires` field. Core spec text also picks up two editorial fixes: the `agents/` canonical-directory rename is carried through both reference templates, and the non-interactive client subsection's deferred-mechanism pointer now references `ROADMAP.md` instead of an internal tracking ID. No normative change — implementers targeting v0.6.0 do not need to re-validate against v0.6.1.

### Added

- **`reference/moat-registry.yml` revocation-tombstones.json emission** — Registry Action template now implements the v0.6.0 tombstone rule from [`moat-spec.md`](moat-spec.md#registry-action-requirements). On each run the action fetches `origin/moat-registry`, computes `prior_revocations − current_revocations` to find newly-pruned hashes, appends them to the existing tombstone set (union, sorted), filters any tombstoned hash from `content[]`, and writes `revocation-tombstones.json` alongside `registry.json`. First run of an existing registry creates the file. No normative change; upstream templates now match the spec.
- **`reference/moat.yml` undiscovered content detection** — Publisher template now scans for non-canonical directories at repo root that contain at least one file with a text extension but were not covered by tier-1 (canonical category directories) or tier-2 (`moat.yml`) discovery. For each unmatched directory the action emits a warning and prints a consolidated `moat.yml` snippet publishers can copy and edit. VCS and common tooling directories (`.git`, `.github`, `node_modules`, `.venv`, `__pycache__`, build output, etc.) are excluded. Behavior is detection-only and non-blocking per [`specs/publisher-action.md` §Undiscovered Content Detection](specs/publisher-action.md). No normative change; upstream template now matches the spec.
- **`reference/moat.yml` discovery summary log line** — Publisher template now emits a single summary line after the attestation phase in the form `Attested N items: X skills, Y agents, Z rules. Skipped: <dir>/ (reason).` as specified in [`specs/publisher-action.md` §Undiscovered Content Detection](specs/publisher-action.md). The "Skipped" list includes canonical category directories that exist but yielded no items, and individual items that failed hashing (symlinks, empty). Gives CI a single grep-able observability line and catches silent-skip regressions. No normative change; upstream template now matches the spec.
- **`reference/moat-registry.yml` (name, type) uniqueness rejection** — Registry Action template now enforces the v0.6.0 normative constraint from [`moat-spec.md §Registry manifest format`](moat-spec.md#registry-manifest-format) and [`specs/registry-action.md` step 7](specs/registry-action.md). After assembling `manifest_items` and applying tombstone filtering, the action groups entries by the `(name, type)` compound key; if any group has more than one member, the action prints a structured error to stderr listing each conflict with its `source_uri` and Rekor entry URL, then exits non-zero. No normative change; upstream template now matches the spec.
- **`reference/moat-registry.yml` auto-populated `expires` field** — Registry Action template now emits the optional-but-auto-emitted `expires` field described in [`moat-spec.md §Freshness Guarantee and Replay Scope`](moat-spec.md#freshness-guarantee-and-replay-scope). Default is `build_time + 72h`, matching the client-side default when `expires` is absent; operators can tighten the window (e.g., 4h for security-critical registries) via an `expires_hours` `workflow_dispatch` input. Emitted as RFC 3339 UTC. No normative change; upstream template now matches the spec.

### Fixed

- **`reference/moat.yml` + `reference/moat-registry.yml` `agents/` discovery drift** — both templates' `discover_items()` `type_map` mapped the canonical directory as `"subagents": "subagent"` instead of the v0.6.0 rename target `"agents": "agent"`. Repositories following the canonical layout had their agent content silently skipped by the Publisher, and any surviving attestations were rejected by the Registry. Now both templates discover `agents/` → `type: agent`. No spec change.
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
