# Design Discussion: npm-distribution-spec

## Summary

**Current state:** MOAT's normative Distribution Channel is a Registry Manifest fetched over HTTPS with per-item Rekor verification — only the GitHub-Actions-based publisher/registry workflow is specified, and the GitHub-specific sub-specs sit at the same directory level as the transport-agnostic ones.
**Desired state:** A new `specs/npm-distribution.md` defines how the transport-agnostic core protocol is realized over the npm Registry, and the GitHub-specific sub-specs live under `specs/github/` so the directory layout reflects the transport-agnostic core / transport-specific extension split.
**End state (narrative):** A Publisher distributing a Content Item via npm declares MOAT attestation in a `package.json` block whose hash domain is the Content Directory inside the Distribution Tarball; a Conforming Client resolving or installing that package can recognize Verified, Unsigned, and Revoked Trust Tiers at the materialization boundary; a backfill-only Registry can attest pre-existing npm packages without Publisher cooperation; and a spec reader sees `specs/github/publisher-action.md`, `specs/github/registry-action.md`, and the transport-agnostic `specs/moat-verify.md` arranged so the protocol/platform separation is visible at a glance.

## Research questions answered

- Q1 — House style of existing sub-specs
- Q2 — Cross-references to GitHub-specific sub-specs
- Q3 — Manifest content-entry schema
- Q4 — Revocation machinery
- Q5 — Content hash algorithm input domain
- Q6 — Four MOAT design tests
- Q7 — CHANGELOG conventions

## Patterns to Follow

### Pattern: Sub-spec file-level metadata header

**Source:** `specs/publisher-action.md:1-9`

**Snippet:**
```markdown
# Publisher Action Specification

**Version:** 0.2.0 (Draft)
**Requires:** moat-spec.md ≥ 0.5.0
**Part of:** [MOAT Specification](../moat-spec.md)

> The Publisher Action is the primary adoption mechanism for MOAT, ...

---
```

**Why it applies here:** `specs/npm-distribution.md` is a peer sub-spec; it MUST open with the same header shape (H1 "<Name> Specification", `Version` / `Requires` / `Part of` lines, blockquote one-liner, trailing `---`) so it reads as a sibling artifact and so the website mirror under `website/src/content/docs/spec/` can ingest it without house-style drift.

### Pattern: Heading-suffix normative status labels

**Source:** `specs/publisher-action.md:25-194`

**Snippet:**
```markdown
## Undiscovered Content Detection (normative)
## Actionable Error Messages (normative — SHOULD)
## Webhook (optional)
### Informed Consent Limitation (informative)
```

**Why it applies here:** Each section in `specs/npm-distribution.md` whose primary content is RFC 2119-bearing should carry the matching parenthetical (`(normative)`, `(normative — MUST)`, `(normative — SHOULD)`, `(informative)`, `(optional)`). Materialization-boundary MUSTs land in `(normative — MUST)` sections; the npm-provenance discussion lands in `(informative)` because D4 is observed-only, not normative.

### Pattern: Bold-label inline normative qualifiers

**Source:** `specs/publisher-action.md:29, 64, 72`; `specs/registry-action.md:104`

**Snippet:**
```markdown
**Detection rule (normative — MUST):** If a top-level directory ...
**Unknown-file warning (normative — MUST):** ...
**Attestation exclusion (normative — MUST):** ...
**Hash mismatch (normative):** ...
```

**Why it applies here:** Materialization-boundary requirements (D2) and revocation hard-block rules (D6) read as bold-label inline qualifiers, not as section-level statements. This style colocates the requirement with the surrounding context — important for the materialization vs runtime distinction, where adjacent paragraphs say very different things about MUSTs.

### Pattern: Field-definition table — 3-column `Field | Required | Description`

**Source:** `specs/registry-action.md:52-63`; `moat-spec.md:766-797`

**Snippet:**
```markdown
| Field | Required | Description |
|-------|----------|-------------|
| `revocations[].reason` | REQUIRED | One of: `malicious`, `compromised`, `deprecated`, `policy_violation`. |
| `revocations[].details_url` | REQUIRED for registry / OPTIONAL for publisher | URL to public revocation details. |
| `revocations[].source` | OPTIONAL | Revocation source: `"registry"` or `"publisher"`. ... |
```

**Why it applies here:** The `package.json` `moat` block field schema (D3 — single block with MUST/SHOULD/MAY split) and the `attestations[]` entry schema (D7 — role-discriminated array) are field-definition tables. Use the same 3-column shape with RFC 2119 keywords as cell values in the `Required` column. The "REQUIRED for X / OPTIONAL for Y" cell form is precedent for backfill-friendly conditional requirements (publisher-only / registry-only / both / neither).

### Pattern: Fenced JSON examples with one-line lead-in

**Source:** `specs/publisher-action.md:100-141`

**Snippet:**
```markdown
The canonical attestation payload is:

```json
{"_version":1,"content_hash":"sha256:..."}
```

The `moat-attestation.json` file produced on the `moat-attestation` branch ...

```json
{
  "_version": 1,
  "source_uri": "https://github.com/owner/repo",
  "attested_at": "...",
  "items": [ ... ],
  "revocations": []
}
```
```

**Why it applies here:** The worked example required by the ticket (a `package.json` `moat` block with a populated `attestations: [...]` array) follows this introduce-then-fence rhythm. Each JSON example gets one prose sentence describing what it shows, then a fenced block — never bare JSON dumps.

### Pattern: Closing `## Scope` section

**Source:** `specs/publisher-action.md:248-251`; `specs/registry-action.md:214-217`

**Snippet:**
```markdown
## Scope

**Current version:** Adoption mechanism for the Publisher Action; reference template at `reference/moat-publisher.yml`.

**Planned future version:** ...
```

**Why it applies here:** The npm sub-spec closes the same way: a `## Scope` section with bold-prefixed `**Current version:**` and `**Planned future version:**` one-liners. "Current version" enumerates what the sub-spec DOES define (Content Directory hash domain, materialization-boundary MUSTs, role-discriminated attestations array); "Planned future version" reserves room for things the concept names as out-of-scope but plausibly-future (other registry transports, runtime gating) without committing to them.

### Pattern: Canonical Attestation Payload as the signed unit

**Source:** `moat-spec.md:1020-1071`

**Snippet:**
```json
{"_version":1,"content_hash":"sha256:<hex>"}
```

**Why it applies here:** The canonical Attestation Payload is byte-identical for Publisher and Registry signers (lexicon: "Byte-identical for a given content hash regardless of who signs"). The npm sub-spec's role-discriminated `attestations[]` array MUST NOT redefine the signed payload — each entry, whether `role: "publisher"` or `role: "registry"`, signs this exact payload. Per-role differences belong in the envelope around the signature (identity, bundle metadata, role discriminator), not in the signed bytes.

### Pattern: Content Hash input domain — directory walk with NFC paths

**Source:** `reference/moat_hash.py:166-198`

**Snippet:**
```python
def content_hash(directory: str | Path) -> str:
    root = Path(directory)
    entries: list[tuple[str, str]] = []
    for path in root.rglob("*"):
        if any(part in VCS_DIRS for part in path.parts): continue
        if path.parent == root and path.name in EXCLUDED_FILES: continue
        if path.is_symlink(): raise ValueError(...)
        if not path.is_file(): continue
        rel = unicodedata.normalize("NFC", path.relative_to(root).as_posix())
        entries.append((rel, file_hash(path)))
    entries.sort(key=lambda e: e[0].encode("utf-8"))
    manifest = "".join(f"{h}  {p}\n" for p, h in entries).encode("utf-8")
    return "sha256:" + hashlib.sha256(manifest).hexdigest()
```

**Why it applies here:** The hash domain (D5) binds to the Content Directory inside the published tarball. The npm sub-spec MUST refer normatively to `reference/moat_hash.py` and its test vectors — it MUST NOT redefine the algorithm. The sub-spec's job is to declare *which* directory inside the tarball is the input (per the Q1 field-name decision below) and to confirm that the algorithm operates over the unpacked tarball contents identically to how it operates over a source-repo content directory.

### Pattern: Lockfile `revoked_hashes` persistence

**Source:** `moat-spec.md:855, 663-665`

**Snippet:**
```markdown
| `revoked_hashes` | REQUIRED | Array of hard-blocked content hash strings; empty array if none. |

`revoked_hashes` entries MUST NOT be silently removed. Clearing a revoked hash
requires deliberate End User action. ... When a client has previously recorded
a revocation in its lockfile `revoked_hashes` array and that revocation entry
subsequently disappears from the registry manifest (due to pruning), the
lockfile entry persists. The hard-block continues.
```

**Why it applies here:** The npm sub-spec's revocation contract (D6) inherits this persistence model unchanged. The sub-spec MUST clarify that `revoked_hashes` in a Conforming Client's Lockfile is keyed by Content Hash, not by npm package name + version, so a republished package whose Content Directory matches a revoked hash remains blocked. The Q2 escape-hatch design is the only sanctioned override path.

### Pattern: Reason-code enum with forward-compat clause

**Source:** `moat-spec.md:614-615, 794`

**Snippet:**
```markdown
Reason values (informational only — they do NOT determine client behavior):
`malicious`, `compromised`, `deprecated`, `policy_violation`.
Unknown future reason values MUST be accepted without error.
```

**Why it applies here:** D6 settles that npm revocation reason codes inherit the core enum unchanged. The sub-spec MUST cite this enum by reference rather than redefining it, and MUST repeat the "Unknown future reason values MUST be accepted without error" clause so an npm-aware Conforming Client implementer reading the sub-spec in isolation does not accidentally enforce a closed enum.

### Pattern: Tombstone permanence for pruned revocations

**Source:** `moat-spec.md:665`

**Snippet:**
```markdown
Tombstone rule (normative for Registry Action): Registries MUST NOT re-list a
content item ... if a revocation entry for that item's content_hash has been
pruned from the revocations array. ... a `revocation-tombstones.json` file in
the `moat-registry` branch alongside the manifest. ... appended to (never
shrunk) when revocations are pruned.
```

**Why it applies here:** Tombstones are a property of the Registry's published artifacts (the `moat-registry` branch / Registry Manifest), not of the npm Distribution Channel. The npm sub-spec MUST state that tombstoning is a Registry concern carried in the upstream Registry Manifest and that an npm-aware Conforming Client respects tombstones via the Registry Manifest, not via npm package metadata — npm tarballs are immutable but a republished tarball with a clean version number could otherwise re-introduce a tombstoned hash.

### Pattern: Manifest content-entry schema and `(name, type)` uniqueness

**Source:** `moat-spec.md:766-807`

**Snippet:**
```markdown
content[].name              REQUIRED  Canonical identifier ...
content[].type              REQUIRED  One of: skill, agent, rules, command
content[].content_hash      REQUIRED  <algorithm>:<hex> — normative identity
content[].source_uri        REQUIRED  Source repository URI
content[].rekor_log_index   REQUIRED for Signed + Dual-Attested  Integer index ...
content[].signing_profile   REQUIRED for Dual-Attested  ...

content[].name + content[].type MUST be unique within a single manifest.
```

**Why it applies here:** When a Registry attests an npm-distributed Content Item, the resulting manifest entry uses this exact schema. The npm sub-spec MUST clarify how `source_uri` is populated for npm-only items (Q4 territory: a backfill-only Registry attestation where no Source Repository is known) and MUST preserve the `(name, type)` uniqueness invariant — a single npm package containing two content items of the same type is malformed, just as a source repo with two same-typed items is malformed.

### Pattern: CHANGELOG `[Unreleased]` entry under Keep-a-Changelog sections

**Source:** `.claude/rules/changelog.md:10-21, 27-30, 43-48`

**Snippet:**
```markdown
## [Unreleased]

Breaking change: ...

### Added
- **specs/npm-distribution.md** — new sub-spec describing the npm Distribution Channel ...

### Changed
- **specs/github/publisher-action.md** — moved from `specs/publisher-action.md`; no normative change.
- **specs/github/registry-action.md** — moved from `specs/registry-action.md`; no normative change.
```

**Why it applies here:** Both the new sub-spec and the directory move are spec edits and MUST be logged under `[Unreleased]` in `CHANGELOG.md` in the same commit. The bold-label form is required; persona/finding-ID/panel/count language is forbidden. Editorial-only moves get the explicit "no normative change" phrase.

### Disambiguation: Hash domain — Tarball Content Directory vs Source-Repo Content Directory vs Dual

**Chosen:** Tarball Content Directory (`reference/moat_hash.py:166-198` applied to the unpacked `.tgz`)
**Considered:** Source-Repo Content Directory (the directory at `source_uri`); Dual hashes (both source-repo and tarball recorded)
**Why:** The npm Distribution Channel materializes content from a tarball, not from a source repo. A Conforming Client only ever has the tarball at install time — it does not (and the protocol does not require it to) clone the source repo. Hashing the source repo would force every install to perform an out-of-band fetch the npm ecosystem does not perform, fail copy-survival (a tarball copied to a different repo cannot reproduce the source-repo hash), and fail the day-one test (existing npm packages have no published source-repo hash). Dual hashes double the schema surface and the ways a Publisher can produce mismatching attestations without buying meaningful trust beyond what the lone tarball hash already provides — the source repo's contribution is captured by `source_uri` plus the Publisher Rekor entry's signing identity, which already binds the tarball back to its origin. The Tarball Content Directory hash is also the only domain a backfill-only Registry can compute: it has the tarball, it does not have privileged access to the Publisher's source layout.
**Consequences:** A Publisher whose source-repo content directory is identical byte-for-byte to the tarball Content Directory (after npm's `files`/`.npmignore` filtering) will see the same Content Hash on both channels, which is the intended cross-channel identity. A Publisher whose npm build step transforms files (TypeScript compilation, bundling) will produce a different Content Hash on npm than in the source repo, and the npm sub-spec MUST acknowledge this — the tarball hash is the npm-channel identity, distinct from the source-channel identity. The hashing algorithm itself (the `reference/moat_hash.py` walk, NFC normalization, exclusion list) is unchanged; only the input directory differs. Tombstones and `revoked_hashes` keyed by Content Hash continue to work because the hash domain is a property of the input bytes, not of the channel — once a tarball hash is revoked, republishing identical bytes under a new version yields the same hash and remains blocked.

### Disambiguation: Attestation array shape — Role-discriminated array vs Separate slots vs Provenance enum

**Chosen:** Role-discriminated `attestations: [...]` array (each entry carries `role: "publisher" | "registry"`)
**Considered:** Separate top-level slots (`moat.publisher_attestation`, `moat.registry_attestation`); a `provenance: { type: "publisher" | "registry" | "both" | "neither" }` enum with mode-specific payload
**Why:** Backfill is a load-bearing concept of the npm sub-spec — a Registry can attest an existing npm package without Publisher cooperation, and a Publisher can attest without a Registry having indexed them yet. Four states must be representable: publisher-only, registry-only, both, neither. Separate slots represent both-and-neither cleanly but force an asymmetric schema (the consumer reads two different field names for two attestations of the same canonical payload); they also make it awkward to ever add a third role. A provenance enum compresses the four states into one tag but loses the ability to carry both attestations side-by-side and forces every reader to branch on the enum before they can find the data. A role-discriminated array is symmetric (both entries carry the same shape modulo the discriminator), grows naturally if a third role is ever needed, and represents all four states with the array's natural cardinality (length 0 / 1 / 2). It also matches the Registry Manifest's existing precedent of using arrays with role-bearing fields — `revocations[].source: "registry" | "publisher"` (`moat-spec.md:792-796`) and the per-item Rekor-entry-vs-signing_profile pairing (`moat-spec.md:786, 790`).
**Consequences:** A Conforming Client reading the `package.json` `moat` block walks `attestations[]` and, for each entry, dispatches on `role`. A length-zero array represents the "neither" state explicitly — the Publisher has reserved the `moat` block (declaring intent to participate) but no attestation is yet present; this is a Day-One legitimate state, not an error. Tooling that wants to find "the publisher attestation" performs a single-pass filter rather than a field lookup. The schema MUST forbid duplicate roles within one array (two entries with `role: "publisher"` is malformed) — the analog of the manifest's `(name, type)` uniqueness constraint. Adding a future role (e.g., a third-party scanner) is a schema-additive change rather than a structural rewrite. A Publisher attestation in this array points at the same canonical Attestation Payload signed by the Publisher Action — the npm sub-spec MUST NOT introduce a second canonical payload format.

### Disambiguation: Revocation framing — Pre/post-materialization vs Resolve/install/activation trichotomy

**Chosen:** Pre-materialization vs post-materialization, with MUSTs anchored at the materialization boundary
**Considered:** A three-phase trichotomy (resolve / install / activation) with separate normative obligations at each phase
**Why:** MOAT's protocol boundary stops at the install step — once content is on disk, MOAT is done (CLAUDE.md "What 'Conforming Client' Means"). A trichotomy that names "activation" as a normative phase implicitly extends MOAT into AI Agent Runtime territory: it suggests there is a MUST to enforce at activation time, which the protocol cannot enforce because activation happens inside Claude Code / Cursor / Windsurf and friends, not inside a Conforming Client. A pre/post-materialization split places the boundary exactly where the protocol's authority ends. Pre-materialization (resolve, fetch, unpack) is where a Conforming Client MUST refuse a revoked hash; post-materialization (file exists on disk, AI Agent Runtime may or may not load it) is where the protocol MAY observe but MUST NOT mandate. The trichotomy also fails the enforcement test: there is no enforcement mechanism a Conforming Client can apply at "activation" because the Conforming Client has finished its job by then.
**Consequences:** The sub-spec's normative MUSTs land cleanly: pre-materialization checks (resolve-time logging when a revoked hash is skipped per D6, install-time hard-block per the lockfile `revoked_hashes` model) carry MUST/MUST NOT; post-materialization is `(informative)` and explicitly says "out of MOAT's protocol boundary." This matches the existing core spec — `moat-spec.md:635` ("MUST be added to revoked_hashes") and `moat-spec.md:663` ("hard-block continues") both fire at install time, not at runtime. Implementers writing an npm-aware Conforming Client get a single clear question to answer ("am I about to materialize this hash on disk?") rather than three overlapping ones. The `MOAT_ALLOW_REVOKED` escape hatch (Q2 below) lives entirely in the pre-materialization side because that is where the block is enforced. AI Agent Runtimes that want to apply runtime gating MAY do so as a separate concern, and the sub-spec is silent about how — that is correct, because that is a different protocol than MOAT.

### Disambiguation: npm provenance integration — Observed vs Required vs Tier-elevating

**Chosen:** Observed-when-present, recommended-but-not-required, orthogonal to MOAT trust tiers (D4)
**Considered:** Required (MUST be present and valid for the Verified label); Tier-elevating (presence promotes a Signed item toward Dual-Attested or a higher npm-only tier)
**Why:** npm provenance and MOAT solve adjacent but distinct problems. npm provenance attests **build integrity** — that the artifact at `registry.npmjs.org` was produced by a particular CI workflow from a particular source commit. MOAT attests **content review** — that an attested party (Publisher and/or Registry) signed off on the canonical attestation payload `{"_version":1,"content_hash":"sha256:..."}`. Treating npm provenance as a MOAT requirement would couple MOAT to a particular registry's build-integrity feature, breaking the transport-agnostic core / transport-specific extension split this very directory move is meant to clarify. Treating npm provenance as tier-elevating would invent a fourth Trust Tier (or worse, a hidden modifier on existing tiers) that the lexicon and core spec do not authorize, fragmenting the cross-channel meaning of "Dual-Attested" and "Signed". Observing it as corroborating evidence (the sub-spec MAY recommend that Conforming Clients surface npm provenance presence to End Users alongside the Trust Tier label) gives users a richer picture without polluting the protocol semantics.
**Consequences:** The Trust Tier values published in the Registry Manifest (`Dual-Attested`, `Signed`, `Unsigned`) carry the same meaning whether the Distribution Channel is GitHub or npm. An npm package with valid npm provenance and no MOAT attestation is `Unsigned` from MOAT's perspective — it has the npm-provenance corroborating signal but no content-review attestation. An npm package with a Registry MOAT attestation but no npm provenance is `Signed` and installable; the absence of npm provenance does not gate it. Conforming Clients MAY expose npm provenance presence in their UI as a separate row from the Trust Tier; they MUST NOT use it to compute or override the Trust Tier. Future registry transports (PyPI, Cargo) inherit this same orthogonality principle: build-integrity primitives in those ecosystems are observed-when-present, not required, not tier-elevating.

## Design Questions

1. **What is the `package.json` field name for the Content Directory?**
   - A) `moat.contentDirectory` — full lexicon name in camelCase; explicit and unambiguous against npm's `files` / `directories` fields.
   - B) `moat.path` — short and idiomatic for `package.json`, but generic; "path" has many meanings inside `package.json` already (e.g., the Node `path` module's name; the `paths` field in `tsconfig.json`).
   - C) `moat.dir` — short; aligns with `directories` plural already in `package.json`, but ambiguous (which directory?).
   - **Recommended:** A — the lexicon defines **Content Directory** as the canonical term, and the term verbatim in the field name is the cheapest way to keep `package.json` readers in MOAT vocabulary. The four-character cost over `moat.path` is rounding error in a `package.json`, and the disambiguation against npm's existing `path`/`paths`/`directories` fields is real.

2. **What is the form of the `MOAT_ALLOW_REVOKED` escape hatch (D6)?**
   - A) Hash-list env var — `MOAT_ALLOW_REVOKED=sha256:abc...,sha256:def...` (comma-separated content hashes); the override is scoped per-hash.
   - B) Boolean env var — `MOAT_ALLOW_REVOKED=1` (any truthy value disables all revocation hard-blocks for the invocation).
   - C) File-path env var — `MOAT_ALLOW_REVOKED=/path/to/allowlist.txt` pointing at a newline-delimited list of allowed hashes.
   - D) Lockfile-only — no env var; an End User must hand-edit a `revocation_overrides[]` field in the Lockfile.
   - **Recommended:** A — per-hash scoping satisfies the enforcement question (a global "allow all revoked" flag is a known footgun in npm's `--force` and pip's `--break-system-packages` and gets used habitually); env-var ergonomics match how operators reach for one-off overrides during incident response without committing a Lockfile change. Hand-edit-only (D) is too high-friction for the legitimate use case (an operator deliberately accepting a deprecated hash they've reviewed); a boolean (B) is too low-friction for the dangerous case.

3. **What does each `attestations[]` entry carry — full Cosign Bundle, just a Rekor reference, or both?**
   - A) Full Cosign Bundle inline (Sigstore protobuf bundle v0.3, base64-encoded inside `attestations[].bundle`) — self-contained, verifiable offline, but each entry can be tens of KB and bloats `package.json`.
   - B) Rekor reference only (`attestations[].rekor_log_index` plus enough identity to fetch the bundle) — keeps `package.json` small but every install must hit Rekor at materialization time, which fails offline-install scenarios.
   - C) Both — `bundle` is REQUIRED, `rekor_log_index` is REQUIRED for cross-checking; bundle is the trust anchor, the index is the cheap lookup.
   - **Recommended:** C — the lockfile schema already stores the full bundle verbatim (lexicon: "Stored verbatim in the lockfile as `attestation_bundle`"); `package.json` follows the same model so a Conforming Client can verify offline directly from the tarball it already has, while `rekor_log_index` lets tooling cross-check against the public log without parsing the bundle. The size cost is bounded (one bundle per role, max two roles); npm packages routinely carry larger metadata.

4. **Does a backfill-only Registry attestation use the same `registry_signing_profile` as a normal Registry signature, or a distinct `registry_backfill_signing_profile`?**
   - A) Same `registry_signing_profile` — a backfill attestation is just a Registry attestation against an npm-distributed Content Item with no Publisher attestation; the signing identity is the Registry's CI workflow either way.
   - B) Distinct `registry_backfill_signing_profile` — the backfill case carries different operational risk (the Registry asserts content authenticity without a Publisher counter-signature) and deserves a separate identity slot a Conforming Client can pin or warn on.
   - **Recommended:** A — the operational difference between "backfill" and "normal" Registry attestation is a property of the Content Item's state (publisher-attested or not), not of the Registry's signing identity. The Registry signs the same canonical Attestation Payload with the same OIDC identity in both cases. End Users who care about the difference read the Trust Tier (`Signed` vs `Dual-Attested`) — that is exactly what the tier signal already encodes. Inventing a second profile field doubles the schema surface for a distinction that is already represented elsewhere.

## Decisions made (not questions)

- **Terminology** — Use **Content Directory** verbatim throughout, and **npm Registry** (qualified) versus **Registry** (the MOAT registry); from D1 + lexicon §"Distribution Channels".
- **Materialization-boundary MUSTs** — Normative MUSTs apply at resolve/fetch/unpack; runtime gating is out of scope; from D2 + CLAUDE.md "What 'Conforming Client' Means".
- **Single `moat` block in `package.json`** — One top-level `moat` object with internal MUST/SHOULD/MAY field split, not multiple sibling fields; from D3.
- **npm provenance is observed-only, orthogonal to Trust Tier** — Observed when present; absence does not change tier; from D4 + Disambiguation above.
- **Hash domain binds to the published tarball's Content Directory** — `reference/moat_hash.py` algorithm applied to the unpacked tarball's content directory; from D5 + Disambiguation above.
- **Revocation reason codes inherit core enum unchanged** — `malicious`, `compromised`, `deprecated`, `policy_violation`; "Unknown future reason values MUST be accepted without error"; from D6 + `moat-spec.md:614-615`.
- **Resolve-time skip logging** — When a Conforming Client skips a revoked hash during resolution (before materialization), it MUST log the skip; from D6.
- **Role-discriminated `attestations: [...]` array** — One array, each entry carries `role: "publisher" | "registry"`; from D7 + Disambiguation above.
- **GitHub sub-specs move to `specs/github/`** — `publisher-action.md` and `registry-action.md` move; `moat-verify.md` stays at top level as transport-agnostic; filenames unchanged; from D7-rider.
- **Cross-references updated repo-wide** — README, `moat-spec.md`, `lexicon.md`, guides under `docs/`, website mirrors under `website/src/content/docs/spec/`, `astro.config.mjs` sidebar slugs, reference workflow comments, panel artifacts left untouched (per `.claude/rules/changelog.md:21` tooling-only exclusion); from Q2 cross-reference inventory.
- **CHANGELOG `[Unreleased]` entry** — Two bullets: an `### Added` for the new sub-spec, a `### Changed` for the directory move with the explicit "no normative change" phrase; from `.claude/rules/changelog.md:10-21`.
- **No new attestation roles beyond publisher and registry** — Future roles are an additive schema change, not part of this sub-spec; from concept Out of Scope.
- **`moat-verify` CLI is unchanged** — Spec-only deliverable; CLI implementation work lives in a follow-on; from concept Out of Scope.

## Out of Scope

- Runtime gating of execution (post-materialization import/require interception) — explicitly outside MOAT's protocol boundary.
- Other registry transports (PyPI, Cargo, Maven, container registries) — npm only for this sub-spec.
- Changes to the transport-agnostic core protocol semantics in `moat-spec.md` beyond what's strictly required to host the npm binding.
- Renaming `publisher-action.md` / `registry-action.md` filenames — only their directory location changes.
- Implementation of `moat-verify` CLI changes — spec-only deliverable.
- New attestation roles beyond publisher and registry.

## Interfaces affected (preview)

- `specs/npm-distribution.md` — new sub-spec; full file added under the house-style header pattern.
- `specs/github/publisher-action.md` — moved from `specs/publisher-action.md`; content unchanged.
- `specs/github/registry-action.md` — moved from `specs/registry-action.md`; content unchanged.
- `specs/moat-verify.md` — remains at top level; no change.
- `moat-spec.md` — `**Sub-specs:**` header (line 9) and the eight-plus inline cross-reference links (lines 103, 143, 148, 218, 281, 286, 681, 682, 1068) updated to `specs/github/...` paths; new bullet under `**Sub-specs:**` linking `specs/npm-distribution.md`.
- `lexicon.md` — entries for **Publisher Action** (line 43) and **Registry Action** (line 44) updated to point at `specs/github/...`; **Distribution Tarball** entry's "Reserved for npm sub-spec" gloss updated to cite `specs/npm-distribution.md`.
- `README.md` — table rows at lines 35–36 updated to `specs/github/...`; new row added for `specs/npm-distribution.md`.
- `RELEASING.md:99` — versioning policy entry updated to `specs/github/publisher-action.md`.
- `CHANGELOG.md` — `[Unreleased]` section gains `### Added` entry for the new sub-spec and `### Changed` entry for the directory move (with "no normative change").
- `docs/guides/publisher.md:248` — link updated to `../../specs/github/publisher-action.md`.
- `website/astro.config.mjs:91-92` — sidebar slugs and a new entry for `spec/npm-distribution`.
- `website/src/content/docs/overview/spec-status.md:22-23`, `website/src/content/docs/overview/use-cases.md`, `website/src/content/docs/guides/*.md` — slug links updated.
- `website/src/content/docs/spec/core.md` — `**Sub-specs:**` header updated; cross-reference anchors updated.
- `website/src/content/docs/spec/publisher-action.md`, `website/src/content/docs/spec/registry-action.md`, plus a new `website/src/content/docs/spec/npm-distribution.md` — website mirrors of the sub-specs (kept at the existing slug positions per `astro.config.mjs`).
- `reference/moat-publisher.yml:260, 482` and `reference/moat-registry.yml:759` — code-comment spec-path strings updated to `specs/github/...` (these are tooling per `.claude/rules/changelog.md:21` but are user-visible inside the workflow files).
- `.github/workflows/moat-publisher.yml:260, 482` and `.github/workflows/moat-registry.yml:759` — same comment updates as the reference templates.

DESIGN_COMPLETE
