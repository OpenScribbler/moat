# Structure Outline: npm-distribution-spec — Round 2

## Current / Desired / End State

**Current:** `specs/npm-distribution.md` (v0.1.0 Draft) shipped at commit `64b9c6b` covers the Content Hash domain, materialization-boundary revocation MUSTs, the `package.json` `moat` block schema, the backfill normative section, and the npm provenance informative section — but the Content Directory rule requires Publisher cooperation (no default), the `MOAT_ALLOW_REVOKED` escape hatch is half-finished (no reason-capture, no per-entry expiry, no logging contract), the materialization boundary is named but not anchored to a precise byte-level moment, the JSON field name `moat.contentDirectory` collides with the lexicon's "Content Directory" concept-name, the npm provenance section lacks a four-state disagreement table, the Publisher attestation embeds the full Cosign Bundle inline rather than disclosing identity and treating Rekor as authoritative, no reference Publisher workflow exists, `moat-spec.md:9`'s Sub-specs line still omits the new sub-spec, and `.claude/rules/changelog.md:40` still cites a pre-reorg path.

**Desired:** `specs/npm-distribution.md` v0.2.0 Draft defines a default Content Directory (= tarball root with one excluded file: `package.json`) so backfill works without Publisher cooperation; renames the JSON field to `moat.tarballContentRoot` to disambiguate concept-vs-realization with a lexicon cross-reference; anchors the materialization boundary normatively at "before any byte of the tarball is written outside the package manager's content cache"; fully specifies `MOAT_ALLOW_REVOKED` (process-scope, REQUIRED reason co-variable, RFC 3339 per-entry expiry, structured override-applied log event); relocates Publisher signing identity into a `publisherSigning` block with optional `rekorLogIndex` discovery accelerator; adds a four-state (provenance × MOAT) disagreement table; ships `reference/moat-npm-publisher.yml` end-to-end; and corrects `moat-spec.md:9` and `.claude/rules/changelog.md:40` cross-references.

**End state:** A Publisher with no source-repo cooperation has their existing npm package backfilled by a Registry — the Registry fetches the Distribution Tarball, applies the default-Content-Directory rule (tarball root minus `package.json`), and produces a Content Hash any Conforming Client can independently reproduce by fetching the same tarball. A Publisher who wants to attest in `package.json` copies `reference/moat-npm-publisher.yml` and gets a working flow from `npm pack` through `npm publish` whose canonical hash is stable across the log-index round-trip. An operator running incident response sets `MOAT_ALLOW_REVOKED=<sha>:<RFC3339>` plus `MOAT_ALLOW_REVOKED_REASON="..."` and every override is logged with package identity, hash, reason, and expiry — the silent-skip footgun is closed. A spec reader sees `specs/npm-distribution.md` cited from `moat-spec.md:9` and a changelog rule that points at the post-reorg path.

## Patterns to Follow

These are copied verbatim from design.md's Patterns section. Round 1 patterns (Sub-spec file-level metadata header, Heading-suffix normative status labels, Bold-label inline normative qualifiers, Field-definition tables, Fenced JSON examples, Closing `## Scope` section, Canonical Attestation Payload, Manifest content-entry schema, CHANGELOG `[Unreleased]` form) are inherited from the Round 1 design.md (commit `64b9c6b`) and not re-explained here.

### Pattern: Default-with-explicit-override field semantics

```markdown
| `content[].rekor_log_index` | REQUIRED for Signed + Dual-Attested | Integer index ... Absent for Unsigned items — its absence is the Unsigned tier signal. |
```

A field whose absence is itself a load-bearing signal (precedent: `moat-spec.md:786`). Round 2 makes `moat.tarballContentRoot` an OPTIONAL field whose absence triggers the default = tarball root with `package.json` excluded.

### Pattern: Field-name realizes lexicon concept (concept ≠ field name)

```markdown
- **Signature** = the cryptographic output of `cosign sign-blob` (a field inside the cosign bundle).
- **Attestation** = the protocol-level claim that a `content_hash` existed at a logged time, manifested as a Rekor entry over the canonical Attestation Payload.
```

Lexicon-concept-vs-realization split (precedent: `lexicon.md:111-119`). Round 2 keeps the lexicon term "Content Directory" and renames the JSON field to `moat.tarballContentRoot`; the lexicon's Content Directory entry gains a one-line note that `tarballContentRoot` is one realization of the concept.

### Pattern: Process-scope environment variable read once at start

```yaml
env:
  ALLOW_PRIVATE_REPO: 'false'   # set to 'true' to attest private repos
```

Read-once discipline at the start of a workflow step (precedent: `reference/moat-publisher.yml:54`). Round 2 makes the read-once rule normative for `MOAT_ALLOW_REVOKED` and `MOAT_ALLOW_REVOKED_REASON` — re-reading mid-process is non-conformant.

### Pattern: Co-variable required for risky operation

```markdown
publisher-source revocation = MUST present, warn once per session,
MAY allow with explicit confirmation, MUST NOT silently continue.
```

Risky operation requires a paired operator-supplied artifact (precedent: `moat-spec.md:633-636`). Round 2 makes `MOAT_ALLOW_REVOKED_REASON` a hard-fail prerequisite: a Conforming Client MUST refuse to honor `MOAT_ALLOW_REVOKED` if the reason is unset or empty.

### Pattern: RFC 3339 timestamps for protocol-time fields

```markdown
| `content[].attested_at` | REQUIRED | Registry attestation timestamp (RFC 3339 UTC) |
```

Protocol timestamps are RFC 3339 UTC (precedent: `moat-spec.md:784`). Round 2 encodes per-entry override expiry as `<sha256-hex>:<RFC3339-timestamp>`; entries past expiry MUST be ignored as if absent.

### Pattern: Sigstore Rekor authoritative + identity disclosure in metadata

```markdown
content[].signing_profile  REQUIRED for Dual-Attested  references signing_profile schema
```

Rekor is the trust anchor; the manifest discloses the expected signing identity (precedent: `moat-spec.md:790`). Round 2's `publisherSigning.{issuer, subject}` mirrors `signing_profile` exactly: the disclosed identity binds the Rekor entry to the right Publisher; `publisherSigning.rekorLogIndex` is only a discovery accelerator.

### Pattern: Reference workflow as adoption-mechanism template

```yaml
name: MOAT Publisher Action

on:
  push:
    branches:
      - main

permissions:
  id-token: write
  contents: write

jobs:
  attest:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout source repository
        uses: actions/checkout@... # v4
      - name: Install cosign
        uses: sigstore/cosign-installer@... # v3.8.1
      ...
```

Single-file YAML a Publisher copies verbatim into `.github/workflows/` (precedent: `reference/moat-publisher.yml:1-80`). Round 2's `reference/moat-npm-publisher.yml` mirrors this shape; the seven steps (`npm pack` → compute canonical hash → Sigstore sign → push to Rekor → write log index back into `package.json` → re-pack → `npm publish`) realize the canonical "compute hash, sign payload, log to Rekor" flow over the npm channel, with the two-pack design making the canonical hash stable across the log-index round-trip (because `package.json` is excluded from the canonical hash, mutating it between packs does not change the hash).

## Design Summary

Round 2 lands ten in-scope decisions from the final-validate gate review on the Round 1 commit `64b9c6b`. The decisions cluster into seven capability slices: (1) the default-Content-Directory rule with `package.json` exclusion (C-1 + C-6b) which makes Registry-side backfill possible without Publisher cooperation; (2) the `moat.contentDirectory` → `moat.tarballContentRoot` rename plus the lexicon note (C-2) which locks concept-vs-realization; (3) the `MOAT_ALLOW_REVOKED` hardening (C-3) which closes the silent-skip footgun via REQUIRED reason co-variable, RFC 3339 expiry, and a structured override-applied log event; (4) the materialization-boundary cache-anchor rephrase (B-1); (5) the relocation of Publisher signing identity from `attestations[].bundle` to `publisherSigning.{issuer, subject, rekorLogIndex}` (C-6a) treating Rekor as authoritative; (6) the four-state provenance × MOAT disagreement table (B-2); and (7) the new `reference/moat-npm-publisher.yml` end-to-end (C-6c). The cross-spec rider edits (A-1, A-2 — the `moat-spec.md:9` Sub-specs cite and the `.claude/rules/changelog.md:40` path fix), the version bump v0.1.0 → v0.2.0, the CHANGELOG `[Unreleased]` entries, and the website mirror byte-identical sync attach to the slices that introduce the corresponding normative change. Two cross-cutting findings (Layering rule + GitHub-ism extraction; Aggregator UI Trust Tier strings) are out of scope per the Round 2 concept and listed in Out of Scope below.

## Slices

### Slice 1: Default-Content-Directory backfill capability

**Observable outcome:** Given any published npm tarball, two independent Conforming Clients (or two independent Registries) can compute the same canonical Content Hash from the tarball alone without Publisher cooperation, by applying the default-Content-Directory rule (tarball root with `package.json` excluded). A backfill workflow produces hashes byte-identical to those a Publisher-driven flow would produce for the same content bytes.

**Interfaces introduced or modified:**

- `specs/npm-distribution.md § Content Directory (normative — MUST)` — new normative subsection — **Deps:** `in-process`
  - **Hides:** the Round 1 ambiguity that left default behavior to Conforming-Client discretion; the chicken-and-egg between writing a Rekor log index into `package.json` and the canonical hash covering that file
  - **Exposes:** a single fixed default — when `moat.tarballContentRoot` is absent, the canonical Content Directory is the unpacked tarball root with `package.json` excluded; subdirectory mode applies no exclusions; the spec MUST forbid Publisher-driven extension of the exclusion list
- `specs/npm-distribution.md` file-level metadata header — version bump v0.1.0 → v0.2.0 Draft — **Deps:** `in-process`
  - **Hides:** none (one-line edit)
  - **Exposes:** new spec version on the canonical artifact and the website mirror
- `website/src/content/docs/spec/npm-distribution.md` — byte-identical mirror update (after Starlight front-matter) — **Deps:** `in-process`
  - **Hides:** the Starlight front-matter divergence that the website wrapper requires
  - **Exposes:** the same normative body to website readers as the canonical sub-spec; non-mirror drift is forbidden
- `CHANGELOG.md § [Unreleased] § Changed` — bold-label entry for the default-Content-Directory rule — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** a stand-alone bullet that a reader with no internal context can act on per `.claude/rules/changelog.md:48`

**Files:**

- `specs/npm-distribution.md` — adds the new Content Directory subsection (default + exclusion + subdirectory-mode rule); bumps version header to v0.2.0
- `website/src/content/docs/spec/npm-distribution.md` — mirror sync per Round 1 precedent at `CHANGELOG.md:35`
- `CHANGELOG.md` — `[Unreleased]` `### Changed` bullet
- `.ship/npm-distribution-spec/conformance/slice-6.sh` — new conformance script asserting that two independent reductions of a fixture tarball produce byte-equal canonical hashes when `moat.tarballContentRoot` is absent, and that introducing a `package.json` mutation between reductions does not change the hash

**Test cases:**

- Unit: `default-content-directory hashes tarball root minus package.json` — fixture tarball `t1` with files `a.md`, `b.js`, `package.json`; expected canonical hash MUST equal `sha256(<algorithm-of-{a.md, b.js}>)`; mutating `package.json` between two computations MUST NOT change the hash
- Unit: `subdirectory mode applies no exclusions` — fixture tarball `t2` with `moat.tarballContentRoot: "src"` and `src/package.json` present; expected canonical hash domain is `src/` contents including `src/package.json`
- Unit: `default-mode exclusion is path-anchored to tarball root` — fixture tarball `t3` with `pkg/package.json` (subdirectory copy at default mode); expected canonical hash domain INCLUDES `pkg/package.json` and EXCLUDES root-level `package.json` only
- Integration: `backfill produces same hash as publisher-driven flow` — given fixture tarball `t1`, the Registry-side backfill path (no Publisher cooperation) and the Publisher-driven path (where the Publisher computed the hash before packing) MUST produce byte-equal canonical hashes
- Conformance: `.ship/npm-distribution-spec/conformance/slice-6.sh` exits 0 on a fresh checkout and exits non-zero if any reduction-equality assertion fails

**Checkpoint:** `bash .ship/npm-distribution-spec/conformance/slice-6.sh` exits 0; `grep -c '## Content Directory' specs/npm-distribution.md` returns ≥ 1; `diff <(sed '1,/^---$/d' website/src/content/docs/spec/npm-distribution.md) specs/npm-distribution.md` exits 0; `grep -F 'v0.2.0' specs/npm-distribution.md` matches; the Round 1 conformance scripts (`slice-1.sh`..`slice-5.sh`) still exit 0.

### Slice 2: tarballContentRoot field-name realization with lexicon cross-reference

**Observable outcome:** Every occurrence of the JSON field in `specs/npm-distribution.md` reads `moat.tarballContentRoot` (no remaining `moat.contentDirectory`), the lexicon's Content Directory entry carries a one-line realization note pointing to the new field name, and the sub-spec's field-table row cross-references the lexicon entry rather than redefining the concept. A reader following the sub-spec to the lexicon and back encounters one canonical concept name and one canonical JSON field name, with the relationship between them stated explicitly.

**Interfaces introduced or modified:**

- `specs/npm-distribution.md § package.json moat block (normative)` field-table row — rename `moat.contentDirectory` → `moat.tarballContentRoot` — **Deps:** `in-process`
  - **Hides:** the prior collision between the JSON field name and the lexicon concept name
  - **Exposes:** a single canonical JSON field name; the row's Description column cross-references the `lexicon.md` Content Directory entry rather than redefining the concept; per the recommended option in design.md Question 3 the rename replaces the row outright with no historical note (Draft-status breaking change permitted by `moat-spec.md:14-16` and `:22`)
- `lexicon.md` Content Directory entry — gains a one-line realization note — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** "`tarballContentRoot` (in `package.json`) is one realization of this concept inside the npm Distribution Channel; the lexicon term Content Directory remains the source of truth"
- `CHANGELOG.md § [Unreleased] § Changed` — bold-label entry for the field rename — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** a stand-alone bullet stating the rename and that no migration scaffolding is provided (Draft-status; zero adopters per `moat-spec.md:22`)
- `website/src/content/docs/spec/npm-distribution.md` — byte-identical mirror update — **Deps:** `in-process`
  - **Hides:** Starlight front-matter divergence
  - **Exposes:** the renamed field on the website mirror

**Files:**

- `specs/npm-distribution.md` — field-table row rename; every `moat.contentDirectory` literal in JSON examples and prose is replaced with `moat.tarballContentRoot`
- `lexicon.md` — Content Directory entry gains the realization note
- `website/src/content/docs/spec/npm-distribution.md` — mirror sync
- `CHANGELOG.md` — `[Unreleased]` `### Changed` bullet

**Test cases:**

- Unit: `no-stale-field-name in canonical sub-spec` — `grep -c 'moat\.contentDirectory' specs/npm-distribution.md` MUST return 0
- Unit: `no-stale-field-name in website mirror` — `grep -c 'moat\.contentDirectory' website/src/content/docs/spec/npm-distribution.md` MUST return 0
- Unit: `lexicon realization note present` — the line containing "`tarballContentRoot`" inside the Content Directory entry of `lexicon.md` MUST exist and reference `package.json`
- Unit: `field-table row cross-references lexicon` — the Description column for `moat.tarballContentRoot` in `specs/npm-distribution.md` MUST contain a link or anchor to the lexicon's Content Directory entry rather than re-defining the concept
- Integration: `mirror byte-identity` — after stripping the Starlight front-matter, `website/src/content/docs/spec/npm-distribution.md` MUST be byte-identical to `specs/npm-distribution.md`

**Checkpoint:** `grep -F 'moat.contentDirectory' specs/npm-distribution.md website/src/content/docs/spec/npm-distribution.md` returns no matches; `grep -F 'tarballContentRoot' lexicon.md` returns ≥ 1 match inside the Content Directory entry; `diff <(sed '1,/^---$/d' website/src/content/docs/spec/npm-distribution.md) specs/npm-distribution.md` exits 0.

### Slice 3: Process-scoped revocation override with auditable expiry

**Observable outcome:** A Conforming Client that reads `MOAT_ALLOW_REVOKED` enforces three normative properties an external observer can verify: (a) the variable is read exactly once at process start (re-read mid-process is non-conformant); (b) `MOAT_ALLOW_REVOKED_REASON` is REQUIRED — a non-empty value is a hard prerequisite, the Client emits a structured error and refuses to honor the override if the reason is unset or empty; (c) each override entry is `<sha256-hex>:<RFC3339-timestamp>` and entries past their expiry are silently ignored (no warning, no log). On every override application, the Client emits a structured log event whose normative shape includes `package`, `content_hash`, `reason`, and `expires_at` (per design.md Question 1's recommended naming). The override is auditable from the log event alone.

**Interfaces introduced or modified:**

- `specs/npm-distribution.md § MOAT_ALLOW_REVOKED Operator Override (normative)` — section expansion replacing the Round 1 minimal form — **Deps:** `in-process`
  - **Hides:** the Round 1 silent-skip footgun where an operator could set the override and skip the reason
  - **Exposes:** four normative MUSTs — process-scope read-once; REQUIRED `MOAT_ALLOW_REVOKED_REASON` co-variable with hard-fail enforcement; per-entry encoded as `<sha256-hex>:<RFC3339-timestamp>`; structured override-applied log event with field names `package`, `content_hash`, `reason`, `expires_at`
- `CHANGELOG.md § [Unreleased] § Changed` — bold-label entry for the override hardening — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** a stand-alone bullet stating the new prerequisites and the structured-event field names
- `website/src/content/docs/spec/npm-distribution.md` — byte-identical mirror update — **Deps:** `in-process`
  - **Hides:** Starlight front-matter divergence
  - **Exposes:** the expanded section to website readers

**Files:**

- `specs/npm-distribution.md` — expanded `MOAT_ALLOW_REVOKED` section
- `website/src/content/docs/spec/npm-distribution.md` — mirror sync
- `CHANGELOG.md` — `[Unreleased]` `### Changed` bullet
- `.ship/npm-distribution-spec/conformance/slice-7.sh` — new conformance script asserting log-event field-name presence and the four normative MUSTs are visible in the spec body

**Test cases:**

- Unit: `override section names all four MUSTs` — `specs/npm-distribution.md` MUST contain literal text covering: process-scope read-once; REQUIRED reason co-variable; `<sha256-hex>:<RFC3339-timestamp>` encoding; structured override-applied event
- Unit: `log-event field names match design.md Q1 recommended option` — the spec MUST cite field names `package`, `content_hash`, `reason`, `expires_at`
- Unit: `expired entries silently ignored rule present` — the spec MUST state that entries past their RFC 3339 timestamp are treated as if absent (no warning, no log)
- Unit: `malformed-entry rule present` — the spec MUST state that override entries without the timestamp delimiter MUST be ignored as malformed (no permanent overrides)
- Integration: `mirror byte-identity` — `diff <(sed '1,/^---$/d' website/...) specs/...` exits 0
- Conformance: `.ship/npm-distribution-spec/conformance/slice-7.sh` greps for the four normative phrases and exits 0 if all match

**Checkpoint:** `bash .ship/npm-distribution-spec/conformance/slice-7.sh` exits 0; `grep -cE 'MOAT_ALLOW_REVOKED_REASON' specs/npm-distribution.md` returns ≥ 2 (definition + hard-fail rule); `grep -cE 'expires_at' specs/npm-distribution.md` returns ≥ 1; the Round 1 conformance scripts still exit 0.

### Slice 4: Cache-boundary materialization anchor

**Observable outcome:** The pre-materialization revocation MUST in `specs/npm-distribution.md` reads "before any byte of the tarball is written outside the package manager's content cache" verbatim, names the three sub-operations a Conforming Client may refuse at (resolve, fetch, unpack), and states that whichever sub-operation the Client chooses, no extracted bytes may land outside the cache. A reader of the sub-spec can map the cache-boundary concept onto a streaming installer (npm's `pacote`), a Plug'n'Play installer, and a content-addressable store (pnpm) without re-wording the MUST.

**Interfaces introduced or modified:**

- `specs/npm-distribution.md § Materialization Boundary (normative — MUST)` — replaces the Round 1 prose at `specs/npm-distribution.md:29` — **Deps:** `in-process`
  - **Hides:** the Round 1 ambiguity that left "before fetch" vs "before unpack" undecided
  - **Exposes:** the cache-boundary anchor verbatim, plus an informative-tagged paragraph naming `pacote`, Yarn Plug'n'Play, and the pnpm content-addressable store as the architectures the rule maps cleanly onto
- `CHANGELOG.md § [Unreleased] § Changed` — bold-label entry for the materialization-boundary rephrase — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** a stand-alone bullet describing the rephrase as a normative clarification (not a behavior change)
- `website/src/content/docs/spec/npm-distribution.md` — byte-identical mirror update — **Deps:** `in-process`
  - **Hides:** Starlight front-matter divergence
  - **Exposes:** the rephrased boundary on the website mirror

**Files:**

- `specs/npm-distribution.md` — section text at the existing materialization-boundary location is replaced (Round 1 prose at line 29 is overwritten)
- `website/src/content/docs/spec/npm-distribution.md` — mirror sync
- `CHANGELOG.md` — `[Unreleased]` `### Changed` bullet

**Test cases:**

- Unit: `cache-boundary anchor verbatim` — `specs/npm-distribution.md` MUST contain the literal phrase "before any byte of the tarball is written outside the package manager's content cache"
- Unit: `three sub-operations enumerated` — the section MUST name `resolve`, `fetch`, and `unpack` as the operations a Conforming Client may refuse at
- Unit: `no-bytes-outside-cache rule present` — the section MUST state that whichever operation the Client refuses at, no extracted bytes may land outside the cache
- Unit: `Round 1 prose at :29 superseded` — `grep` for any Round 1-specific phrasing the rephrase replaces MUST return 0
- Integration: `mirror byte-identity` — `diff <(sed '1,/^---$/d' website/...) specs/...` exits 0

**Checkpoint:** `grep -F "before any byte of the tarball is written outside the package manager's content cache" specs/npm-distribution.md` returns ≥ 1 match; `grep -cE 'resolve.*fetch.*unpack|fetch.*unpack' specs/npm-distribution.md` returns ≥ 1; the Round 1 conformance scripts still exit 0.

### Slice 5: Publisher identity disclosure via publisherSigning block

**Observable outcome:** The `package.json` `moat` schema's Publisher attestation moves out of `attestations[].bundle` (Round 1's inline-bundle form) into a top-level `publisherSigning` block with REQUIRED `issuer` and `subject` and OPTIONAL `rekorLogIndex`. The `attestations[]` array is preserved for the Registry role only. A Conforming Client receiving a published `package.json` validates the Rekor entry's signing identity matches `publisherSigning.{issuer, subject}` exactly, with `rekorLogIndex` used as a discovery accelerator only — when absent the Client falls back to a Rekor query keyed on the canonical Content Hash, filtered by the disclosed `{issuer, subject}`. The cross-channel symmetry with `moat-spec.md:790`'s `signing_profile` field is cited explicitly in the sub-spec body.

**Interfaces introduced or modified:**

- `specs/npm-distribution.md § package.json moat block (normative)` schema — Publisher-role section — **Deps:** `in-process`
  - **Hides:** the Round 1 inline-bundle approach that inflated `package.json` and duplicated a trust anchor already in Rekor
  - **Exposes:** `publisherSigning.issuer` REQUIRED; `publisherSigning.subject` REQUIRED; `publisherSigning.rekorLogIndex` OPTIONAL; the `attestations[]` array retained for Registry role only; the per-role cardinality (exactly one Publisher per package) enforced via JSON schema rather than the Round 1 "duplicate role is malformed" rule
- `specs/npm-distribution.md § Publisher Verification (normative)` — new normative MUSTs for Conforming Clients — **Deps:** `in-process`
  - **Hides:** the Round 1 underspec around what to do when the inline bundle was malformed or absent
  - **Exposes:** when `rekorLogIndex` is present, MUST fetch by index and MUST validate the entry's signing identity matches `publisherSigning.{issuer, subject}` exactly; when absent, MUST query Rekor by canonical Content Hash and MUST filter results by `{issuer, subject}`; the disclosed identity is the trust anchor, the log index is only a discovery accelerator
- `CHANGELOG.md § [Unreleased] § Changed` — bold-label entry for the schema change — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** a stand-alone bullet stating the schema-shape change and that this is a Draft-status breaking change with no migration scaffolding
- `website/src/content/docs/spec/npm-distribution.md` — byte-identical mirror update — **Deps:** `in-process`
  - **Hides:** Starlight front-matter divergence
  - **Exposes:** the relocated Publisher-role schema on the website mirror

**Files:**

- `specs/npm-distribution.md` — Publisher-role section of the `moat` block schema is rewritten; new Publisher Verification subsection added
- `website/src/content/docs/spec/npm-distribution.md` — mirror sync
- `CHANGELOG.md` — `[Unreleased]` `### Changed` bullet

**Test cases:**

- Unit: `publisherSigning fields present and required` — the field-table for `publisherSigning.issuer` and `publisherSigning.subject` MUST mark both REQUIRED; `publisherSigning.rekorLogIndex` MUST be OPTIONAL
- Unit: `attestations[] retained for Registry role only` — the `attestations[].bundle` Publisher-role row from Round 1 MUST NOT appear; the Registry-role `attestations[]` row MUST appear
- Unit: `cross-channel symmetry citation present` — the sub-spec body MUST cite `moat-spec.md` `signing_profile` (whether by anchored link or section reference)
- Unit: `Conforming Client verification MUSTs present` — the spec MUST contain MUSTs covering both the `rekorLogIndex` present and `rekorLogIndex` absent cases
- Integration: `mirror byte-identity` — `diff <(sed '1,/^---$/d' website/...) specs/...` exits 0

**Checkpoint:** `grep -cE 'publisherSigning\.(issuer|subject|rekorLogIndex)' specs/npm-distribution.md` returns ≥ 3; `grep -c 'attestations\[\].bundle' specs/npm-distribution.md` returns 0; `grep -F 'signing_profile' specs/npm-distribution.md` returns ≥ 1 match; the Round 1 conformance scripts still exit 0.

### Slice 6: Four-state provenance × MOAT disagreement table

**Observable outcome:** The npm Provenance section in `specs/npm-distribution.md` carries a four-row pipe table covering the Cartesian product of (npm provenance: present | absent) × (MOAT attestation: present | absent), per the recommended Option A in design.md Question 2. Each row names the cell, the Conforming Client display rule, and the Trust Tier impact. The section explicitly states that npm provenance and Trust Tier are orthogonal axes — a Conforming Client treats them as independent inputs.

**Interfaces introduced or modified:**

- `specs/npm-distribution.md § npm Provenance (informative)` — new four-row disagreement table — **Deps:** `in-process`
  - **Hides:** the Round 1 underspec where the provenance section did not enumerate the disagreement states
  - **Exposes:** four rows: `(both present, MOAT-only, provenance-only, neither)`; columns `(npm provenance, MOAT attestation, Conforming Client display, Trust Tier impact)`; the orthogonality statement that provenance and Trust Tier are independent axes
- `CHANGELOG.md § [Unreleased] § Changed` — bold-label entry for the four-state table — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** a stand-alone bullet stating the new informative section
- `website/src/content/docs/spec/npm-distribution.md` — byte-identical mirror update — **Deps:** `in-process`
  - **Hides:** Starlight front-matter divergence
  - **Exposes:** the new table on the website mirror

**Files:**

- `specs/npm-distribution.md` — four-row pipe table appended to the existing npm Provenance section (`specs/npm-distribution.md:107-115` per design.md decision B-2)
- `website/src/content/docs/spec/npm-distribution.md` — mirror sync
- `CHANGELOG.md` — `[Unreleased]` `### Changed` bullet

**Test cases:**

- Unit: `four-row pipe table present` — the npm Provenance section MUST contain a Markdown pipe table with at least four data rows
- Unit: `all four states named` — the table rows MUST cover all four states: both present, MOAT-only, provenance-only, neither
- Unit: `orthogonality statement present` — the section MUST state that npm provenance and Trust Tier are orthogonal axes
- Integration: `mirror byte-identity` — `diff <(sed '1,/^---$/d' website/...) specs/...` exits 0

**Checkpoint:** `awk '/## npm Provenance/,/^## /' specs/npm-distribution.md | grep -c '^|' ` returns ≥ 5 (header row + separator + four data rows); `grep -F 'orthogonal' specs/npm-distribution.md` returns ≥ 1 match; the Round 1 conformance scripts still exit 0.

### Slice 7: End-to-end npm Publisher reference workflow

**Observable outcome:** A Publisher copies `reference/moat-npm-publisher.yml` into their repo's `.github/workflows/` and gets a working flow from `npm pack` through `npm publish` whose canonical Content Hash is byte-stable across the log-index round-trip. The seven-step pipeline is observable end-to-end: `npm pack` produces tarball v1; the canonical hash is computed using Slice 1's exclusion rule; Sigstore signs the canonical Attestation Payload; the Rekor entry is pushed; the log index is written back into `package.json`; `npm pack` produces tarball v2; `npm publish` ships v2. The two-pack design's correctness (canonical hash stable across the `package.json` mutation) is the consequence of Slice 1's `package.json` exclusion. The `moat-spec.md:9` Sub-specs line cites `specs/npm-distribution.md` and `.claude/rules/changelog.md:40` cites the post-reorg path so a reader of the core spec discovers the new sub-spec and a CHANGELOG-rule reader sees a working anchor.

**Interfaces introduced or modified:**

- `reference/moat-npm-publisher.yml` — new file — **Deps:** `local-substitutable`
  - **Hides:** the Sigstore install boilerplate, the `npm pack` two-pack discipline, the canonical-hash computation step, and the Rekor push mechanics
  - **Exposes:** a single-file YAML a Publisher copies verbatim into `.github/workflows/`; mirrors `reference/moat-publisher.yml:1-80`'s structure exactly (same `permissions` block, same `sigstore/cosign-installer` step shape, same job/step layout); triggered on release tag push or `workflow_dispatch`
  - **Substitution note:** a non-GHA Publisher tooling alternative is explicitly out of scope (see Out of Scope); `local-substitutable` here means the YAML is one realization of the canonical "compute hash, sign payload, log to Rekor" flow over the npm channel — a Publisher could write an equivalent script in another runner without changing the protocol
- `moat-spec.md` line 9 — Sub-specs line edit — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** `specs/npm-distribution.md` cited in the Sub-specs comma-separated list so a core-spec reader discovers the new sub-spec
- `.claude/rules/changelog.md` line 40 — example-anchor path edit — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** the post-reorg path `specs/github/publisher-action.md` (replacing the pre-reorg `specs/publisher-action.md`); per `.claude/rules/changelog.md:21`'s tooling-only exclusion no CHANGELOG entry is required for this file
- `specs/npm-distribution.md § Reference Implementations` — bullet citing `reference/moat-npm-publisher.yml` — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** a discoverable pointer from the sub-spec body to the reference workflow, mirroring `moat-spec.md:681`'s pattern of citing `reference/moat-publisher.yml` from `specs/github/publisher-action.md`
- `CHANGELOG.md § [Unreleased] § Added` — bold-label entry for the new reference workflow — **Deps:** `in-process`
  - **Hides:** none
  - **Exposes:** a stand-alone bullet stating that `reference/moat-npm-publisher.yml` ships as the npm-channel adoption template; per design.md's reference-content classification this IS a spec-surface artifact requiring a CHANGELOG entry, not a tooling-only one
- `website/src/content/docs/spec/npm-distribution.md` — byte-identical mirror update — **Deps:** `in-process`
  - **Hides:** Starlight front-matter divergence
  - **Exposes:** the Reference Implementations bullet on the website mirror

**Files:**

- `reference/moat-npm-publisher.yml` — new file; seven-step GHA workflow mirroring `reference/moat-publisher.yml:1-80`
- `specs/npm-distribution.md` — Reference Implementations bullet added
- `website/src/content/docs/spec/npm-distribution.md` — mirror sync
- `moat-spec.md` — line 9 Sub-specs line edit
- `.claude/rules/changelog.md` — line 40 path edit
- `CHANGELOG.md` — `[Unreleased]` `### Added` bullet
- `.ship/npm-distribution-spec/conformance/slice-8.sh` — new conformance script asserting that a fixture run of the seven-step flow produces a canonical hash that is byte-equal between tarball v1 and tarball v2 (the two-pack invariant)

**Test cases:**

- Unit: `seven-step structure present` — `reference/moat-npm-publisher.yml` MUST declare exactly seven named steps in the order: `npm pack` v1, compute canonical hash, Sigstore sign, push to Rekor, write log index back to `package.json`, `npm pack` v2, `npm publish`
- Unit: `permissions block matches reference precedent` — the `permissions:` block MUST contain `id-token: write` and `contents: write` (per `reference/moat-publisher.yml:1-80`)
- Unit: `Sigstore installer step present` — the workflow MUST `uses: sigstore/cosign-installer@...`
- Unit: `triggered on release tag or workflow_dispatch` — the `on:` block MUST cover release tag push and manual dispatch
- Unit: `core-spec sub-specs line cites new file` — `moat-spec.md:9` MUST contain the literal `specs/npm-distribution.md`
- Unit: `changelog rule cites post-reorg path` — `.claude/rules/changelog.md:40` MUST cite `specs/github/publisher-action.md` (post-reorg) and MUST NOT cite the pre-reorg path
- Integration: `two-pack canonical hash stability` — given a fixture source repo, running steps 1–6 produces tarball v1 and tarball v2; the canonical hash computed by Slice 1's rule MUST be byte-equal between the two tarballs (because `package.json` is excluded under default mode)
- Integration: `mirror byte-identity` — `diff <(sed '1,/^---$/d' website/...) specs/...` exits 0
- Conformance: `.ship/npm-distribution-spec/conformance/slice-8.sh` runs the two-pack invariant assertion against a fixture and exits 0

**Checkpoint:** `bash .ship/npm-distribution-spec/conformance/slice-8.sh` exits 0; `test -f reference/moat-npm-publisher.yml` succeeds; `grep -F 'specs/npm-distribution.md' moat-spec.md | head -1` matches at line 9; `grep -F 'specs/github/publisher-action.md' .claude/rules/changelog.md` matches at line 40 and `grep -F 'specs/publisher-action.md' .claude/rules/changelog.md` returns no match (the pre-reorg path is gone); the Round 1 conformance scripts (`slice-1.sh`..`slice-5.sh`) still exit 0; new conformance scripts (`slice-6.sh`..`slice-8.sh`) all exit 0.

## Acceptance

- `specs/npm-distribution.md` is at v0.2.0 Draft and contains: a default Content Directory rule (tarball root with `package.json` exclusion); the renamed `moat.tarballContentRoot` field with a lexicon cross-reference; the expanded `MOAT_ALLOW_REVOKED` section with reason co-variable, RFC 3339 expiry, and structured override-applied event; the cache-boundary materialization anchor verbatim; the `publisherSigning` block with REQUIRED `issuer`/`subject` and OPTIONAL `rekorLogIndex` plus Conforming-Client verification MUSTs; the four-state provenance × MOAT disagreement table with orthogonality statement; and a Reference Implementations bullet citing `reference/moat-npm-publisher.yml`. (Slices 1–7.)
- `lexicon.md`'s Content Directory entry carries a one-line note that `tarballContentRoot` (in `package.json`) is one realization of the concept. (Slice 2.)
- `reference/moat-npm-publisher.yml` exists, mirrors `reference/moat-publisher.yml:1-80`'s structure, declares the seven steps in order, and produces canonical-hash-stable two-pack behavior under fixture conditions. (Slice 7.)
- `moat-spec.md` line 9's Sub-specs line cites `specs/npm-distribution.md`. (Slice 7.)
- `.claude/rules/changelog.md` line 40 cites `specs/github/publisher-action.md` and does not cite the pre-reorg path. (Slice 7.)
- `CHANGELOG.md` `[Unreleased]` carries `### Changed` bullets for the default-Content-Directory rule, the field rename, the `MOAT_ALLOW_REVOKED` hardening, the materialization-boundary rephrase, the `publisherSigning` schema change, and the four-state disagreement table; and an `### Added` bullet for the new reference workflow. Each bullet is in the bold-label form per `.claude/rules/changelog.md:48`, contains no panel/persona/finding-ID language per `.claude/rules/changelog.md:23-32`, and stands alone for a reader with zero internal context per `.claude/rules/changelog.md:46`. (Slices 1–7.)
- `website/src/content/docs/spec/npm-distribution.md` is byte-identical to `specs/npm-distribution.md` after stripping Starlight front-matter, on every commit that touches the canonical sub-spec. (Slices 1–7.)
- The Round 1 conformance scripts `.ship/npm-distribution-spec/conformance/slice-1.sh` through `slice-5.sh` continue to exit 0 on a fresh checkout (no Round 1 normative-surface regression).
- New conformance scripts `slice-6.sh` (default-Content-Directory hashing equality), `slice-7.sh` (override-event log shape and four-MUSTs presence), and `slice-8.sh` (two-pack canonical-hash stability) exit 0 on a fresh checkout.
- The four MOAT design tests (`CLAUDE.md:121-127`) hold for the override section: day-one (operator can override on the day the spec ships), copy-survival (override semantics survive being copied to another Conforming Client implementation because the structured event is the audit anchor), works-fine-without-it (the hard-fail on missing reason closes the silent-skip path), enforcement (the structured event provides the detection mechanism — there is no "trust that operators will write good logs").
- ADRs 0005–0009 (auto-drafted from this design's Disambiguation blocks) flip from Proposed to Accepted via the ship-adr-handler hook on the slice commits that land their respective decisions; this is hook-managed and not a structure-level acceptance criterion.

## Out of Scope

- **Layering rule + GitHub-ism extraction in `moat-spec.md` / `specs/moat-verify.md`** — deferred to a separate ship.
- **Aggregator UI Trust Tier strings + visual guidance** — deferred to a separate ship.
- **Standalone CLI for non-GHA npm Publishers** — `reference/moat-npm-publisher.yml` is GitHub-Actions-shaped only; non-GHA reference Publisher tooling is a future concern.
- **Multi-provider OIDC examples** — the reference workflow uses GitHub Actions OIDC only; OIDC providers other than GitHub are not enumerated in this ship.
- **Enumerating npm-injected metadata files beyond `package.json`** — the exclusion list is fixed at exactly `package.json`; if future npm-injected files (e.g., `.npmrc`-injected fields, metadata blocks added by registry middleware) need exclusion, they require their own sub-spec amendment.
- **npm Registry first-class metadata field** — proposing a top-level npm Registry metadata field (e.g., `dist.attestations[].moatAttestation`) outside `package.json` is out of scope; this ship uses `package.json` only.
- **Other registry transports** — PyPI, Cargo, Maven, container registries; each needs its own sub-spec.
- **Runtime gating of execution** — outside MOAT's protocol boundary; the materialization-boundary anchor is the protocol's last word on revocation.
