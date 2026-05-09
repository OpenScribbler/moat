# Research findings — npm-distribution-spec

## Q1 — House style of existing sub-specs

### File-level metadata header

`specs/publisher-action.md:1-9` opens with a fixed metadata block:
- Line 1: `# Publisher Action Specification` (H1, "<Name> Specification")
- Line 3: `**Version:** 0.2.0 (Draft)`
- Line 4: `**Requires:** moat-spec.md ≥ 0.5.0`
- Line 5: `**Part of:** [MOAT Specification](../moat-spec.md)`
- Line 7: a single blockquote one-liner stating the artifact's purpose and primary adoption claim ("> The Publisher Action is the primary adoption mechanism …").
- Line 9: a horizontal rule (`---`) separating the header from body sections.

`specs/registry-action.md:1-9` mirrors that exact structure (same H1 form, same `Version`/`Requires`/`Part of` lines, same blockquote one-liner, same trailing `---`).

### Section heading map (publisher-action.md, line ranges)

From `grep '^#' specs/publisher-action.md` — file is 251 lines:

- `## What It Does (on push)` — `specs/publisher-action.md:11-23` (numbered procedure 1–9 plus a "Branch isolation note:" paragraph)
- `## Undiscovered Content Detection (normative)` — `specs/publisher-action.md:25-53`
- `## `.moat/` Directory Reservation (normative)` — `specs/publisher-action.md:55-74`
- `## Actionable Error Messages (normative — SHOULD)` — `specs/publisher-action.md:76-94`
- `## Attestation Payload Schema (normative)` — `specs/publisher-action.md:96-118`
- `## `moat-attestation.json` Format (normative)` — `specs/publisher-action.md:120-149`
- `## Revocation via Publisher Action` — `specs/publisher-action.md:151-157`
- `## Webhook (optional)` — `specs/publisher-action.md:159-180`
- `## Badge Integration` — `specs/publisher-action.md:182-192`
- `## Private Repository Guard` — `specs/publisher-action.md:194-246`
  - `### Visibility States (normative)` — `specs/publisher-action.md:196-212`
  - `### Opting In` — `specs/publisher-action.md:214-232`
  - `### Informed Consent Limitation (informative)` — `specs/publisher-action.md:234-244`
- `## Scope` — `specs/publisher-action.md:248-251` (closes with "**Current version:**" and "**Planned future version:**" lines)

### Section heading map (registry-action.md, line ranges)

File is 217 lines:

- `## What It Does (on schedule / on `.moat/registry.yml` change)` — `specs/registry-action.md:11-30`
- `## `.moat/registry.yml` Config Format (normative)` — `specs/registry-action.md:32-67`
- `## Trust Tier Determination (normative)` — `specs/registry-action.md:69-115`
- `## Crawl Optimization (Informative)` — `specs/registry-action.md:117-131`
- `## Manifest Size (Informative)` — `specs/registry-action.md:133-141`
- `## Per-Item Canonical Payload` — `specs/registry-action.md:143-163`
- `## Revocation Handling` — `specs/registry-action.md:165-177`
- `## Self-Publishing` — `specs/registry-action.md:179-194`
- `## Private Repository Guard` — `specs/registry-action.md:196-212`
- `## Scope` — `specs/registry-action.md:214-217`

### Heading-suffix conventions (descriptive parentheticals)

The file labels sections by normative status directly in the heading. Patterns observed in `specs/publisher-action.md:25-194`:
- `(normative)` — content is RFC 2119-bearing and binding (e.g. lines 25, 55, 96, 120).
- `(normative — MUST)` — section's primary requirement is a MUST (e.g. line 29 inline label).
- `(normative — SHOULD)` — section's primary requirement is a SHOULD (e.g. line 76).
- `(informative)` — non-binding context (e.g. `### Informed Consent Limitation (informative)` at line 234).
- `(optional)` — feature opt-in section (`## Webhook (optional)`, line 159).

`specs/registry-action.md:117` and `:133` use `(Informative)` (capitalized) for whole-section informative-only blocks.

### RFC 2119 keyword usage observed

All-caps RFC 2119 keywords appear inline within prose paragraphs and table cells, never in heading text alone. Examples:
- `MUST` — `specs/publisher-action.md:23, 27, 29, 49, 57, 64, 70, 72, 145, 147, 174, 198, 207, 211, 223, 229`
- `MUST NOT` — `specs/publisher-action.md:23, 57, 70, 72, 147, 178, 210` (and registry-action.md:26, 173, 192, 206, 210)
- `SHOULD` — `specs/publisher-action.md:76, 78, 86, 143, 176`; `specs/registry-action.md:26, 113, 119, 121, 123, 135, 137, 175, 192, 206`
- `MAY` — `specs/publisher-action.md:143, 229`; `specs/registry-action.md:111, 113, 119, 121, 175, 208, 210`
- `REQUIRED` / `OPTIONAL` — used as cell values in field-definition tables (e.g. `specs/registry-action.md:54-63`, `specs/publisher-action.md:143-147`); also inline as `**Required**` column headers.
- `RECOMMENDED` — not observed in the two sub-specs' bodies; `specs/publisher-action.md:116` uses lower-case "recommended" prose.

Bold-label inline qualifiers introduce many normative statements, e.g. `**Detection rule (normative — MUST):**` (`specs/publisher-action.md:29`), `**Unknown-file warning (normative — MUST):**` (line 64), `**Attestation exclusion (normative — MUST):**` (line 72), `**Hash mismatch (normative):**` (`specs/registry-action.md:104`), `**Disclosure:**` (`specs/registry-action.md:192`).

There is no dedicated "Conventions / Terminology" section in either sub-spec citing RFC 2119 by reference; conventions are inherited from the parent `moat-spec.md`.

### Example-structure conventions

- **Field-definition tables** use a 3-column `Field | Required | Description` grid with the `Required` cell carrying RFC 2119 keywords (`REQUIRED`, `OPTIONAL`). Example: `specs/registry-action.md:52-63` (`.moat/registry.yml` config); `moat-spec.md:766-797` (manifest); `moat-spec.md:840-855` (lockfile).
- **Fenced JSON examples** are introduced by a one-line lead-in describing what the snippet shows, e.g. `specs/publisher-action.md:124-141` (`moat-attestation.json` block) and `specs/publisher-action.md:100-102` (canonical attestation payload one-liner).
- **Fenced YAML examples** for config files appear at `specs/registry-action.md:34-48` (`.moat/registry.yml`) and `specs/publisher-action.md:163-167, 216-221` (workflow `with:` blocks).
- **Field-notes lists** follow each table, prefixed by `**Field notes:**` or `**Field definitions:**` (`moat-spec.md:798-807`, `:856-867`).
- **Procedural steps** in "What It Does" are numbered ordered lists ending with a "Branch isolation note:" or similar paragraph (`specs/publisher-action.md:11-23`, `specs/registry-action.md:11-26`).
- **Tables for tier/visibility/state matrices** use Markdown pipe tables, e.g. `specs/publisher-action.md:202-205` (visibility/behavior matrix); `specs/registry-action.md:200-204` (same structure); `specs/registry-action.md:127-131` (reuse-criteria summary).
- **Closing `## Scope` section** lists "**Current version:**" and "**Planned future version:**" as bold-prefixed one-liners (`specs/publisher-action.md:250-251`, `specs/registry-action.md:216-217`).

## Q2 — Cross-references to GitHub-specific sub-specs

All matches in the moat repo for literal occurrences of `specs/publisher-action.md` / `specs/registry-action.md`, or for path-equivalent slugs (`/spec/publisher-action`, `spec/publisher-action`) on the website mirror. Categorized by file.

### Top-level docs

- `README.md:35` — table row linking to `specs/publisher-action.md`.
- `README.md:36` — table row linking to `specs/registry-action.md`.
- `RELEASING.md:99` — versioning policy mentioning `specs/publisher-action.md` (note: only `publisher-action.md` is named there; `registry-action.md` is not mentioned in `RELEASING.md`).

### Core spec `moat-spec.md`

- `moat-spec.md:9` — `**Sub-specs:**` header listing both files.
- `moat-spec.md:103` — prose link to `specs/publisher-action.md`.
- `moat-spec.md:143` — defining bullet for "**[Publisher Action](specs/publisher-action.md)**".
- `moat-spec.md:148` — defining bullet for "**[Registry Action](specs/registry-action.md)**".
- `moat-spec.md:218` — link to `specs/publisher-action.md` (Repository Layout section).
- `moat-spec.md:281` — link to `specs/publisher-action.md` (Discovery section).
- `moat-spec.md:286` — link to `specs/publisher-action.md` (`moat-attestation.json` reserved-filename note).
- `moat-spec.md:681` — Reference-implementations bullet linking `reference/moat-publisher.yml` to `specs/publisher-action.md`.
- `moat-spec.md:682` — Reference-implementations bullet linking `reference/moat-registry.yml` to `specs/registry-action.md`.
- `moat-spec.md:1068` — anchored link to `specs/publisher-action.md#attestation-payload-schema-normative`.

### Lexicon

- `lexicon.md:43` — entry "**Publisher Action**" defines the term as the Action specified in `specs/publisher-action.md`.
- `lexicon.md:44` — entry "**Registry Action**" defines the term as the Action specified in `specs/registry-action.md`.

### Specs cross-linking each other

- `specs/publisher-action.md:62` — link from `.moat/` directory reservation list to `registry-action.md`.

### CHANGELOG entries (history of edits)

All from `CHANGELOG.md`:
- `CHANGELOG.md:12` — "Publisher Action signing step (`specs/publisher-action.md`)" entry.
- `CHANGELOG.md:13` — "Registry Action signing steps (`specs/registry-action.md`)" entry.
- `CHANGELOG.md:26` — `workflow_run` chain entry citing `specs/registry-action.md`.
- `CHANGELOG.md:30` — sub-spec version bump entry naming both `specs/publisher-action.md` and `specs/registry-action.md`.
- `CHANGELOG.md:35` — website mirror drift entry referencing `website/src/content/docs/spec/registry-action.md`.
- `CHANGELOG.md:45` — config-path rename entry naming both sub-specs.
- `CHANGELOG.md:49` — `.moat/` reservation entry citing `specs/publisher-action.md`.
- `CHANGELOG.md:50` — actionable-error-messages entry citing `specs/publisher-action.md §Actionable Error Messages`.
- `CHANGELOG.md:51` — `.moat` exclusion entry citing `specs/publisher-action.md`.
- `CHANGELOG.md:59` — OIDC legacy-path fallback removal citing both sub-specs.
- `CHANGELOG.md:86` — reference template entry citing the v0.6.0 tombstone rule.
- `CHANGELOG.md:87` — reference template undiscovered-content entry.
- `CHANGELOG.md:88` — reference template log-line entry citing `specs/publisher-action.md §Undiscovered Content Detection`.
- `CHANGELOG.md:89` — `(name, type)` uniqueness entry citing `specs/registry-action.md` step 7.
- `CHANGELOG.md:140` — bullet noting "operational details belong in `specs/publisher-action.md`".
- `CHANGELOG.md:164` — `publisher_workflow_ref` documentation entry naming `specs/publisher-action.md`.
- `CHANGELOG.md:165` — entry naming `specs/registry-action.md`.
- `CHANGELOG.md:169` — bullet referencing `publisher-action.md`.
- `CHANGELOG.md:173` — bullet referencing `specs/registry-action.md`.
- `CHANGELOG.md:183` — bullet announcing the addition of `specs/registry-action.md`.

### Rules / agent-only docs

- `.claude/rules/changelog.md:40` — names `specs/publisher-action.md` as an example of an "external reference" anchor that is welcome in changelog entries.

### Reference implementations and workflows

- `reference/moat-publisher.yml:260` — code comment "Tier-3: undiscovered content detection (specs/publisher-action.md)."
- `reference/moat-publisher.yml:482` — code comment "Discovery summary (specs/publisher-action.md §Undiscovered Content Detection)."
- `reference/moat-registry.yml:239` — User-Agent string `"moat-registry-action/0.2.0"` (string token "registry-action" appears here, not a path reference).
- `reference/moat-registry.yml:759` — code comment referencing `registry-action.md` step 7.
- `reference/moat_verify.py:556` — code comment "moat-verify.md spec says /raw/main/ but publisher-action pushes to" (token "publisher-action").
- `.github/workflows/moat-publisher.yml:260` — same comment as the reference template.
- `.github/workflows/moat-publisher.yml:482` — same comment as the reference template.
- `.github/workflows/moat-registry.yml:239` — same User-Agent string.
- `.github/workflows/moat-registry.yml:759` — same step-7 code comment.

### Guides (top-level `docs/`)

- `docs/guides/publisher.md:248` — link to `../../specs/publisher-action.md`.

(There were no matches for `specs/publisher-action.md` or `specs/registry-action.md` in `docs/guides/registry.md`, `docs/guides/moat-verify.md`, `docs/guides/cosign-offline.md`, or `docs/guides/self-publishing.md` in the grep output.)

### Website (`website/`)

- `website/astro.config.mjs:91` — sidebar entry `{ label: 'Publisher Action', slug: 'spec/publisher-action' }`.
- `website/astro.config.mjs:92` — sidebar entry `{ label: 'Registry Action', slug: 'spec/registry-action' }`.
- `website/src/content/docs/overview/spec-status.md:22` — table row linking `/spec/publisher-action`.
- `website/src/content/docs/overview/spec-status.md:23` — table row linking `/spec/registry-action`.
- `website/src/content/docs/overview/use-cases.md:34` — link `/spec/publisher-action`.
- `website/src/content/docs/overview/use-cases.md:58` — link `/spec/registry-action`.
- `website/src/content/docs/overview/use-cases.md:82` — link `/spec/publisher-action`.
- `website/src/content/docs/overview/use-cases.md:83` — link `/spec/registry-action`.
- `website/src/content/docs/overview/use-cases.md:163` — link `/spec/publisher-action`.
- `website/src/content/docs/guides/publishers.md:65` — link `/spec/publisher-action`.
- `website/src/content/docs/guides/publishers.md:258` — link `/spec/publisher-action`.
- `website/src/content/docs/guides/registry-operators.md:66` — link `/spec/registry-action`.
- `website/src/content/docs/spec/publisher-action.md` — the file itself; line 65 cross-links `/spec/registry-action`; lines 167 and 220 contain `uses: moat-spec/publisher-action@v1`.
- `website/src/content/docs/spec/registry-action.md` — the file itself.
- `website/src/content/docs/spec/core.md:9` — `**Sub-specs:**` header listing both website slugs.
- `website/src/content/docs/spec/core.md:103, 143, 148, 218, 281, 286, 681, 682, 1068` — all the same anchor positions as `moat-spec.md`, ported to website slugs.
- `website/landing-mockups/01-academic-standard/index.html:462, 466` — string tokens `/spec/publisher-action`, `/spec/registry-action`.
- `website/landing-mockups/09-diagram-blueprint/index.html:521, 531, 638, 650` — token references `moat-publisher-action`, `moat-registry-action`, `publisher-action.yml`, `registry-action.yml` in static HTML diagrams.

### Panel / working-group artifacts (informative — not user-facing)

- `panel/issues-archive.md:7, 36, 108, 118, 166` — historical panel notes referencing `specs/publisher-action.md`.
- `panel/doc-restructure-plan.md:25, 67, 70, 172, 226, 232, 233, 912, 964, 977, 1008` — historical restructuring plan referencing both sub-specs.
- `panel/remy-0-4-1-review.md:7, 77` — panel review document referencing `specs/publisher-action.md`.
- `panel/fix-hashing-bug.md:62, 78` — panel note referencing `publisher-action.md`.

### Inline-only string tokens (no file path link)

- `specs/publisher-action.md:164, 217` — `uses: moat-spec/publisher-action@v1` (workflow consumer string, not a spec path).

## Q3 — Manifest content-entry schema

The registry-manifest content-entry schema is defined in `moat-spec.md` under `### Registry Manifest` at `moat-spec.md:732-808`. The minimum-structure JSON example covers `content[]` at `moat-spec.md:751-761`:

```
"content": [
  {
    "name": "my-skill",
    "display_name": "My Skill",
    "type": "skill",
    "content_hash": "sha256:abc123...",
    "source_uri": "https://github.com/owner/repo",
    "attested_at": "2026-04-08T00:00:00Z",
    "private_repo": false
  }
]
```

The full field table is at `moat-spec.md:766-797`. Per-`content[]` rows (verbatim from that table):

- `content[].name` — REQUIRED — "Canonical identifier for the content item" (`moat-spec.md:779`).
- `content[].display_name` — REQUIRED — "Human-readable name" (`moat-spec.md:780`).
- `content[].type` — REQUIRED — "One of: `skill`, `agent`, `rules`, `command`" (`moat-spec.md:781`).
- `content[].content_hash` — REQUIRED — "`<algorithm>:<hex>` — normative identity of the content" (`moat-spec.md:782`).
- `content[].source_uri` — REQUIRED — "Source repository URI" (`moat-spec.md:783`).
- `content[].attested_at` — REQUIRED — "Registry attestation timestamp (RFC 3339 UTC)" (`moat-spec.md:784`).
- `content[].private_repo` — REQUIRED — "`true` if sourced from a private or internal repository" (`moat-spec.md:785`).
- `content[].rekor_log_index` — "REQUIRED for Signed + Dual-Attested" — "Integer index of the registry's Rekor transparency log entry attesting this content item. Absent for Unsigned items — its absence is the Unsigned tier signal." (`moat-spec.md:786`).
- `content[].derived_from` — OPTIONAL — "Source URI of the item this was forked or derived from" (`moat-spec.md:787`).
- `content[].version` — OPTIONAL — "Display label only; `content_hash` is normative identity" (`moat-spec.md:788`).
- `content[].scan_status` — OPTIONAL — references `### scan_status` schema (`moat-spec.md:789`; nested schema at `moat-spec.md:929-956`).
- `content[].signing_profile` — "REQUIRED for Dual-Attested" — references `### signing_profile` (`moat-spec.md:790`; nested schema at `moat-spec.md:958-1018`).
- `content[].attestation_hash_mismatch` — OPTIONAL — "`true` if the registry's computed hash for this item differed from the hash recorded in the publisher's `moat-attestation.json`. Present only when a mismatch was detected; absent otherwise. Indicates that the publisher's attestation does not cover the current content." (`moat-spec.md:791`).

Adjacent uniqueness constraint (`moat-spec.md:807`): `content[].name` + `content[].type` MUST be unique within a single manifest. The compound key `(name, type)` is the normative uniqueness constraint. A manifest with two entries sharing the same `name` and `type` is malformed — conforming registries MUST NOT publish such a manifest.

There is no separate JSON Schema (`.json` schema file) checked into the repo for the manifest. The schema is defined in prose + table + JSON example only at the locations above. The registry-action workflow encodes the same field set procedurally — for example, `(name, type)` uniqueness is enforced at `specs/registry-action.md:22` and at the comment `reference/moat-registry.yml:759` ("# registry-action.md step 7 — fail non-zero on duplicates."). No `*.schema.json`, `manifest-schema.*`, or similar file is referenced elsewhere in the codebase grep results.

## Q4 — Revocation machinery

### Lockfile `revoked_hashes` field

Defined in `moat-spec.md` under `### Lockfile`:
- Schema example: `moat-spec.md:836` shows `"revoked_hashes": []` as a top-level lockfile field.
- Field row: `moat-spec.md:855` — "`revoked_hashes` | REQUIRED | Array of hard-blocked content hash strings; empty array if none".
- Field-notes constraint (`moat-spec.md:865`): "`revoked_hashes` entries MUST NOT be silently removed. Clearing a revoked hash requires deliberate End User action. This prevents the remove-and-reinstall bypass: an attempt to reinstall a revoked hash is blocked by this record."
- Lockfile-authoritative rule (`moat-spec.md:663`): "When a client has previously recorded a revocation in its lockfile `revoked_hashes` array and that revocation entry subsequently disappears from the registry manifest (due to pruning), the lockfile entry persists. The hard-block continues. A client MUST NOT remove a `revoked_hashes` entry because the manifest no longer carries the revocation."
- Client behavior on registry revocation (`moat-spec.md:635`): "The revoked content hash MUST be added to `revoked_hashes` in the lockfile — see lockfile specification above."

### Manifest `revocations` array

Defined in `moat-spec.md` under `### Registry Manifest`:
- Schema example: `moat-spec.md:762` shows `"revocations": []`.
- Field rows (`moat-spec.md:792-796`):
  - `revocations` — REQUIRED — "Array of revocation entries; empty array if none".
  - `revocations[].content_hash` — REQUIRED — "Hash of the revoked content item".
  - `revocations[].reason` — REQUIRED — "One of: `malicious`, `compromised`, `deprecated`, `policy_violation`".
  - `revocations[].details_url` — "REQUIRED for registry / OPTIONAL for publisher" — "URL to public revocation details".
  - `revocations[].source` — OPTIONAL — "Revocation source: `\"registry\"` or `\"publisher\"`. Absent defaults to `\"registry\"` (fail-closed). Determines client behavioral class — see [Revocation Mechanism](#revocation-mechanism)."
- Top-level revocation-mechanism prose: `moat-spec.md:612-616` — "**Revocation mechanism** — `revocations` array in manifest (REQUIRED; empty if none). Each entry MUST include: `content_hash`, `reason`, and `details_url` (REQUIRED for registry revocations; OPTIONAL for publisher revocations). Reason values (informational only — they do NOT determine client behavior): `malicious`, `compromised`, `deprecated`, `policy_violation`. Unknown future reason values MUST be accepted without error."

The publisher side's revocations array is documented in `moat-attestation.json` schema at `specs/publisher-action.md:124-141` (line 139 shows `"revocations": []`), and operational rules at `specs/publisher-action.md:151-157` (publisher revocations are warnings, not hard blocks).

The registry-action handling of the manifest's `revocations` array is at `specs/registry-action.md:165-176` — registry-initiated revocations (`source: "registry"`) come from `.moat/registry.yml`; publisher-initiated revocations (`source: "publisher"`) come from each source's `moat-attestation.json`. When both exist for the same hash, the registry-initiated entry takes precedence (line 173).

Registry-action `.moat/registry.yml` schema fields for revocations: `specs/registry-action.md:60-63`.

### `revocation-tombstones.json`

Specified in `moat-spec.md` under the revocation-archival rule (`moat-spec.md:665`): "**Tombstone rule (normative for Registry Action):** Registries MUST NOT re-list a content item in the `content` array if a revocation entry for that item's `content_hash` has been pruned from the `revocations` array. A content hash that was once revoked and subsequently pruned is permanently tombstoned — it MUST NOT reappear as installable content. The Registry Action enforces this via a `revocation-tombstones.json` file in the `moat-registry` branch alongside the manifest. This file contains an array of content_hash strings that must never reappear in the `content` array. The file persists between crawl runs and is appended to (never shrunk) when revocations are pruned from the `revocations` array."

The reference implementation reads/writes the file in `reference/moat-registry.yml`:
- Definition `get_existing_registry_state` — `reference/moat-registry.yml:280-317` (fetches existing `registry.json` and `revocation-tombstones.json` from the `moat-registry` branch; line 306: `["git", "show", "FETCH_HEAD:revocation-tombstones.json"]`).
- `push_manifest(manifest_path, tombstones_path, branch="moat-registry")` — `reference/moat-registry.yml:507-540` (copies the tombstones file alongside the manifest on push; line 540: `"revocation-tombstones.json"`).
- Tombstone accumulation logic — `reference/moat-registry.yml:731-755` (line 744: `tombstones = sorted(set(existing_tombstones) | newly_pruned)`; lines 746-755 filter tombstoned hashes out of `content[]`).
- Output write — `reference/moat-registry.yml:811-815` (line 813: `tombstones_path = Path("revocation-tombstones.json")`; line 815: `json.dump(tombstones, f, indent=2)`).

The associated `.github/workflows/moat-registry.yml` (the deployed copy) carries identical logic.

### Reason-code enum

Canonical enum values appear in three normative locations and are identical across them:

1. `moat-spec.md:614-615` (Revocation mechanism prose): `malicious`, `compromised`, `deprecated`, `policy_violation`. Marked "informational only — they do NOT determine client behavior".
2. `moat-spec.md:794` (manifest field table): `revocations[].reason` REQUIRED — "One of: `malicious`, `compromised`, `deprecated`, `policy_violation`".
3. `specs/registry-action.md:62` (`.moat/registry.yml` config field table): `revocations[].reason` REQUIRED — "One of: `malicious`, `compromised`, `deprecated`, `policy_violation`".

Reason-code semantics table (informative meanings + urgency signals) at `moat-spec.md:619-624`:
- `malicious` — "Content has been identified as having malicious behavior (e.g., prompt injection, exfiltration, destructive side effects)" — "High — surface prominently".
- `compromised` — "The publisher's account, signing key, or distribution channel is believed compromised; content may not be malicious but cannot be trusted as authentic" — "High — surface prominently".
- `deprecated` — "Publisher has formally deprecated this content in favor of a successor; no security concern" — "Low — may be surfaced passively".
- `policy_violation` — "Content was removed for registry policy reasons; security posture unspecified" — "Informational".

Forward-compat rule (`moat-spec.md:615`): "Unknown future reason values MUST be accepted without error."

Behavior-by-source (not by reason) table — `moat-spec.md:633-636`: registry-source revocation = MUST hard-block; publisher-source revocation = MUST present, warn once per session, MAY allow with explicit confirmation, MUST NOT silently continue.

Non-interactive client matrix — `moat-spec.md:652-657`. Archive policy (180-day minimum retention) — `moat-spec.md:661`.

## Q5 — Content hash algorithm input domain

### What `reference/moat_hash.py` consumes

The script's CLI accepts a single argument, a directory path:
- Module docstring (`reference/moat_hash.py:14-15`): `Usage:    python3 moat_hash.py <directory>`.
- CLI entry point (`reference/moat_hash.py:203-211`): `if len(sys.argv) != 2: print(f"Usage: {sys.argv[0]} <directory>", file=sys.stderr); sys.exit(1)` then `print(content_hash(sys.argv[1]))`.
- Top-level function signature (`reference/moat_hash.py:166`): `def content_hash(directory: str | Path) -> str:` — takes a directory; the docstring at `:167-172` says: "Compute the MOAT content hash for a directory. Raises ValueError if any symlinks are present (rejected at ingestion) or if the directory contains no files."
- Walk implementation (`reference/moat_hash.py:173-176`): `root = Path(directory); entries: list[tuple[str, str]] = []; for path in root.rglob("*"):` — full recursive walk.

The input domain is therefore a single directory rooted at `directory`; the file list is derived by recursive walk of that root. There is no API for an externally provided file list.

### Canonicalization and exclusion steps applied

Walk-time exclusions (`reference/moat_hash.py:176-184`):
- `if any(part in VCS_DIRS for part in path.parts): continue` — excludes any path whose parts include `.git`, `.svn`, `.hg`, `.bzr`, `_darcs`, `.fossil` (set defined `:50`).
- `if path.parent == root and path.name in EXCLUDED_FILES: continue` — root-level exclusion of `moat-attestation.json` only (set defined `:60`; comment `:52-59` documents the rule that subdirectory copies of the same name are NOT excluded).
- `if path.is_symlink(): raise ValueError(...)` — symlinks anywhere reject the whole hash.
- `if not path.is_file(): continue` — directories themselves are not hashed; only files contribute.

Per-file canonicalization (`reference/moat_hash.py:65-75, 77-90, 95-101, 103-161, 186-198`):
- **Path normalization (`:186`):** `rel = unicodedata.normalize("NFC", path.relative_to(root).as_posix())` — paths are NFC-normalized POSIX-form strings relative to the root.
- **Text/binary classification (`:65-90`):** A file is text iff (a) `final_extension(name)` is in the closed `TEXT_EXTENSIONS` set and (b) the first 8 KB (`NUL_SCAN = 8192`, `:44`) contain no NUL byte. `final_extension` returns `""` for dotfiles and extensionless files (`:65-75`), so all such files are treated as binary.
- **`TEXT_EXTENSIONS` (`:25-40`):** `.md, .txt, .rst, .yaml, .yml, .json, .toml, .ini, .cfg, .conf, .html, .htm, .xml, .svg, .css, .scss, .less, .js, .ts, .jsx, .tsx, .mjs, .cjs, .py, .rb, .lua, .rs, .go, .sh, .bash, .zsh, .fish, .csv, .tsv, .sql, .lock, .sum, .mod`.
- **Text canonicalization (`:103-161`):** SHA-256 over UTF-8 bytes after stripping a leading UTF-8 BOM (`UTF8_BOM = b"\xef\xbb\xbf"`, `:42`) and normalizing line endings: CR LF → LF, lone CR → LF, LF → LF, with greedy CRLF matching across chunk boundaries (`pending_cr` state).
- **Binary hashing (`:95-100`):** SHA-256 of the file bytes verbatim (no normalization).
- **Sort order (`:194`):** `entries.sort(key=lambda e: e[0].encode("utf-8"))` — entries are sorted by the raw UTF-8 byte order of the relative path.
- **Manifest line format (`:197`):** `manifest = "".join(f"{h}  {p}\n" for p, h in entries).encode("utf-8")` — sha256sum-style "<hex_hash>  <relpath>\n" lines, UTF-8.
- **Final output (`:198`):** `return "sha256:" + hashlib.sha256(manifest).hexdigest()`.
- **Empty-directory rule (`:190-191`):** `if not entries: raise ValueError("No files found — content is unpublishable")`.

Constants: `CHUNK = 65536` (`:43`); `NUL_SCAN = 8192` (`:44`).

### Where the algorithm is specified in `moat-spec.md`

`moat-spec.md` does not embed the algorithm body. The spec section `### Content Hashing` at `moat-spec.md:325-330` reads in full:

> The content hash identifies a content directory by canonical byte sequence using the normative [`reference/moat_hash.py`](reference/moat_hash.py) reference implementation. Resolved normalization rules, exclusion rules, and conformance expectations are defined by the reference implementation and its test vectors.

The reference-implementations bullet (`moat-spec.md:677-679`) says: "**[`reference/moat_hash.py`](reference/moat_hash.py)** — Python reference implementation. A conforming implementation produces identical output for all test vectors. Two independent implementations in different languages must pass all test vectors before the spec advances beyond Draft."

The script itself (`reference/moat_hash.py:3-12`) qualifies the normative authority: "This script is an informative reference implementation. The normative authority for correct output is the test vector suite in generate_test_vectors.py and test_normalization.py. When this script and a test vector disagree, the test vector is correct and this script has a bug."

`moat-spec.md:683`: "**[`reference/generate_test_vectors.py`](reference/generate_test_vectors.py)** — **Normative.**"

The publisher-action and registry-action sub-specs both delegate hash computation to `reference/moat_hash.py`:
- `specs/publisher-action.md:15` — step 3: "Computes content hashes using the MOAT algorithm ([`reference/moat_hash.py`](../reference/moat_hash.py))."
- `specs/registry-action.md:19` — step 4: "Computes content hashes for all discovered items using the MOAT algorithm ([`reference/moat_hash.py`](../reference/moat_hash.py))."

## Q6 — Four MOAT design tests

The four design tests are defined in `CLAUDE.md`, the project AI-session guidelines file. The section is `## For AI-Assisted Sessions` at `CLAUDE.md:117`. Lead-in line at `CLAUDE.md:119`: "Before landing on a recommendation or drafting spec language, apply these checks:".

Verbatim text of each test:

- **Day-one test** — `CLAUDE.md:121`:
  > **The day-one test.** What does the ecosystem look like the moment this spec ships — not after ideal adoption? If thousands of existing content items don't conform on day one, the spec needs to acknowledge that, not pretend conformance will materialize.

- **Copy-survival test** — `CLAUDE.md:123`:
  > **The copy survival test.** Content gets copied between repos constantly. Aggregators scrape and re-host without reading specs. Does this design element survive being copied to a different repo by someone who never read the spec? If it depends on a sidecar file an aggregator will strip, it is fragile by design.

- **"Works fine without it" test** — `CLAUDE.md:125`:
  > **The "works fine without it" test.** If a requirement can be ignored with no observable consequence, it will be ignored. Before using MUST or SHOULD, confirm there is a way to detect or enforce non-compliance. If there isn't, it's a suggestion.

- **Enforcement question** — `CLAUDE.md:127`:
  > **The enforcement question.** What is the enforcement mechanism? If the answer is "trust that people will comply," either provide tooling that enforces it automatically or remove the normative language.

A fifth check appears immediately after them at `CLAUDE.md:129` ("**The reference implementation question.**"); it is not part of the four enumerated tests but lives in the same checklist section.

Other locations referencing day-one framing:
- `panel/remy-0-4-1-review.md:34` — "prevents the tier from becoming alert fatigue from day one".
- `panel/remy-0-4-0-review.md:119` — "On day one and for an extended period thereafter…".

No grep match for "copy-survival", "copy survival", "works-fine-without", or "enforcement test" outside `CLAUDE.md` (and the `.ship/npm-distribution-spec.json` ticket scaffold, which I did not read).

## Q7 — CHANGELOG conventions

Source: `.claude/rules/changelog.md` (74 lines).

### Frontmatter / scope

`.claude/rules/changelog.md:1-4`:
```
---
description: MOAT changelog conventions — how to write CHANGELOG.md and when spec edits require an [Unreleased] entry
globs: CHANGELOG.md, moat-spec.md, specs/**/*.md
---
```

### `[Unreleased]` entry rule

`.claude/rules/changelog.md:10-21` ("Every spec edit gets a changelog entry"):
- "Any change to `moat-spec.md` or a sub-spec under `specs/*.md` made after a release tag MUST be logged in `CHANGELOG.md` in the same commit." (line 12)
- "If there is no `[Unreleased]` section at the top of `CHANGELOG.md`, add one." (line 14)
- "Log the edit under the appropriate Keep-a-Changelog section (`Added`, `Changed`, `Removed`, `Fixed`, `Deprecated`, `Security`)." (line 15)
- "State whether the edit is normative or editorial. If editorial, include a phrase like \"no normative change\" so readers know it's a PATCH-level clarification." (line 16)
- "When the next release is cut, the `[Unreleased]` contents move into the new versioned section per [RELEASING.md](../../RELEASING.md)." (line 17)
- "This applies even to single-line edits. Version bumping is batched per RELEASING.md's \"batch editorial fixes\" policy, but `[Unreleased]` tracking is **per-commit**, not batched." (line 19)
- Tooling-only exclusion list (line 21): "Tooling-only changes (files under `scripts/`, `.github/`, `.gitignore`, `AGENTS.md`, `.claude/`, `ROADMAP.md`) are not spec content and do not need a changelog entry."

Existing `[Unreleased]` shape in `CHANGELOG.md`:
- `CHANGELOG.md:5` — `## [Unreleased]`.
- `CHANGELOG.md:7` — opening one-paragraph summary ("Breaking change: the cosign bundle format is now pinned to Sigstore protobuf bundle v0.3…").
- `CHANGELOG.md:9` — `### Changed` Keep-a-Changelog subsection.
- Subsequent versioned sections at `CHANGELOG.md:20, 39, 80, 97, 134, 145, 156, 177, 200, 237, 279, 294, 331` use the form `## [<version>] — <YYYY-MM-DD> (Draft)` (Draft is dropped after the version is released; cf. `:156, :177, :237, :279` for non-Draft examples).

### Forbidden phrases / content

`.claude/rules/changelog.md:23-32` ("Do not include internal process metadata"):

> The following MUST NOT appear in changelog entries.

Bulleted list (lines 27-30):
- **Panel, review, or persona references.** Examples to avoid: `"five-persona panel review"`, `"adversarial review"`, `"reviewer feedback"`, `"agent consensus"`.
- **Internal finding IDs.** Examples to avoid: `SC-2`, `DQ-5`, `SB-1`, `SC-1`–`SC-7`, "any `XX-N` pattern used in panel notes, review scratchpads, or tracking systems".
- **Counts of internal artifacts.** Examples to avoid: `"resolved 17 findings"`, `"3 ship-blockers"`, `"7 spec changes"`, `"7 design questions"`.
- **References to internal documents or pipelines.** Examples to avoid: "linking or naming `panel/`, bead IDs, internal working-group threads."

Trailing rule (line 32): "If a reader can't act on the detail without context from an internal thread, cut it."

### External references that ARE welcome

`.claude/rules/changelog.md:34-41`:
- CVE identifiers (e.g., `CVE-2024-23651`).
- External standards and their section numbers (e.g., TUF, in-toto, SLSA, OWASP, RFC 3339).
- Spec file locations and section headings (e.g., `moat-spec.md §Trust Model`, `specs/publisher-action.md`).
- Published test vector IDs (e.g., `TV-09`, `TV-MH4`) — "these are part of the spec surface, not internal tracking".

### Required structural sections

`.claude/rules/changelog.md:43-48` ("Structure"):
- "Use Keep-a-Changelog sections: `Added`, `Changed`, `Removed`, `Fixed`, `Deprecated`, `Security`."
- "Open each version with **one paragraph** summarizing what the release delivers and any breaking changes that affect conformers. Do not open with process metadata."
- "Each bullet must stand alone. A reader with zero knowledge of internal discussions should understand the change from the bullet text alone."
- "Prefer the form **bold-label — explanation**. The label names the thing; the explanation says what changed and why it matters."

### Example contrast

`.claude/rules/changelog.md:50-64` provides "Don't" / "Do" examples. The Don't form mixes panel-review language and finding IDs (`(SC-2)`, `(SC-4)`); the Do form retains the same technical content but drops the parentheticals and lead-in, opening with a one-paragraph summary "Breaking release: content type rename, field renames, new required lockfile fields, staleness model redesign."

### Pre-save checklist (when editing existing entries)

`.claude/rules/changelog.md:66-73` ("When editing an existing entry"):

> Before saving any edit to `CHANGELOG.md`, re-read the entry and confirm:
> 1. No panel/persona/review language.
> 2. No finding IDs of the form `SC-N`, `DQ-N`, `SB-N`, or similar.
> 3. No counts of internal artifacts ("N findings", "N ship-blockers").
> 4. The opening paragraph describes the release, not the process.

### Persona / finding-ID rules — summary

There are no positive "use persona X" rules for changelog content; both persona names and finding IDs are forbidden in changelog entries. The two relevant prohibitions are:
- Persona language: forbidden everywhere in entries (line 27).
- Finding IDs: forbidden everywhere in entries (lines 28, 71).

## Cross-cutting observations

- The repo has a parallel website mirror under `website/src/content/docs/spec/` with files `core.md`, `publisher-action.md`, `registry-action.md`, `moat-verify.md`. `CHANGELOG.md:35` records that these mirrors have drifted from the canonical specs in the past and were re-synced.
- `website/astro.config.mjs:91-92` configures the Starlight sidebar with hard-coded `slug: 'spec/publisher-action'` and `slug: 'spec/registry-action'`. A path move would change the sidebar slugs (or require renaming the website mirrors to keep slugs stable).
- Both `.github/workflows/moat-publisher.yml` and `.github/workflows/moat-registry.yml` are checked-in copies of `reference/moat-publisher.yml` and `reference/moat-registry.yml`, with several identical comments at matching line numbers (260, 482; 239, 759). A move of the spec paths would not change workflow filenames but would change the spec-path strings inside comments.
- `RELEASING.md:99` mentions only `specs/moat-verify.md` and `specs/publisher-action.md` as independently-versioned sub-specs; `specs/registry-action.md` is not enumerated there even though `CHANGELOG.md:30` confirms it bumps in lockstep with `publisher-action.md`.
- `lexicon.md:43-44` defines "Publisher Action" and "Registry Action" with explicit pointers to `specs/publisher-action.md` and `specs/registry-action.md`. The lexicon is the source of truth for terminology per `CLAUDE.md` ("Look to npm/Go/TUF/Sigstore/SLSA…" and the "Influences" section, `CLAUDE.md:74-114`).
- The transparency-log primitive name in MOAT is **Rekor**; the canonical attestation payload (`{"_version":1,"content_hash":"sha256:<hex>"}`) is identical for publisher and registry signers and is canonicalized at `moat-spec.md:1020-1071`. The Sigstore protobuf bundle v0.3 is the only supported signature envelope per `moat-spec.md:426` and `CHANGELOG.md:7-14`.
- `panel/` contents are explicitly internal working-group artifacts. `.claude/rules/changelog.md:27, 30` forbids referencing them in CHANGELOG entries. They DO appear in cross-reference grep results for `publisher-action`/`registry-action` (Q2) but are flagged here as internal-only.
- The phrase "Content Directory" is used inside `reference/moat_hash.py:52-60` only as a comment ("root of the content directory only", "Files excluded from content hashing by name — root of the content directory only.") — not as a spec-defined term in `moat-spec.md`. The lexicon contents at `lexicon.md` would be the authority for that term; the lexicon was not fully read here.
- `.beads/` and `.ship/npm-distribution-spec.json` exist in the working tree; per the research-phase guard rules I did not read the ticket file or the design-concept JSON beyond what surfaced incidentally in grep for cross-references in Q2.

RESEARCH_COMPLETE
