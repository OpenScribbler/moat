# Design Discussion: npm-distribution-spec — Round 2

> **Round 2 scope.** Round 1 of this ship is implemented and committed at `64b9c6b` on `main`. The Round 1 design.md (preserved in git history at that commit) is the baseline; this Round 2 document covers only the 10 in-scope decisions surfaced by the final-validate gate review. Two cross-cutting findings (Layering rule + GitHub-ism extraction in `moat-spec.md` / `specs/moat-verify.md`; Trust Tier UI surfacing in the Aggregator) are deferred to a separate ship and are out of scope here.

## Summary

**Current state:** `specs/npm-distribution.md` (v0.1.0 Draft) ships the Content Hash domain, materialization-boundary revocation MUSTs, the `package.json` `moat` block schema, backfill normative section, and the npm provenance informative section — but the Content Directory rule requires Publisher cooperation (no default), the `MOAT_ALLOW_REVOKED` escape hatch is half-finished (no reason-capture, no per-entry expiry, no logging contract), the materialization boundary is named but not anchored to a precise byte-level moment, the `moat-spec.md:9` Sub-specs line still omits the new sub-spec, `.claude/rules/changelog.md:40` still cites the pre-reorg path, the npm provenance section lacks a four-state disagreement table, no reference Publisher workflow exists, and the `package.json` field name `moat.contentDirectory` collides with the lexicon's "Content Directory" concept-name (one realization vs the source-of-truth concept).

**Desired state:** `specs/npm-distribution.md` (v0.2.0 Draft) defines a default Content Directory (= tarball root with one excluded file: `package.json`) so backfill works without Publisher cooperation, renames the JSON field to `moat.tarballContentRoot` to disambiguate concept-vs-realization, anchors the materialization boundary normatively at "before any byte of the tarball is written outside the package manager's content cache," fully specifies `MOAT_ALLOW_REVOKED` (process-scope, REQUIRED reason co-variable, RFC 3339 per-entry expiry, structured override-applied logging), relocates Publisher signing identity into a `publisherSigning` block with optional `rekorLogIndex` discovery accelerator, adds a four-state (provenance × MOAT) disagreement table, and ships `reference/moat-npm-publisher.yml` end-to-end. `moat-spec.md:9` Sub-specs line cites `specs/npm-distribution.md`, `.claude/rules/changelog.md:40` cites the post-reorg path, and `lexicon.md` records that `tarballContentRoot` is the JSON field name realizing the Content Directory concept.

**End state (narrative):** A Publisher with no source-repo cooperation can have their existing npm package backfilled by a Registry — the Registry fetches the Distribution Tarball, applies the default-Content-Directory rule (tarball root minus `package.json`), and the resulting Content Hash binds to bytes any consumer can independently reproduce. A Publisher who wants to attest in `package.json` copies `reference/moat-npm-publisher.yml` and gets a working flow from `npm pack` through `npm publish` with the canonical-hash-stable-across-republish guarantee. An operator running an incident response sets `MOAT_ALLOW_REVOKED=<sha>:<RFC3339>` plus `MOAT_ALLOW_REVOKED_REASON="..."`, and every override is logged with package identity, hash, reason, and expiry — the silent-skip footgun is closed. A spec reader sees `specs/npm-distribution.md` cited from `moat-spec.md:9` and a changelog rule that points at the right path.

## Research questions answered

Round 1 research (Q1–Q7) is unchanged and still grounds this work. Round 2 raises no new research questions — every input is either a Round 1 finding, a Round 2 design-concept decision, or a `file:line` anchor in the on-disk artifacts (`specs/npm-distribution.md`, `moat-spec.md`, `.claude/rules/changelog.md`, `reference/moat-publisher.yml`, `lexicon.md`). The four MOAT design tests (`CLAUDE.md:121-127`) are applied inline below where their judgment matters (default Content Directory, override env-var, materialization boundary).

## Patterns to Follow

The Round 1 design.md (commit `64b9c6b`) established the foundational patterns this sub-spec follows: Sub-spec file-level metadata header (`specs/publisher-action.md:1-9`), Heading-suffix normative status labels, Bold-label inline normative qualifiers, Field-definition tables, Fenced JSON examples with one-line lead-in, Closing `## Scope` section, Canonical Attestation Payload as the signed unit, Content Hash input domain, Lockfile `revoked_hashes` persistence, Reason-code enum, Tombstone permanence, Manifest content-entry schema with `(name, type)` uniqueness, and the CHANGELOG `[Unreleased]` form. Those patterns are not re-explained here. Round 2 adds the patterns below.

### Pattern: Default-with-explicit-override field semantics

**Source:** `moat-spec.md:786` (`content[].rekor_log_index` — "REQUIRED for Signed + Dual-Attested … Absent for Unsigned items — its absence is the Unsigned tier signal."); `reference/moat_hash.py:60` (`EXCLUDED_FILES` set — root-level `moat-attestation.json` is excluded by default with no field to opt out of)

**Snippet:**
```markdown
| `content[].rekor_log_index` | REQUIRED for Signed + Dual-Attested | Integer index ... Absent for Unsigned items — its absence is the Unsigned tier signal. |
```

**Why it applies here:** C-1 makes `moat.tarballContentRoot` an OPTIONAL field whose absence carries meaning (default = tarball root, exclusion = `package.json`). The precedent at `moat-spec.md:786` is the same shape: a field whose absence is itself a load-bearing signal. The Round 2 sub-spec section MUST state the default explicitly and MUST state that absence is the trigger — not a Conforming-Client-discretion fallback. The exclusion list (C-6b) attaches to the default mode only; when `tarballContentRoot` is set to a subdirectory, no exclusions apply.

### Pattern: Field-name realizes lexicon concept (concept ≠ field name)

**Source:** `lexicon.md:111-119` (Flagged ambiguity: "signature" vs "attestation" vs "provenance"); SLSA's `predicateType` convention (informative — the SLSA spec uses one canonical concept name and a different JSON field name, and both are normative at their respective layers)

**Snippet:**
```markdown
- **Signature** = the cryptographic output of `cosign sign-blob` (a field inside the cosign bundle).
- **Attestation** = the protocol-level claim that a `content_hash` existed at a logged time, manifested as a Rekor entry over the canonical Attestation Payload.
```

**Why it applies here:** C-2 keeps the lexicon term "Content Directory" as the source of truth for the concept and renames the JSON field to `moat.tarballContentRoot`. The lexicon already accepts this concept-vs-realization split (see the signature/attestation distinction). Round 2 MUST add a one-line note to `lexicon.md`'s Content Directory entry stating that `tarballContentRoot` is one realization of the concept inside `package.json`, and the npm-distribution.md field-table row MUST cross-reference the lexicon entry rather than redefining the concept. This prevents future readers from treating the JSON field name as the canonical concept term.

### Pattern: Process-scope environment variable read once at start

**Source:** `reference/moat-publisher.yml:54` (`ALLOW_PRIVATE_REPO: 'false'   # set to 'true' to attest private repos`) — environment variables are set in workflow-step `env:` blocks and consumed once during the step's execution; there is no re-read mid-step

**Snippet:**
```yaml
env:
  ALLOW_PRIVATE_REPO: 'false'   # set to 'true' to attest private repos
```

**Why it applies here:** C-3 makes `MOAT_ALLOW_REVOKED` process-scope: read once at process start, re-reading mid-process is non-conformant. The reference templates already follow the read-once discipline implicitly (env vars consumed by a single Python `os.environ` lookup near the top of each step). Round 2 makes the read-once rule normative and explicit so a Conforming Client implementer cannot accidentally introduce a hot-reload mode that defeats incident-response auditability (the override is supposed to be a single, logged, time-bounded action).

### Pattern: Co-variable required for risky operation

**Source:** `moat-spec.md:633-636` (registry-source revocation MUST hard-block; publisher-source revocation MUST present, MUST warn once per session, MAY allow with explicit confirmation, MUST NOT silently continue) — the spec already requires explicit confirmation alongside the action when the operator overrides a publisher-source revocation

**Snippet:**
```markdown
publisher-source revocation = MUST present, warn once per session,
MAY allow with explicit confirmation, MUST NOT silently continue.
```

**Why it applies here:** C-3 requires `MOAT_ALLOW_REVOKED_REASON` whenever `MOAT_ALLOW_REVOKED` is non-empty. The "explicit confirmation" precedent at `moat-spec.md:635-636` is the structural model: a risky operation requires a paired, operator-supplied artifact (there: confirmation; here: a non-empty reason string). Round 2 makes the reason a hard-fail prerequisite — a Conforming Client MUST refuse to honor `MOAT_ALLOW_REVOKED` if `MOAT_ALLOW_REVOKED_REASON` is unset or empty, and MUST emit a structured error in that case. The four MOAT design tests reinforce this: the works-fine-without-it test (`CLAUDE.md:125`) catches the silent-skip failure mode where an operator sets the override and forgets the reason — without the hard fail, the override is "trust that people will comply."

### Pattern: RFC 3339 timestamps for protocol-time fields

**Source:** `moat-spec.md:784` (`content[].attested_at` REQUIRED — "Registry attestation timestamp (RFC 3339 UTC)"); `moat-spec.md:855` field-row context for lockfile timestamp fields

**Snippet:**
```markdown
| `content[].attested_at` | REQUIRED | Registry attestation timestamp (RFC 3339 UTC) |
```

**Why it applies here:** C-3 encodes per-entry expiry as `<sha256-hex>:<RFC3339-timestamp>`. The core spec already standardizes on RFC 3339 UTC for protocol timestamps, so the override-list timestamp MUST use the same form (no Unix-epoch seconds, no ISO-8601 variants without the `T` separator). A Conforming Client past the entry's RFC 3339 timestamp MUST treat the entry as if absent — the entry does not block, it does not warn; it is silently ignored. This matches the natural semantics of "the override has expired."

### Pattern: Sigstore Rekor authoritative + identity disclosure in metadata

**Source:** `moat-spec.md:1020-1071` (Canonical Attestation Payload — the bytes signed by both publisher and registry are byte-identical; the per-role distinction lives in the signing identity recorded in the bundle, not in the payload); `moat-spec.md:790` (`content[].signing_profile` — "REQUIRED for Dual-Attested" — manifest discloses publisher's expected CI signing identity); `specs/registry-action.md:69-115` (Trust Tier Determination — Rekor is consulted as authoritative)

**Snippet:**
```markdown
content[].signing_profile  REQUIRED for Dual-Attested  references signing_profile schema
```

**Why it applies here:** C-6a treats Sigstore Rekor as authoritative for Publisher attestation and uses `package.json` only for identity disclosure — `publisherSigning.{issuer, subject}` REQUIRED, `publisherSigning.rekorLogIndex` OPTIONAL discovery accelerator. The pattern mirrors `moat-spec.md:790`'s `signing_profile` field exactly: the manifest discloses what identity the consumer should expect to see in Rekor, and Rekor is consulted as the trust anchor. When `rekorLogIndex` is absent, a Conforming Client falls back to a Rekor query keyed on the canonical content hash, filtered by the disclosed `{issuer, subject}` — the identity disclosure is the trust anchor, not the log index. This pattern preserves the GitHub-flow's architecture (Rekor authoritative, manifest disclosing identity) verbatim in the npm channel.

### Pattern: Reference workflow as adoption-mechanism template

**Source:** `reference/moat-publisher.yml:1-80` (the existing reference Publisher Action workflow — a single-file YAML template that a Publisher copies into `.github/workflows/` and runs without modification); `moat-spec.md:681` (Reference-implementations bullet linking `reference/moat-publisher.yml` to `specs/github/publisher-action.md`)

**Snippet:**
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

**Why it applies here:** C-6c ships `reference/moat-npm-publisher.yml` as the npm analog. The structure mirrors `reference/moat-publisher.yml:1-80` (same `permissions` block, same Sigstore install pattern, same step-by-step style). The seven steps (`npm pack` → compute canonical hash with C-6b's exclusion → Sigstore sign → push to Rekor → write log index back into `package.json` → `npm pack` again → `npm publish`) are the npm-channel realization of the canonical "compute hash, sign payload, log to Rekor" flow. The two-pack design (pack → sign → write index → re-pack → publish) is what makes the canonical hash stable across the log-index round-trip: because `package.json` is excluded from the canonical hash by C-6b, mutating `package.json` between the two `npm pack` calls does not change the canonical hash, so the Rekor entry signed against the first pack's hash is still valid for the published tarball.

### Disambiguation: Default Content Directory — Tarball root with exclusion vs Publisher-required field vs Heuristic search

**Chosen:** Tarball root as default, with a fixed single-file exclusion list (`package.json`) when `moat.tarballContentRoot` is absent (C-1 + C-6b)
**Considered:** Publisher-required `moat.tarballContentRoot` field with no default (Round 1's effective behavior — a Publisher had to set the field to participate); Heuristic search (Conforming Client probes for common layouts: `src/`, `dist/`, `lib/`, `skill/`, falling back to root)
**Why:** The day-one test (`CLAUDE.md:121`) is the deciding lens. On day one, thousands of npm packages exist with no `moat` block. A Publisher-required field means backfill is impossible without Publisher cooperation — every backfilled package needs a Publisher to land a `moat.tarballContentRoot` field, which kills the backfill goal stated in the original ticket ("Sub-spec defines a backfill path so registries can attest pre-existing npm packages without publisher cooperation"). A heuristic search introduces ecosystem-wide ambiguity: two Conforming Clients with different probe orders can compute different Content Hashes for the same tarball, breaking the copy-survival test (`CLAUDE.md:123`) and violating the protocol's hash-as-identity invariant. A fixed default — tarball root with a single named exclusion — is the only choice that lets a Registry compute a canonical hash from the published tarball alone, with no Publisher cooperation, and that no two Conforming Clients can disagree about. The exclusion of `package.json` is forced by C-6a's identity-disclosure-in-package.json design: if `package.json` were inside the canonical hash, mutating it (to write the Rekor log index after signing) would change the hash and invalidate the signature — the chicken-and-egg the C-6 family was designed to break.
**Consequences:** Backfill becomes a real capability — a Registry Operator can run a backfill workflow over arbitrary npm packages and produce canonical hashes that any other Conforming Client can independently reproduce by fetching the same tarball. Publishers who want to scope the canonical hash to a subdirectory (e.g., `src/`) set `moat.tarballContentRoot: "src"` and the exclusion list does not apply (because the subdirectory case has no chicken-and-egg — `package.json` lives at tarball root, outside any subdirectory). The default mode's exclusion list is exactly one entry; the spec MUST forbid future expansion of this list without a sub-spec version bump (extending the exclusion list silently would change the canonical hash for every default-mode package). The npm Registry's tarball SHA-512 covers `package.json` independently, so excluding it from the MOAT canonical hash does not reduce the consumer's ability to detect tarball-level tampering — it only narrows MOAT's normative scope to the bytes a Publisher and Registry can both control identically.

### Disambiguation: Materialization-boundary anchor — "Before any byte written outside the package manager's content cache" vs "Before fetch" vs "Before unpack"

**Chosen:** "Before any byte of the tarball is written outside the package manager's content cache" (B-1)
**Considered:** "Before fetch" (block at HTTP request time — refuse to download); "Before unpack" (allow fetch into local cache, refuse unpack to install target)
**Why:** Streaming installers — npm's `pacote` is the canonical example — interleave fetch and unpack: bytes flow in via HTTPS, are decompressed on the fly, and may be tee'd into both a content-addressable cache and an extraction directory. A "before fetch" rule is too strict (it forbids ever caching a revoked tarball, even for forensic analysis after the fact, and it fights pacote's streaming architecture). A "before unpack" rule is too loose (it doesn't say where the cache lives — bytes might already be on disk inside the install target if the cache is the install target itself). The chosen anchor names the moment that matters: bytes inside the package manager's content cache are still under the package manager's control and can be discarded (pacote can abort mid-stream and delete the partial cache entry); bytes outside the cache (in the install target, in node_modules, in a workspace) are materialized — they may be loaded by an AI Agent Runtime, copied by a downstream tool, or surface elsewhere. The cache boundary is the protocol-meaningful boundary because it is the last point at which a Conforming Client can refuse without already having published bytes. This anchor lets a streaming installer comply by aborting mid-stream and discarding the partial cache entry, and lets a non-streaming installer comply by checking before fetch — both implementation choices are conformant.
**Consequences:** The pre-materialization MUST in `specs/npm-distribution.md:31` is rephrased to anchor at the cache boundary, naming the three sub-operations (resolve, fetch, unpack) and stating that whichever operation the Conforming Client chooses to refuse at, no extracted bytes may land outside the cache. A Conforming Client that fetches a revoked tarball into its content cache and then discards it on unpack-refusal is conformant; a Conforming Client that writes a revoked tarball to `node_modules/` and then deletes it is non-conformant (bytes briefly existed outside the cache, which means a parallel reader could have observed them). This phrasing also future-proofs against installers that don't have a cache-then-extract architecture (Yarn Plug'n'Play, pnpm content-addressable store) — each can map the cache-boundary concept onto its own architecture without rewording the MUST.

### Disambiguation: MOAT_ALLOW_REVOKED hardening — Process-scope + REQUIRED reason + per-entry RFC 3339 expiry vs Round 1 minimal form

**Chosen:** Process-scope, REQUIRED `MOAT_ALLOW_REVOKED_REASON` co-variable, per-entry encoded as `<sha256-hex>:<RFC3339-timestamp>`, structured override-applied logging (C-3)
**Considered:** Round 1 minimal form (simple comma-separated hash list, optional reason in operational logs, no expiry); Lockfile-only override (no env-var, hand-edit a `revocation_overrides[]` field — Round 1 design.md option D)
**Why:** The Round 1 form passes the "operator can override at all" bar but fails three of the four MOAT design tests. Works-fine-without-it (`CLAUDE.md:125`): an operator who sets the env var and forgets to record why has overridden a security boundary with no auditable record — the operation works fine without the reason, so the reason gets skipped. Enforcement (`CLAUDE.md:127`): "trust that people will write good operational logs" is exactly the answer the test forbids — the protocol provides no mechanism to detect or enforce a reason being recorded. Day-one (`CLAUDE.md:121`): the Round 1 form has no expiry, which means an override set during incident response persists across process restarts and across the eventual revocation-was-a-mistake retraction — the override outlives its purpose. The chosen form fixes all three: process-scope (no hot-reload, the override is a deliberate single action), REQUIRED reason co-variable with hard-fail enforcement (the protocol refuses to honor the override without the reason — "works fine without it" no longer applies), per-entry expiry (the override has a built-in retraction time). The lockfile-only alternative was rejected in Round 1 (high-friction for legitimate incident-response use); Round 2 doesn't revisit that decision. The structured-logging requirement is what makes the override auditable: a downstream operator reviewing logs after the incident can reconstruct exactly which hash was overridden, by whom (via the reason string), when, and until when (via the expiry).
**Consequences:** A Conforming Client that reads `MOAT_ALLOW_REVOKED` MUST also read `MOAT_ALLOW_REVOKED_REASON`; if the reason is unset or empty, the Conforming Client MUST emit a structured error and refuse to honor the override. A Conforming Client that re-reads either variable mid-process is non-conformant — the read-once discipline is what makes the override a single auditable action. Each override entry MUST be of the form `<sha256-hex>:<RFC3339-timestamp>`; entries without the timestamp delimiter MUST be ignored as malformed (no permanent overrides — the spec forbids them by syntax). A Conforming Client past an entry's RFC 3339 timestamp MUST treat the entry as if absent (no warning, no log — silent expiry). When an override is applied (the Conforming Client proceeds to materialize a hash that appeared in `revoked_hashes`), the Conforming Client MUST log a structured event whose fields include: the package identity (npm package name + version), the matched canonical Content Hash, the operator-supplied reason string, and the entry's expiry timestamp. The override-applied event is a normative log shape — implementers MUST produce it on every override application; it is the audit anchor.

### Disambiguation: Publisher signing-identity location — Sigstore Rekor authoritative + package.json identity disclosure vs Bundle-in-package.json vs Rekor-only

**Chosen:** Sigstore Rekor authoritative; `package.json` carries `publisherSigning.{issuer, subject}` REQUIRED plus optional `publisherSigning.rekorLogIndex` discovery accelerator (C-6a)
**Considered:** Round 1's `attestations[].bundle` form (full Cosign Bundle base64-encoded inline in `package.json`); Rekor-only with no `package.json` disclosure (Conforming Client queries Rekor by canonical hash and trusts whatever identity it finds)
**Why:** Round 1 embedded the full Cosign Bundle in `package.json` to allow offline verification, but the Round 2 default-Content-Directory rule (C-1 + C-6b) requires excluding `package.json` from the canonical hash to prevent the chicken-and-egg with the log index. Once `package.json` is outside the canonical hash, embedding the bundle there has no security advantage over disclosing only the identity — the bundle itself is already in Rekor (that's what Rekor is for), and the `{issuer, subject}` pair plus the canonical hash plus a Rekor query is sufficient to recover the same bundle. Embedding the bundle inflates `package.json` size by tens of KB per role, every install fetches it whether or not it verifies, and it duplicates a trust anchor that already lives in a public log designed exactly for this purpose. Rekor-only with no disclosure (the second alternative) fails because a Conforming Client receiving a hash with no expected identity has no way to detect a Sigstore-valid signature from the wrong actor — any party that can produce a valid Sigstore signature over the canonical payload would be accepted. The `{issuer, subject}` disclosure is what binds the Rekor entry to the right Publisher identity, and it mirrors the GitHub flow's `signing_profile` model exactly (`moat-spec.md:790`).
**Consequences:** The Round 1 `moat.attestations[].bundle` field is replaced by the new `publisherSigning` block at the top level of the `moat` object. `publisherSigning.issuer` and `publisherSigning.subject` are REQUIRED; `publisherSigning.rekorLogIndex` is OPTIONAL. When `rekorLogIndex` is present, a Conforming Client MUST fetch the Rekor entry by index and MUST validate that the entry's signing identity matches `publisherSigning.{issuer, subject}` exactly. When `rekorLogIndex` is absent, a Conforming Client falls back to a Rekor query keyed on the canonical Content Hash and MUST filter results by the disclosed `{issuer, subject}` — the disclosed identity is the trust anchor, the log index is only a discovery accelerator. The Round 1 `attestations[]` array carrying both `role: "publisher"` and `role: "registry"` entries is preserved for the registry side (a Conforming Client still walks `attestations[]` to find registry entries); only the publisher side moves into `publisherSigning`. This consolidates the per-role cardinality (exactly one Publisher per package) into the JSON schema rather than enforcing it via the Round 1 "duplicate role is malformed" rule. The Round 2 sub-spec MUST cross-reference `moat-spec.md:790`'s `signing_profile` field-shape so a reader sees the cross-channel symmetry. A new ADR (proposed 0006) is warranted because this is a load-bearing change to the `package.json` schema introduced in Round 1.

### Disambiguation: Hash exclusion list — Single fixed file in default mode vs No exclusions vs Configurable exclusion list

**Chosen:** Default-mode-only exclusion of exactly one file (`package.json`); subdirectory mode applies no exclusions (C-6b)
**Considered:** No exclusions (default mode hashes the entire tarball root including `package.json`); Configurable exclusion list (Publisher declares `moat.hashExclude: ["package.json", ...]`)
**Why:** The chicken-and-egg between `publisherSigning.rekorLogIndex` and the canonical hash is the binding constraint. Without an exclusion, writing the log index back into `package.json` after Sigstore signing changes the canonical hash, invalidating the signature — the C-6c reference workflow's two-pack design becomes impossible without the exclusion. "No exclusions" is rejected on this ground alone. A configurable exclusion list (the second alternative) opens a far larger attack surface: a malicious Publisher could set `moat.hashExclude: ["malicious-payload.js"]` and have the canonical hash cover only the benign files, attesting bytes the Conforming Client never executes. The exclusion list itself would have to live inside `package.json` and would also need to be inside the canonical hash (otherwise it's the same chicken-and-egg again at one remove), which forces a circular schema. A fixed single-file exclusion ties exactly to the protocol's needs and admits no Publisher-driven expansion. The exclusion is forced to `package.json` specifically because that is the file the C-6c reference workflow mutates between the two `npm pack` calls — no other file in a normal npm package is npm-injected metadata that the Publisher both signs and then needs to mutate post-signing. The npm Registry's tarball SHA-512 covers `package.json` independently of MOAT (`specs/npm-distribution.md:21`), so a consumer who wants tarball-level integrity over `package.json` already has the npm primitive — MOAT does not lose meaningful security by excluding it. The subdirectory mode does not need the exclusion: when `moat.tarballContentRoot: "src"`, the canonical hash domain is `src/`'s contents, and `package.json` (at tarball root, outside `src/`) is outside the hash domain by construction.
**Consequences:** The Round 2 sub-spec MUST state that the default-mode exclusion list contains exactly one entry (`package.json` at tarball root) and MUST forbid future Publisher-driven extension of this list without a sub-spec version bump. The subdirectory-mode rule "no exclusions apply" MUST be stated explicitly to prevent a Conforming Client from carrying the default-mode exclusion through into subdirectory mode. The exclusion targets `package.json` at tarball root only — a `package.json` file inside a subdirectory (e.g., `src/package.json` for a workspace member) is hashed normally in subdirectory mode and is not excluded in default mode either (the exclusion is path-anchored to the tarball root, mirroring `reference/moat_hash.py:60`'s root-level-only exclusion of `moat-attestation.json`). A new ADR (proposed 0007) is warranted because this exclusion rule is a normative, security-relevant constraint that will be referenced repeatedly by Conforming Client implementers and Registry Operators running backfill.

## Design Questions

The Round 2 design concept (signed off 2026-05-09T03:13:32Z) resolves the architectural decisions concretely. The questions remaining at the design layer are narrow editorial choices about how to express decisions already made — wording, log-event field names, table layouts. These are A/B/C-able because each option produces a working spec; the choice is about which form best fits the existing house style.

1. **What field names does the override-applied structured log event carry?**
   - A) `package_identity`, `content_hash`, `override_reason`, `override_expiry` — long-form, self-documenting, parseable without context.
   - B) `pkg`, `hash`, `reason`, `expiry` — short, terse, matches the structured-event style in `reference/moat-publisher.yml`'s log-line patterns.
   - C) `package`, `content_hash`, `reason`, `expires_at` — middle ground; uses `expires_at` (RFC 3339-friendly suffix) and `package` (npm-native singular term).
   - **Recommended:** C — `expires_at` matches the `attested_at` convention at `moat-spec.md:784` (RFC 3339 timestamp field naming); `content_hash` matches the lexicon term verbatim; `package` is npm-native and unambiguous in this context; `reason` is short and self-explanatory. A long-form names duplicate context already present in the surrounding log envelope; B short-form sacrifices grep-ability for one-time-write brevity that doesn't matter to operators reading the event after the fact.

2. **What form does the npm provenance disagreement table take in the npm Provenance section?**
   - A) Four-row pipe table with columns `(npm provenance, MOAT attestation, Conforming Client display, Trust Tier impact)` — flat, all four states visible at a glance.
   - B) Four bullet points, each starting with a bold-label state name (`**Both present:**`, `**MOAT only:**`, `**Provenance only:**`, `**Neither:**`) followed by the prose for each row — narrative, easier to read inline, harder to scan.
   - C) A two-axis table (`npm provenance: present | absent` × `MOAT: present | absent`) with cells containing the per-cell display rule — structurally honest about the two-axis nature but harder to render compactly in Markdown.
   - **Recommended:** A — the existing sub-specs use pipe tables for state matrices (`specs/publisher-action.md:202-205` visibility/behavior matrix; `specs/registry-action.md:127-131` reuse-criteria summary) and the four-row form is the closest match to that house style. The two-axis form (C) is structurally accurate but would render as a 2×2 grid of run-on cells that's harder to read than four discrete rows. Bullet form (B) loses the at-a-glance scanability the table provides — readers comparing the four cases need columns aligned, not paragraphs.

3. **How is the `moat.tarballContentRoot` rename communicated in the npm-distribution.md field table — replace the row, or replace-with-historical-note?**
   - A) Replace the field-table row with the new name, no historical note — Round 2 is a Draft-to-Draft edit and the v0.1.0 → v0.2.0 bump is a permitted breaking change in Draft status (`moat-spec.md:14-16` "This draft has not been validated by any implementations").
   - B) Replace the row, but add a one-line "Renamed from `moat.contentDirectory` in v0.1.0" note in the field-table row's Description column — preserves a discoverable history pointer for any pre-v0.2.0 reader.
   - C) Replace the row plus add a `## Migration from v0.1.0` informative section enumerating the field renames — heavy-handed for a Draft-status spec with no implementations, but unambiguous.
   - **Recommended:** A — `moat-spec.md:22` ("Zero adopters. No implementations exist beyond draft tooling concepts. This is a greenfield spec. Design for correctness, not continuity.") explicitly authorizes Draft-status breaking changes without migration scaffolding. The CHANGELOG `[Unreleased]` entry for Round 2 already records the rename in the public-facing record; duplicating that pointer inside the spec body is process-metadata leak (the kind of thing `.claude/rules/changelog.md:32` flags as "if a reader can't act on the detail without context from an internal thread, cut it"). If a v0.1.0 reader exists, their action is "read v0.2.0 instead," not "follow a migration path."

## Decisions made (not questions)

These are settled by the Round 2 design concept; listed here for the Structure phase to consume directly.

- **A-1 — `moat-spec.md:9` Sub-specs line cites `specs/npm-distribution.md`** — one-line edit to append the new sub-spec to the existing comma-separated list at `moat-spec.md:9`.
- **A-2 — `.claude/rules/changelog.md:40` cites `specs/github/publisher-action.md`** — one-line edit replacing the pre-reorg path with the post-reorg path; tooling-only file (`.claude/`) so per `.claude/rules/changelog.md:21` no CHANGELOG entry is required.
- **B-1 — Materialization-boundary anchor is "before any byte of the tarball is written outside the package manager's content cache"** — replaces the Round 1 phrasing at `specs/npm-distribution.md:29`; conformant Conforming Clients MAY refuse at resolve, fetch, or unpack so long as no extracted bytes land outside the cache.
- **B-2 — Four-state (provenance × MOAT) disagreement table** — added to the npm Provenance section (`specs/npm-distribution.md:107-115`); covers (both, MOAT-only, provenance-only, neither); spec MUST state that provenance and Trust Tier are orthogonal axes.
- **C-1 — Default Content Directory = tarball root with C-6b exclusion** — when `moat.tarballContentRoot` is absent, the canonical Content Directory is the unpacked tarball root, with `package.json` excluded; subdirectory mode applies no exclusions.
- **C-2 — Field rename `moat.contentDirectory` → `moat.tarballContentRoot`** — the lexicon term "Content Directory" is unchanged; `lexicon.md`'s Content Directory entry gains a one-line note that `tarballContentRoot` is the JSON field name realizing the concept.
- **C-3 — `MOAT_ALLOW_REVOKED` hardening** — process-scope only (read once at process start); REQUIRED `MOAT_ALLOW_REVOKED_REASON` co-variable with hard-fail enforcement; per-entry encoded as `<sha256-hex>:<RFC3339-timestamp>`; entries past expiry MUST be ignored as if absent; structured override-applied log event MUST be emitted on every override application.
- **C-6a — Publisher attestation: Sigstore Rekor authoritative + `package.json` identity disclosure** — `publisherSigning.{issuer, subject}` REQUIRED, `publisherSigning.rekorLogIndex` OPTIONAL; Conforming Clients MUST validate Rekor entry's signing identity matches `publisherSigning.{issuer, subject}`; Round 1's `attestations[].bundle` field for the Publisher role is removed (Registry role preserved in `attestations[]`).
- **C-6b — Hash exclusion list: exactly one file in default mode (`package.json` at tarball root)** — subdirectory mode applies no exclusions; the spec MUST forbid Publisher-driven extension of the exclusion list.
- **C-6c — Reference Publisher workflow `reference/moat-npm-publisher.yml`** — seven steps (`npm pack` → compute canonical hash → Sigstore sign → push to Rekor → write log index back to `package.json` → re-pack → `npm publish`); triggered on release tag push or manual dispatch; mirrors `reference/moat-publisher.yml`'s structure (`reference/moat-publisher.yml:1-80`); non-GHA Publisher support is deferred (out of scope for this ship per the Round 2 concept).
- **`lexicon.md` — `tarballContentRoot` realization note** — one-line addition to the Content Directory entry stating that `tarballContentRoot` (in `package.json`) is one realization of the concept; the lexicon term remains the source of truth.
- **`specs/npm-distribution.md` version bump** — v0.1.0 → v0.2.0; Draft status retained.
- **CHANGELOG `[Unreleased]` entry** — bullets under `### Changed` for the Round 2 sub-spec amendments and `### Added` for the reference workflow; `.claude/` and `reference/` paths follow `.claude/rules/changelog.md:21`'s tooling-only exclusion (the workflow file is reference content per `moat-spec.md:681`'s precedent of citing `reference/moat-publisher.yml`, so the CHANGELOG `### Added` entry for the npm reference workflow IS required as a spec-surface artifact, not a tooling-only one).
- **Website mirror sync** — `website/src/content/docs/spec/npm-distribution.md` MUST be byte-identical (after the Starlight front-matter) to canonical `specs/npm-distribution.md`; mirror is updated in the same commit per Round 1 precedent at `CHANGELOG.md:35`.
- **Round 1 conformance scripts continue to pass** — none of the Round 2 changes modify the Round 1 normative surfaces those scripts cover; new conformance scripts MAY be added for the Round 2 sections (default-Content-Directory hashing, override-event log shape, exclusion-list semantics).

## Out of Scope

- **Layering rule + GitHub-ism extraction in `moat-spec.md` / `specs/moat-verify.md`** — deferred to a separate ship.
- **Aggregator UI Trust Tier strings + visual guidance** — deferred to a separate ship.
- **Standalone CLI for non-GHA npm Publishers** — `reference/moat-npm-publisher.yml` is GitHub-Actions-shaped only; non-GHA reference Publisher tooling is a future concern.
- **Multi-provider OIDC examples** — the reference workflow uses GitHub Actions OIDC only; OIDC providers other than GitHub are not enumerated in this ship.
- **Enumerating npm-injected metadata files beyond `package.json`** — the exclusion list is fixed at exactly `package.json`; if future npm-injected files (e.g., `.npmrc`-injected fields, metadata blocks added by registry middleware) need exclusion, they require their own sub-spec amendment.
- **npm Registry first-class metadata field** — proposing a top-level npm Registry metadata field (e.g., `dist.attestations[].moatAttestation`) outside `package.json` is out of scope; this ship uses `package.json` only.
- **Other registry transports** — PyPI, Cargo, Maven, container registries; each needs its own sub-spec.
- **Runtime gating of execution** — outside MOAT's protocol boundary; the materialization-boundary anchor is the protocol's last word on revocation.

## Interfaces affected (preview)

- `specs/npm-distribution.md` — version bump v0.1.0 → v0.2.0 Draft; field-table row rename (`moat.contentDirectory` → `moat.tarballContentRoot`); new default-Content-Directory rule with exclusion list; materialization-boundary anchor rephrased; `MOAT_ALLOW_REVOKED` section expanded with reason co-variable, expiry, and override-applied log event; Publisher attestation moves from `attestations[].bundle` (publisher role) to top-level `publisherSigning` block; `attestations[]` retained for Registry role only; npm Provenance section gains four-state disagreement table.
- `moat-spec.md:9` — Sub-specs line gains `specs/npm-distribution.md` cross-reference.
- `lexicon.md` — Content Directory entry gains a one-line note that `tarballContentRoot` (in `package.json`) is one realization of the concept; lexicon term unchanged.
- `.claude/rules/changelog.md:40` — example-anchor reference updated from `specs/publisher-action.md` to `specs/github/publisher-action.md`.
- `reference/moat-npm-publisher.yml` — new file; seven-step GitHub Actions workflow mirroring `reference/moat-publisher.yml`'s structure.
- `CHANGELOG.md` — `[Unreleased]` gains `### Changed` entries for the sub-spec amendments and `### Added` entry for the new reference workflow; bold-label form per `.claude/rules/changelog.md:48`.
- `website/src/content/docs/spec/npm-distribution.md` — website mirror updated to match canonical sub-spec byte-for-byte (after front-matter).
- `.ship/npm-distribution-spec/adr/` — three new Proposed ADRs auto-drafted by the ship-adr-handler hook from this design's three Disambiguation blocks (proposed 0005 default Content Directory, 0006 publisher signing-identity location, 0007 hash exclusion list); the materialization-boundary, override-hardening, and field-rename Disambiguations also produce ADRs (proposed 0008, 0009, 0010 — the hook drafts one per `### Disambiguation:` header).

DESIGN_COMPLETE
