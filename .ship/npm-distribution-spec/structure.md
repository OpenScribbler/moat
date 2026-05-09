# Structure Outline: npm-distribution-spec

## Current / Desired / End State

**Current:** MOAT's normative Distribution Channel is a Registry Manifest fetched over HTTPS with per-item Rekor verification. The only specified Publisher/Registry workflow is GitHub-Actions-based, and `specs/publisher-action.md` and `specs/registry-action.md` sit alongside `specs/moat-verify.md` at `specs/` root with no directory cue distinguishing transport-agnostic from GitHub-platform-specific artifacts. There is no normative spec for distributing MOAT-attested content via npm.

**Desired:** A new `specs/npm-distribution.md` defines how the transport-agnostic core protocol is realized over the npm Registry — naming the Content Directory inside the Distribution Tarball as the hash domain, fixing the `package.json` `moat` block schema with a role-discriminated `attestations: [...]` array, anchoring revocation MUSTs at the materialization boundary, framing npm provenance as observed-only, and admitting a backfill path for Registries to attest pre-existing npm packages without Publisher cooperation. The GitHub-platform-specific sub-specs live under `specs/github/` so the directory layout reflects the protocol/platform separation; `specs/moat-verify.md` stays at top level as transport-agnostic.

**End state:** A Publisher distributing a Content Item via npm declares MOAT attestation in a `package.json` `moat` block whose `contentDirectory` names the Content Directory inside the Distribution Tarball; a Conforming Client resolving or installing that package recognizes Verified, Unsigned, and Revoked Trust Tiers at the materialization boundary; a backfill-only Registry attests pre-existing npm packages without Publisher cooperation under the same `registry_signing_profile` used for normal Registry attestations; and a spec reader sees `specs/github/publisher-action.md`, `specs/github/registry-action.md`, the transport-agnostic `specs/moat-verify.md`, and the new `specs/npm-distribution.md` arranged so the protocol/platform separation is visible at a glance — with `CHANGELOG.md`'s `[Unreleased]` section documenting both the structural move (no normative change) and the new sub-spec.

## Patterns to Follow

### Pattern: Sub-spec file-level metadata header

```markdown
# Publisher Action Specification

**Version:** 0.2.0 (Draft)
**Requires:** moat-spec.md ≥ 0.5.0
**Part of:** [MOAT Specification](../moat-spec.md)

> The Publisher Action is the primary adoption mechanism for MOAT, ...

---
```

### Pattern: Heading-suffix normative status labels

```markdown
## Undiscovered Content Detection (normative)
## Actionable Error Messages (normative — SHOULD)
## Webhook (optional)
### Informed Consent Limitation (informative)
```

### Pattern: Bold-label inline normative qualifiers

```markdown
**Detection rule (normative — MUST):** If a top-level directory ...
**Unknown-file warning (normative — MUST):** ...
**Hash mismatch (normative):** ...
```

### Pattern: Field-definition table — 3-column `Field | Required | Description`

```markdown
| Field | Required | Description |
|-------|----------|-------------|
| `revocations[].reason` | REQUIRED | One of: `malicious`, `compromised`, `deprecated`, `policy_violation`. |
| `revocations[].details_url` | REQUIRED for registry / OPTIONAL for publisher | URL to public revocation details. |
| `revocations[].source` | OPTIONAL | Revocation source: `"registry"` or `"publisher"`. ... |
```

### Pattern: Fenced JSON examples with one-line lead-in

```markdown
The canonical attestation payload is:

```json
{"_version":1,"content_hash":"sha256:..."}
```
```

### Pattern: Closing `## Scope` section

```markdown
## Scope

**Current version:** Adoption mechanism for the Publisher Action; reference template at `reference/moat-publisher.yml`.

**Planned future version:** ...
```

### Pattern: Canonical Attestation Payload as the signed unit

```json
{"_version":1,"content_hash":"sha256:<hex>"}
```

### Pattern: Reason-code enum with forward-compat clause

```markdown
Reason values (informational only — they do NOT determine client behavior):
`malicious`, `compromised`, `deprecated`, `policy_violation`.
Unknown future reason values MUST be accepted without error.
```

### Pattern: CHANGELOG `[Unreleased]` entry under Keep-a-Changelog sections

```markdown
## [Unreleased]

Breaking change: ...

### Added
- **specs/npm-distribution.md** — new sub-spec describing the npm Distribution Channel ...

### Changed
- **specs/github/publisher-action.md** — moved from `specs/publisher-action.md`; no normative change.
- **specs/github/registry-action.md** — moved from `specs/registry-action.md`; no normative change.
```

## Design Summary

The work decomposes into spec-document capabilities, not modules. The directory move (Decision: GitHub sub-specs relocate to `specs/github/`) lands first because the new sub-spec's header `Part of:` link and cross-references depend on the post-move repo layout. The new sub-spec then materializes in capability waves: first the core normative spine (Content Directory hash domain per Disambiguation D5, materialization-boundary revocation per D6); then the publisher-facing `package.json` schema with the role-discriminated `attestations: [...]` array per Disambiguation D7; then the two reader-distinguishing capabilities the ticket calls out — backfill (Decision: same `registry_signing_profile`, from D-Q4) and npm-provenance orthogonality (Disambiguation D4). The website mirror and CHANGELOG `[Unreleased]` entry close the loop so a public reader can navigate to the new sub-spec from the documentation site and read the change record under Keep-a-Changelog conventions per `.claude/rules/changelog.md:10-21`.

## Slices

### Slice 1: GitHub sub-specs reachable under `specs/github/` with platform-neutral core visible at top level

**Observable outcome:** A spec reader walks `specs/`, sees `moat-verify.md` at top level (signaling platform neutrality), sees `specs/github/publisher-action.md` and `specs/github/registry-action.md` grouped under a GitHub directory, and every cross-reference repo-wide that pointed at the old paths now resolves to the new paths. `grep -rn "specs/publisher-action.md\|specs/registry-action.md" .` returns no spec-content hits outside `panel/` and `CHANGELOG.md` historical entries.

**Interfaces introduced or modified:**

- `specs/github/publisher-action.md` — moved from `specs/publisher-action.md`; content unchanged — **Deps:** `local-substitutable`
  - **Hides:** Internal section structure of the Publisher Action sub-spec is unchanged; only its file location is observable to consumers.
  - **Exposes:** Same H1 / `Version:` / `Requires:` / `Part of:` / blockquote header; same section heading map. The `Part of:` link path becomes `../../moat-spec.md` (one level deeper).
- `specs/github/registry-action.md` — moved from `specs/registry-action.md`; content unchanged — **Deps:** `local-substitutable`
  - **Hides:** Same — section structure unchanged.
  - **Exposes:** Same body; `Part of:` link becomes `../../moat-spec.md`.
- `specs/moat-verify.md` — unchanged; remains at top level as the transport-neutral signal — **Deps:** `local-substitutable`
  - **Hides:** Nothing new.
  - **Exposes:** Top-level location is itself the platform-neutrality cue.
- `moat-spec.md` cross-reference surface — **Deps:** `local-substitutable`
  - **Hides:** The body prose around each link is unchanged; only path strings update.
  - **Exposes:** `**Sub-specs:**` list (line 9) and inline links (lines 103, 143, 148, 218, 281, 286, 681, 682, 1068) point at `specs/github/...`.
- `lexicon.md` Publisher Action / Registry Action entries (lines 43–44) — **Deps:** `local-substitutable`
  - **Hides:** Definitions unchanged.
  - **Exposes:** Path pointers updated to `specs/github/...`.

**Files:**

- `specs/github/publisher-action.md` — new path; content identical to old `specs/publisher-action.md` modulo the `Part of:` link's relative depth.
- `specs/github/registry-action.md` — same; new path, body identical.
- `specs/publisher-action.md` — deleted at this path.
- `specs/registry-action.md` — deleted at this path.
- `moat-spec.md` — `**Sub-specs:**` header and 9 inline cross-reference links updated to `specs/github/...`.
- `lexicon.md` — entries at lines 43, 44 updated to point at `specs/github/...`.
- `README.md` — table rows at lines 35, 36 updated to `specs/github/...`.
- `RELEASING.md` — line 99 updated to `specs/github/publisher-action.md`.
- `docs/guides/publisher.md` — line 248 updated to `../../specs/github/publisher-action.md`.
- `reference/moat-publisher.yml` — code-comment paths at lines 260, 482 updated to `specs/github/publisher-action.md`.
- `reference/moat-registry.yml` — code-comment path at line 759 updated to `specs/github/registry-action.md`.
- `.github/workflows/moat-publisher.yml` — same comment updates as the reference template (lines 260, 482).
- `.github/workflows/moat-registry.yml` — same comment update as the reference template (line 759).

**Test cases:**

- Unit: `grep -rn "specs/publisher-action.md" -- ':!panel/' ':!CHANGELOG.md' ':!.ship/'` returns zero matches — every non-historical reference points at the new path.
- Unit: `grep -rn "specs/registry-action.md" -- ':!panel/' ':!CHANGELOG.md' ':!.ship/'` returns zero matches.
- Unit: `test -f specs/github/publisher-action.md && test -f specs/github/registry-action.md && test -f specs/moat-verify.md && ! test -e specs/publisher-action.md && ! test -e specs/registry-action.md` exits 0.
- Integration: every Markdown link in `moat-spec.md`, `lexicon.md`, `README.md`, `RELEASING.md`, `docs/guides/publisher.md` whose target was `specs/publisher-action.md` or `specs/registry-action.md` now resolves to a file that exists under `specs/github/`.
- Unit: `grep -n 'specs/github' lexicon.md` returns at least the two updated rows; the term entries themselves are otherwise byte-identical.

**Checkpoint:** `find specs -name '*.md' | sort` lists exactly `specs/github/publisher-action.md`, `specs/github/registry-action.md`, `specs/moat-verify.md`; and `grep -rln 'specs/publisher-action.md\|specs/registry-action.md' . | grep -v -E '^(\./)?(panel/|CHANGELOG\.md|\.ship/)'` returns no results.

### Slice 2: npm-distribution sub-spec fixes the Tarball-Content-Directory hash domain and the materialization-boundary revocation contract

**Observable outcome:** A reader opening `specs/npm-distribution.md` sees the house-style header, a normative section that names the Content Directory inside the Distribution Tarball as the hash input domain (citing `reference/moat_hash.py` without redefining the algorithm), and a normative section anchoring revocation hard-blocks at the pre-materialization boundary with the lockfile `revoked_hashes` persistence rule inherited unchanged from `moat-spec.md`. The file passes the four MOAT design tests (day-one, copy-survival, works-fine-without-it, enforcement) when read against the four-test checklist.

**Interfaces introduced or modified:**

- `specs/npm-distribution.md` (header + normative spine) — **Deps:** `local-substitutable`
  - **Hides:** Internal section ordering and prose rhythm; readers consume the artifact through its public sections only.
  - **Exposes:** H1 `# npm Distribution Specification`; `**Version:** 0.1.0 (Draft)`; `**Requires:** moat-spec.md ≥ 0.7.1`; `**Part of:** [MOAT Specification](../moat-spec.md)`; blockquote one-liner; trailing `---`. Two normative spine sections: `## Content Hash Domain (normative)` and `## Revocation at the Materialization Boundary (normative)`.
- `reference/moat_hash.py` (cited, not modified) — **Deps:** `local-substitutable`
  - **Hides:** Algorithm body, NFC normalization rules, exclusion list — all stay in the reference file.
  - **Exposes:** A single normative cross-reference from the new sub-spec saying "the algorithm is unchanged; only the input directory differs (the unpacked Distribution Tarball's Content Directory)."
- `moat-spec.md §Lockfile` `revoked_hashes` semantics (cited, not modified) — **Deps:** `local-substitutable`
  - **Hides:** The persistence rule (`moat-spec.md:865`) and the lockfile-authoritative rule (`moat-spec.md:663`) stay where they are.
  - **Exposes:** A normative cite from the new sub-spec saying revoked hashes keyed by Content Hash continue to hard-block republished tarballs containing identical bytes.
- npm registry / Sigstore / Rekor concepts (cited, not redefined) — **Deps:** `true-external`
  - **Hides:** npm tarball mechanics, Sigstore bundle format, Rekor log internals — all referenced by name only.
  - **Exposes:** Bare term mentions ("the unpacked tarball", "Rekor log entry", "Sigstore bundle") used to anchor what MOAT layers on top of.

**Files:**

- `specs/npm-distribution.md` — new file, sections written through `## Revocation at the Materialization Boundary (normative)`. Subsequent slices append further sections; this slice writes the file's first ~third.

**Test cases:**

- Unit: `head -9 specs/npm-distribution.md` matches the house-style header pattern (H1 ending in "Specification", `**Version:**`, `**Requires:**`, `**Part of:** [MOAT Specification](../moat-spec.md)`, blockquote, trailing `---`).
- Unit: every section heading in the file ends in one of `(normative)`, `(normative — MUST)`, `(normative — SHOULD)`, `(informative)`, or `(optional)` per the heading-suffix pattern (verified by `grep -E '^## .+\((normative|informative|optional)' specs/npm-distribution.md`).
- Unit: `grep -E 'def content_hash|rglob|NFC' specs/npm-distribution.md` returns zero matches — the sub-spec cites `reference/moat_hash.py` rather than re-implementing the algorithm.
- Unit: `grep -n 'revoked_hashes' specs/npm-distribution.md` returns matches that are all references (no field definitions) — the lockfile schema is not redefined.
- Manual: read every MUST in the new sections against the four MOAT design tests in `CLAUDE.md:121-127`; each MUST answers the enforcement question with a Conforming Client action (refuse to materialize). No MUST exists that has no enforcement mechanism.
- Manual: read the sub-spec for day-one prose — it acknowledges that existing npm packages on day one carry no `moat` block and are `Unsigned` from MOAT's perspective.
- Manual: read the sub-spec for the copy-survival assertion — the hash domain is the bytes inside the tarball, so a republished or copied tarball with identical Content Directory bytes produces the same Content Hash and inherits the same revocation state.

**Checkpoint:** `specs/npm-distribution.md` exists, opens with the house-style header, contains `## Content Hash Domain (normative)` and `## Revocation at the Materialization Boundary (normative)` sections, and a Markdown-lint pass plus a manual read against `CLAUDE.md:121-127` (the four design tests) confirms each MUST is enforceable.

### Slice 3: `package.json` `moat` block schema with role-discriminated `attestations[]` array and worked example readable by Publishers

**Observable outcome:** A Publisher reading `specs/npm-distribution.md` finds a single `## package.json moat Block (normative)` section with a 3-column `Field | Required | Description` table fixing every field of the `moat` block (including `contentDirectory` per Q1) and a fenced JSON worked example showing a populated `moat` block with two `attestations[]` entries (one publisher, one registry) signing the canonical `{"_version":1,"content_hash":"sha256:..."}` payload. A Conforming Client implementer reading the same section can walk `attestations[]`, dispatch on `role`, and verify each entry's bundle without parsing the spec a second time.

**Interfaces introduced or modified:**

- `specs/npm-distribution.md §package.json moat Block (normative)` — **Deps:** `local-substitutable`
  - **Hides:** The internal grouping logic (which fields are MUST vs SHOULD vs MAY) is captured in one place — the field-definition table. Readers do not have to reconstruct it from scattered prose.
  - **Exposes:** Field-definition table for the `moat` object: `moat.contentDirectory` (REQUIRED), `moat.attestations` (REQUIRED, array), `moat.attestations[].role` (REQUIRED, enum `publisher | registry`), `moat.attestations[].bundle` (REQUIRED, base64 Sigstore protobuf bundle v0.3), `moat.attestations[].rekor_log_index` (REQUIRED, integer), and any further fields the design fixes. Worked-example JSON block with the canonical payload and both attestation roles populated.
- Canonical Attestation Payload `{"_version":1,"content_hash":"sha256:<hex>"}` (cited, not redefined) — **Deps:** `local-substitutable`
  - **Hides:** The canonicalization rules at `moat-spec.md:1020-1071` stay in the core spec.
  - **Exposes:** A one-sentence cite from the new section saying each `attestations[]` entry, regardless of `role`, signs this exact payload. The sub-spec MUST NOT introduce a second canonical payload format.
- `(role)` uniqueness invariant within `attestations[]` — **Deps:** `in-process`
  - **Hides:** No new structure.
  - **Exposes:** A bold-label inline qualifier: `**Role uniqueness (normative — MUST):** an attestations array MUST NOT contain two entries with the same role value.`
- Cosign Bundle / Sigstore protobuf v0.3 (cited, not redefined) — **Deps:** `true-external`
  - **Hides:** Bundle format mechanics live in the Sigstore project.
  - **Exposes:** The sub-spec names the bundle format by version and cites `moat-spec.md:426` for the canonical bundle-format pin.

**Files:**

- `specs/npm-distribution.md` — appends `## package.json moat Block (normative)` and the worked-example JSON. The file now covers header + hash domain + revocation contract + `package.json` schema.

**Test cases:**

- Unit: the section contains exactly one Markdown table whose columns are `Field | Required | Description` and whose rows include `moat.contentDirectory`, `moat.attestations`, `moat.attestations[].role`, `moat.attestations[].bundle`, `moat.attestations[].rekor_log_index`. Each `Required` cell carries an RFC 2119 keyword (`REQUIRED`, `OPTIONAL`, or a "REQUIRED for X / OPTIONAL for Y" form).
- Unit: a fenced ```json block follows the table, contains `"moat": {`, contains `"contentDirectory":`, contains `"attestations": [`, and contains at least two array entries — one with `"role": "publisher"` and one with `"role": "registry"`. The example is introduced by a one-sentence prose lead-in per the introduce-then-fence pattern.
- Unit: `grep -n '_version' specs/npm-distribution.md` finds the canonical `{"_version":1,"content_hash":"sha256:..."}` payload form (cited from `moat-spec.md`) — not a variant. The section does NOT define a second payload shape.
- Unit: `grep -nE '\*\*Role uniqueness \(normative — MUST\):\*\*' specs/npm-distribution.md` returns exactly one match — a bold-label inline qualifier forbidding duplicate roles.
- Manual: read the section for length-zero array semantics — it explicitly treats `"attestations": []` as a Day-One-legitimate state (Publisher has reserved the `moat` block but no attestation is yet present), not an error. This satisfies the day-one test for the schema slice.

**Checkpoint:** A Publisher copy-pastes the worked-example block into a real `package.json`, fills in real `content_hash` and `bundle` values, and a `python -c 'import json; json.load(open("package.json"))'` parses it cleanly; a manual read of the table against the design's D7 disambiguation confirms all four states (publisher-only, registry-only, both, neither) are representable by the array's natural cardinality.

### Slice 4: Backfill path and npm-provenance orthogonality codified so existing npm packages can be attested without Publisher cooperation

**Observable outcome:** A Registry Operator reading `specs/npm-distribution.md` finds a normative section explaining how to attest a pre-existing npm package without Publisher cooperation, using the same `registry_signing_profile` as a normal Registry attestation; a Conforming Client implementer reading the same file finds an `(informative)` section explaining that npm provenance, when present, is observed-only — it does NOT change the Trust Tier and MUST NOT be required for the `Verified` label. The result: the four states (publisher-only, registry-only, both, neither) the role-discriminated array represents map cleanly to real-world npm publishing scenarios with no protocol gap.

**Interfaces introduced or modified:**

- `specs/npm-distribution.md §Backfill Attestation by Registry (normative)` — **Deps:** `local-substitutable`
  - **Hides:** The operational decision to use the same `registry_signing_profile` (rather than a `registry_backfill_signing_profile`) is fixed; readers do not need to reason about why.
  - **Exposes:** Normative prose stating: a backfill-only Registry attestation uses the same `registry_signing_profile` as a normal Registry attestation; the operational distinction (publisher counter-signature absent vs present) is encoded in the resulting Trust Tier (`Signed` vs `Dual-Attested`), not in a second profile field. `source_uri` for npm-only items where no Source Repository is known is fixed by reference to the manifest content-entry schema at `moat-spec.md:766-807`; the `(name, type)` uniqueness invariant is preserved.
- `specs/npm-distribution.md §npm Provenance (informative)` — **Deps:** `true-external`
  - **Hides:** The npm provenance feature's internals (build attestations, registry-side verification) live in npm's own documentation.
  - **Exposes:** Informative-only prose stating: npm provenance is observed-when-present, recommended-but-not-required, orthogonal to MOAT Trust Tiers. A Conforming Client MAY surface npm provenance presence in its UI as a separate row from the Trust Tier; it MUST NOT use npm provenance to compute or override the Trust Tier. Future registry transports inherit the same orthogonality principle.
- Trust Tier values (`Dual-Attested`, `Signed`, `Unsigned`) — cited, not modified — **Deps:** `local-substitutable`
  - **Hides:** Tier-determination logic stays in `specs/github/registry-action.md §Trust Tier Determination` (now at the new path) and `moat-spec.md §Trust Model`.
  - **Exposes:** A cite saying tier values carry the same meaning whether the Distribution Channel is GitHub or npm; the npm sub-spec adds no fourth tier and no hidden modifier.
- Sigstore / Rekor primitives (cited as the trust anchor) — **Deps:** `true-external`
  - **Hides:** Backfill attestations are signed and logged identically to normal Registry attestations.
  - **Exposes:** A cite confirming the canonical Attestation Payload signed in a backfill case is byte-identical to the canonical payload signed in a normal Registry case.

**Files:**

- `specs/npm-distribution.md` — appends `## Backfill Attestation by Registry (normative)`, `## npm Provenance (informative)`, and closes with a `## Scope` section using the bold-prefixed `**Current version:**` / `**Planned future version:**` form per the closing-`## Scope` pattern.

**Test cases:**

- Unit: `grep -nE '^## Backfill.+\(normative' specs/npm-distribution.md` returns one match — a section heading containing `Backfill` and ending in `(normative)` (or `(normative — MUST)` / `(normative — SHOULD)`) exists.
- Unit: `grep -nE '^## npm Provenance \(informative\)' specs/npm-distribution.md` returns one match — a section heading containing `npm Provenance` and ending in `(informative)` exists. Its body explicitly states npm provenance MUST NOT be used to compute or override the Trust Tier.
- Unit: `grep -n -E 'Verified|Dual-Attested|Signed|Unsigned' specs/npm-distribution.md` finds all four labels used consistently with their `moat-spec.md` definitions; no fourth tier is invented.
- Unit: `grep -n 'registry_backfill_signing_profile' specs/npm-distribution.md` returns zero matches — the backfill section uses the same `registry_signing_profile`, no second profile field is introduced.
- Unit: `tail -10 specs/npm-distribution.md | grep -E '## Scope'` finds the closing section; the section body contains both `**Current version:**` and `**Planned future version:**` bold-label one-liners.
- Manual: read the file for worked-state coverage — the four states the role-discriminated array represents (publisher-only / registry-only / both / neither) are each acknowledged as legitimate runtime configurations; none is described as an error.
- Manual: read the backfill section against the day-one test — the sub-spec acknowledges that on day one, thousands of npm packages exist with no `moat` block, and the backfill path lets a Registry attest those without Publisher cooperation.

**Checkpoint:** A Registry Operator reads the Backfill section and can answer "yes, I can attest an existing npm package without the Publisher's cooperation, using my normal `registry_signing_profile`" without consulting any other document; a Conforming Client implementer reads the npm Provenance section and can answer "no, npm provenance does not change the Trust Tier" without ambiguity. `specs/npm-distribution.md` is feature-complete and survives a manual pass through the four MOAT design tests in `CLAUDE.md:121-127`.

### Slice 5: Website mirror surfaces the new sub-spec and CHANGELOG `[Unreleased]` entry documents the change set

**Observable outcome:** A reader visits the documentation site, sees the Starlight sidebar list "npm Distribution" alongside the existing sub-spec entries, navigates to `/spec/npm-distribution`, and reads the new sub-spec rendered through the website mirror. A reader visits `CHANGELOG.md`, sees an `[Unreleased]` section with one `### Added` bullet describing the new sub-spec and one `### Changed` bullet documenting the `specs/github/` directory move with the explicit "no normative change" phrase. Both bullets follow the bold-label form and contain no panel/persona/finding-ID/count language.

**Interfaces introduced or modified:**

- `website/src/content/docs/spec/npm-distribution.md` — **Deps:** `local-substitutable`
  - **Hides:** The Markdown body is a mirror of `specs/npm-distribution.md` produced for the Starlight content collection.
  - **Exposes:** A page reachable at the `spec/npm-distribution` slug; same sectioning as the canonical sub-spec.
- `website/src/content/docs/spec/core.md` (the website mirror of `moat-spec.md`) — **Deps:** `local-substitutable`
  - **Hides:** Body unchanged. Cross-reference anchors here use slug form (`/spec/publisher-action`), which is decoupled from filesystem path; the directory move does NOT propagate edits to the nine slug-based links.
  - **Exposes:** `**Sub-specs:**` header (line 9) gains `[npm Distribution](/spec/npm-distribution)` alongside the existing three slug entries. No other lines in `core.md` change.
- `website/astro.config.mjs` sidebar (lines 87–94) — **Deps:** `local-substitutable`
  - **Hides:** Starlight sidebar config; the entry's shape is unchanged.
  - **Exposes:** A new entry `{ label: 'npm Distribution', slug: 'spec/npm-distribution' }` joins the existing four-item `Specification` group (`spec/core`, `spec/moat-verify`, `spec/publisher-action`, `spec/registry-action`); existing slugs are preserved verbatim.
- `website/src/content/docs/spec/publisher-action.md` and `website/src/content/docs/spec/registry-action.md` (slug stability) — **Deps:** `local-substitutable`
  - **Hides:** These files stay where they are — their location is dictated by Starlight slug, not by canonical-spec filesystem path. Their bodies use slug-form links (`/spec/registry-action`) that are unaffected by the directory move.
  - **Exposes:** No changes from this slice. (Their bodies are maintained in parallel to the canonical specs and any sync work is out-of-scope per the concept's "Implementation of `moat-verify` CLI changes — spec-only deliverable" stance, which extends to website-mirror sync.)
- Website overview / guides surface (audit-only) — **Deps:** `local-substitutable`
  - **Hides:** No new structure.
  - **Exposes:** `grep -rln 'specs/publisher-action.md\|specs/registry-action.md' website/src/` confirms zero filesystem-path references in these files (they all use `/spec/<slug>` form). An audit step verifies the empty result; if any non-zero match appears, those lines are updated to `specs/github/...`. The audit is a guard, not an expected edit.
- `CHANGELOG.md` `[Unreleased]` section — **Deps:** `local-substitutable`
  - **Hides:** The release-history versioned sections below `[Unreleased]` are untouched.
  - **Exposes:** Two new bullets — `### Added` for the new sub-spec, `### Changed` for the directory move (with the explicit "no normative change" phrase). Bullets follow the bold-label form per `.claude/rules/changelog.md:43-48`.

**Files:**

- `website/src/content/docs/spec/npm-distribution.md` — new mirror of the canonical sub-spec.
- `website/src/content/docs/spec/core.md` — `**Sub-specs:**` header and the nine inline cross-reference anchors updated to `specs/github/...`.
- `website/astro.config.mjs` — sidebar gains the new entry; line 91-92 entries retain their slugs.
- `website/src/content/docs/overview/spec-status.md`, `website/src/content/docs/overview/use-cases.md`, `website/src/content/docs/guides/publishers.md`, `website/src/content/docs/guides/registry-operators.md` — audit sweep; updates only where canonical-spec file paths (not slugs) are referenced.
- `CHANGELOG.md` — `[Unreleased]` section gains an `### Added` bullet for `specs/npm-distribution.md` and a `### Changed` bullet for the `specs/github/` directory move with the "no normative change" phrase.

**Test cases:**

- Unit: `grep -n 'npm-distribution' website/astro.config.mjs` returns at least one match — the new sidebar entry sits alongside the existing `spec/publisher-action` / `spec/registry-action` entries.
- Unit: `test -f website/src/content/docs/spec/npm-distribution.md` exits 0; the mirror's first heading line matches the canonical sub-spec's first heading line.
- Manual: diff `specs/npm-distribution.md` against `website/src/content/docs/spec/npm-distribution.md` — only website-frontmatter differences (Starlight YAML frontmatter at the top) and link-path differences (relative-link rewrites) appear, not body-prose differences.
- Unit: `head -40 CHANGELOG.md | grep -E '^## \[Unreleased\]'` returns exactly one match; below it, an `### Added` line and a `### Changed` line both appear before the next `## [<version>]` heading.
- Unit: `grep -nE '\*\*specs/npm-distribution\.md\*\*' CHANGELOG.md` returns at least one match in the `[Unreleased]` block, and `grep -nE '\*\*specs/github/(publisher|registry)-action\.md\*\*' CHANGELOG.md` returns at least two matches, all containing the literal phrase `no normative change` per `.claude/rules/changelog.md:43-48`.
- Unit: `awk '/^## \[Unreleased\]/,/^## \[[0-9]/' CHANGELOG.md | grep -nE '(panel|persona|five-persona|adversarial|reviewer feedback|agent consensus|SC-[0-9]|DQ-[0-9]|SB-[0-9])'` returns no matches — the pre-save checklist at `.claude/rules/changelog.md:66-73` passes.
- Integration: every internal Markdown link in `website/src/content/docs/spec/core.md` whose target was the old canonical-spec slug or path resolves under the website's build (Astro `npm run build` or equivalent succeeds with no broken-link warnings).

**Checkpoint:** Running the website's local preview command renders the Starlight sidebar with three spec sub-pages plus core, the new `/spec/npm-distribution` page loads with the canonical sub-spec body, and `head -30 CHANGELOG.md` shows an `[Unreleased]` section whose two bullets pass the `.claude/rules/changelog.md:66-73` four-item pre-save checklist (no panel/persona/review language, no `SC-N` / `DQ-N` / `SB-N` finding IDs, no internal-artifact counts, opening prose describes the release not the process).

## Acceptance

- `specs/npm-distribution.md` exists with: house-style metadata header (H1 / Version / Requires / Part of / blockquote / `---`), normative `package.json moat`-block field-definition table including `contentDirectory` and the role-discriminated `attestations[]` array, Tarball-Content-Directory hash-domain section citing `reference/moat_hash.py` without redefinition, materialization-boundary revocation contract citing `moat-spec.md:663, 855, 865` without redefinition, normative backfill-by-registry section, informative npm-provenance section explicit about Trust Tier orthogonality, at least one fenced JSON worked example showing a populated `moat` block with both `role: "publisher"` and `role: "registry"` entries, and a closing `## Scope` section with `**Current version:**` and `**Planned future version:**` lines.
- `specs/github/publisher-action.md` and `specs/github/registry-action.md` exist with content unchanged from their old locations modulo the `Part of:` link's relative depth; `specs/publisher-action.md` and `specs/registry-action.md` no longer exist; `specs/moat-verify.md` is unchanged.
- All cross-references to the moved files throughout `moat-spec.md`, `lexicon.md`, `README.md`, `RELEASING.md`, `docs/guides/publisher.md`, `reference/moat-publisher.yml`, `reference/moat-registry.yml`, `.github/workflows/moat-publisher.yml`, `.github/workflows/moat-registry.yml`, and the website mirror are updated to `specs/github/...`. Panel artifacts under `panel/` are intentionally untouched per `.claude/rules/changelog.md:21`.
- `CHANGELOG.md` `[Unreleased]` section contains one `### Added` bullet for the new sub-spec and one `### Changed` bullet for the directory move; both follow the bold-label form; the `### Changed` bullet carries the explicit "no normative change" phrase; neither bullet contains panel/persona/finding-ID/count language per `.claude/rules/changelog.md:23-32`.
- The new sub-spec specifies what is hashed for npm-distributed content (the unpacked Distribution Tarball's Content Directory) and explicitly explains the relationship to npm's tarball SHA-512 and npm provenance — npm provenance is observed-when-present and orthogonal to Trust Tier; npm's tarball SHA-512 is npm's own integrity primitive, not the MOAT Content Hash.
- The new sub-spec defines a backfill path so a Registry can attest a pre-existing npm package without Publisher cooperation, using the same `registry_signing_profile` as a normal Registry attestation.
- The new sub-spec passes the four MOAT design tests in `CLAUDE.md:121-127` (day-one, copy-survival, works-fine-without-it, enforcement); each MUST has a Conforming Client enforcement mechanism (refuse to materialize at the materialization boundary).
- The website mirror at `website/src/content/docs/spec/npm-distribution.md` exists and is reachable via the Starlight sidebar; existing sub-spec slugs `spec/publisher-action` and `spec/registry-action` are preserved.
- House-style conformance: every section heading in the new sub-spec carries an RFC-2119-status parenthetical (`(normative)`, `(normative — MUST)`, `(normative — SHOULD)`, `(informative)`, or `(optional)`); inline normative qualifiers use the bold-label form per the design's Pattern: Bold-label inline normative qualifiers.

## Out of Scope

- Runtime gating of execution (post-materialization import/require interception) — explicitly outside MOAT's protocol boundary.
- Other registry transports (PyPI, Cargo, Maven, container registries) — npm only for this sub-spec.
- Changes to the transport-agnostic core protocol semantics in `moat-spec.md` beyond what's strictly required to host the npm binding.
- Renaming `publisher-action.md` / `registry-action.md` filenames — only their directory location changes.
- Implementation of `moat-verify` CLI changes — spec-only deliverable.
- New attestation roles beyond publisher and registry.
