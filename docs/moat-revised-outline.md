# MOAT Revised Architecture — Working Outline

**Status:** Working design document — v0.4.0
**Sub-specs:** [`specs/publisher-action.md`](../specs/publisher-action.md), [`specs/moat-verify.md`](../specs/moat-verify.md)
**Decisions:** [`docs/decisions/resolved.md`](decisions/resolved.md)
**OWASP alignment:** [`docs/owasp-alignment.md`](owasp-alignment.md)
**Author:** Holden Hewett
**Date:** 2026-04-06

> **Adoption status:** Zero adopters. No implementations exist beyond draft tooling concepts. This is a greenfield spec.
> Design for correctness, not continuity.

---

## What MOAT Is

**Model for Origin Attestation and Trust** — a protocol for secure distribution of AI agent content through registries.

MOAT defines how registries publish, sign, and distribute collections of agent content. It is a distribution protocol,
not a metadata format.

MOAT answers three questions at the registry level:

- **Has this been tampered with since the registry signed it?** (content hash + signature)
- **Which registry attested to this content?** (registry identity + Rekor transparency)
- **Where did the registry source it from?** (source URI + lineage)

MOAT verifies what a registry claims — it does NOT answer whether registry operators are acting in good faith,
whether content is safe to use, or whether a publisher identity is legitimate. Choosing which registries to trust
is an End User decision; MOAT provides the tools to verify what those registries attest.

MOAT does NOT define:

- The internal format of content items
- Per-file metadata within content items
- Individual file attestation outside a registry context

## Actors

MOAT involves six distinct actors. They are not interchangeable.

**End User** - The human who chooses which registries to trust and who approves installs or use of content through a conforming client. MOAT requires clients to surface trust tier, `risk_tier`, and revocation state clearly so the End User can make an informed decision.

**Publisher** - Creates content and keeps it in a source repository. A publisher may adopt the Publisher Action to produce source-side attestations, but MOAT does not require the publisher to run a registry or implement client behavior.

**Registry Operator** - Runs a registry that crawls or ingests content from source repositories, computes content hashes, signs registry metadata, and publishes a manifest for clients to consume. The Registry Operator is the party making the registry-level attestation.

**Conforming Client** - The install and management tool that implements MOAT's normative client behavior. A conforming client fetches manifests, verifies signatures and content hashes, maintains a lockfile, checks revocations, and surfaces trust signals before install or use. A conforming client is not an AI agent runtime.

**AI Agent Runtime** - A system such as Claude Code, Gemini, Cursor, or Windsurf that loads or executes content after installation. AI agent runtimes are outside the MOAT protocol boundary. MOAT does not define runtime behavior, sandboxing, permission enforcement, or execution semantics.

**moat-verify** - A standalone verification tool that audits the MOAT trust chain for a content item. It verifies, but does not install, manage, or execute content. It is therefore not a conforming client and not a runtime.

### Use Cases

**End User** - Chooses which registries to trust and decides whether to install, load, or remove content based on the trust tier, `risk_tier`, and revocation state surfaced by a conforming client. This includes individual users and team or enterprise administrators enforcing local policy.

**Publisher** - Wants accurate source attribution, visible lineage for forks, and an optional low-friction way to co-attest content from the source repository.

**Registry Operator** - Publishes a curated catalog with verifiable registry attestations that any conforming client can consume.

**Conforming Client** - Implements install-time and sync-time protocol behavior: fetch manifest, verify signatures and hashes, maintain a lockfile, surface trust signals, and enforce revocation behavior consistently for the End User.

**AI Agent Runtime** - Loads or executes already-installed content after a conforming client has completed verification and placement. It appears here to make the boundary explicit: MOAT intentionally defines no runtime behavior for it.

**moat-verify** - Lets any reader independently audit the trust chain for a specific content item without installing or executing it. Its use case is diagnosis, validation, and interoperability testing rather than installation or runtime management.

---

## Why This Architecture

Research across npm, Cargo, Go modules, Homebrew, mise, SLSA, in-toto, and TUF points to a stable pattern:

1. The package or content directory is the trust unit.
2. The registry is the trust decision End Users actually make.
3. Signing that scales is either keyless or hidden behind tooling.
4. Publisher effort must be near zero or adoption fails.
5. Per-file integrity is an implementation detail, not a protocol boundary.
6. Files shared outside a distribution channel are not solvable at protocol level.

---

## Core Design Principles

**Creators do as little as possible.** Attestation is generated by tooling, not by manual publisher workflow.

**The registry is the trust unit.** End Users choose a registry; conforming clients verify what that registry attested.

**Secure path is the default path.** Unsigned content can still work, but the trust signal is explicit.

**No central infrastructure required to operate a registry.** A GitHub repo with a GitHub Action is enough to run one.
Verification of Signed content depends on Rekor availability.

**Simplicity over completeness.** The hashing and verification path should be straightforward enough to implement
correctly in one pass.

---

## The Three Layers

### 1. Content

Skills, hooks, agents, rules, MCP configs, commands, and similar artifacts live wherever creators already keep them.
MOAT treats the content directory as opaque and hashes it as a unit.

### 2. The Registry

Anyone can run one. A registry declares sources in a config file, runs a scheduled CI job that crawls sources and signs
everything with its own identity, and publishes a signed registry manifest — the trust anchor conforming clients use.
Hosting is a static file server, a git repo, or anything that serves the manifest at a known URL. The spec defines the
format, not the host.

The registry manifest is the core artifact of MOAT: registry identity, signing profile, an index of all content items
with content hashes, per-item metadata, and the registry's signature logged to Rekor.

The **Publisher Action** (optional) allows source repos to co-sign their own content, enabling the Dual-Attested tier.
Registries can also crawl from sources with no MOAT awareness. Full spec:
[`specs/publisher-action.md`](../specs/publisher-action.md)

### 3. Conforming Clients

A conforming client is the install and management layer that implements MOAT's normative client behavior. It may be a
package manager, CLI installer, IDE-side content manager, or similar tool. It is not an AI agent runtime such as
Claude Code, Gemini, Cursor, or Windsurf.

The spec defines what a conforming client must do on install and sync:

- Require explicit End User action to add a trusted registry
- Verify the registry manifest using the declared signing profile
- Verify content hashes against the manifest on install
- Maintain a local lockfile of installed content hashes. Minimum conforming lockfile schema:

  ```json
  {
    "moat_lockfile_version": "1",
    "entries": [
      {
        "name": "string",
        "type": "skill|subagent|rules|command",
        "registry": "https://...",
        "content_hash": "sha256:<hex>",
        "attested_at": "ISO8601",
        "pinned_at": "ISO8601"
      }
    ]
  }
  ```

  `content_hash` is the normative identity. `attested_at` comes from the manifest item. `pinned_at` records when the
  the End User installed or pinned this version. Conforming clients MAY add additional fields but MUST include all six.
  Lockfile interoperability requires all conforming clients to use this schema — a lockfile from one conforming
  client must be readable by another.
- Surface trust tier and `risk_tier` before install confirmation
- Surface revocation source attribution and treat publisher revocations as warnings, registry revocations as the gating
  signal
- On manifest sync: check all installed content hashes against the updated `revocations` array; apply hard-block for
  registry revocations and warn-on-use for publisher revocations (see Revocation mechanism above)

The conforming client is the component responsible for trust decisions at install or load time; the runtime consumes
content only after that step.

---

## Content Types

MOAT currently defines four normative content types, with two more deferred:

| Type       | Category dir | Notes                                                         |
|------------|--------------|---------------------------------------------------------------|
| `skill`    | `skills/`    | Reusable instruction sets                                     |
| `subagent` | `subagents/` | Specialized persona definitions with controlled tools/context |
| `rules`    | `rules/`     | Behavior configuration files and rule bundles                 |
| `command`  | `commands/`  | User-invoked slash commands                                   |
| `hook`     | `hooks/`     | Deferred — directory reserved, type not yet normative         |
| `mcp`      | `mcp/`       | Deferred — directory reserved, type not yet normative         |

Each subdirectory within a category directory is one content item. The content hash covers that subdirectory as a unit.

### Repository Layout

Canonical layout:

```text
commands/
hooks/
mcp/
rules/
skills/
subagents/
moat-attestation.json
```

The Publisher Action uses a two-tier discovery model:

- **Tier 1:** Canonical category directories
- **Tier 2:** `moat.yml` for custom layouts; when present it overrides Tier 1

`moat-attestation.json` is excluded from content hashing to avoid a circular dependency.

---

## Trust Model

### Trust Tiers

| Tier | Meaning |
|---|---|
| **Dual-Attested** | Registry-signed and independently attested by the source repo CI for the same content hash |
| **Signed** | Registry-signed with a Rekor transparency log entry. Tamper-evident. Registry-attested. |
| **Unsigned** | No MOAT attestation. Works, but labeled clearly. |

`Dual-Attested` will be rare at launch. Its absence is not a negative signal; `Signed` is the standard tier.

### Registry Trust

- Adding a registry is an explicit End User decision
- Registry signing identity is declared and verifiable
- Signing identity changes require client re-approval
- Registries are responsible for curation in their own domain

### Content Hashing

The content hash identifies a content directory by canonical byte sequence using the normative `moat_hash.py` reference
implementation. Resolved normalization rules, exclusion rules, and conformance expectations are archived in
[`docs/decisions/resolved.md`](decisions/resolved.md).

### Trust Anchor Model

**The per-item Rekor transparency log entry is the authoritative trust anchor for each content item.** The registry
manifest signature establishes integrity of the manifest index (the list of Rekor references). Both are required —
they serve different roles:

- **Manifest signature:** proves the registry published this index without tampering. Verified once per manifest fetch.
- **Per-item Rekor entry:** proves this specific `content_hash` was attested at a logged point in time. Verified for
  each item being installed or verified.

A conforming verifier such as `moat-verify` MUST verify the manifest signature AND MUST verify the per-item Rekor entry for each item under
verification. Rekor unavailability is a hard failure — there is no fallback to manifest-signature-only when Rekor is
offline. This is a deliberate design choice: silent degradation to an unverified-transparency state creates a
downgrade path attackers can exploit.

The Rekor instance URL is configurable. Organizations running a private Rekor-compatible instance satisfy the Rekor
connectivity requirement — there is no hard dependency on `rekor.sigstore.dev`.

**Offline verification of already-installed content** uses the lockfile rather than re-running the full verification
flow. In this mode, the lockfile is the trust anchor — Rekor is not consulted. Offline lockfile verification
re-hashes the local content directory and compares against `content_hash` in the lockfile entry, confirming on-disk
content matches what was installed. It does NOT re-verify current registry state: revocations issued since install,
superseding versions, and trust tier changes are not reflected. Conforming clients SHOULD surface this
distinction when operating in lockfile mode.

This resolves Issue 15.

### Signature Envelope

The core spec defines a platform-agnostic signing envelope. Informative profiles currently include:

- `sigstore` for keyless OIDC signing via Fulcio/Rekor
- `ssh` for operator-managed signing

---

## Scope Boundary

MOAT is scoped to **registry-distributed content**.

Out of scope:

- Informally shared standalone files
- Per-file metadata inside content items
- Content format definitions such as SKILL.md schemas
- AI agent runtimes and execution environments
- Runtime sandboxing or permission enforcement
- Cross-item dependency graphs

MOAT governs registry-distributed content, attestation, install-time verification, lockfiles, and revocation
signaling. It does not define what an AI agent runtime does with already-installed content, and it does not define
runtime sandboxing, permission enforcement, or execution semantics.

MOAT's trust guarantee covers the content directory as a unit. Dependencies outside that directory are outside the
guarantee and need to be surfaced by companion specs and conforming clients.

---

## Fork and Lineage Handling

If a repo is forked and the content is unchanged, registries can preserve lineage with `derived_from` while attesting
the fork under a new identity. If the content changes, it becomes a new content hash with explicit lineage. Suspicious
attribution conflicts are surfaced to End Users; they are not automatic hard blocks.

---

## What the Spec Defines

### Normative core

These items are required for conformance. A conforming registry, a conforming client, and a conforming verifier such as
`moat-verify` all
implement exactly these.

- **Content type registry** — normative list of current types (`skill`, `subagent`, `rules`, `command`), category
  directory names, and deferred types (`hook`, `mcp`).
- **Repository layout convention** — canonical directory structure and two-tier discovery model (`moat.yml` override).
- **Registry manifest format** — the signed document a registry publishes. The core artifact of MOAT. Per-item entries:
  `name`, `display_name`, `content_hash`, `source_uri`, `attested_at`, `derived_from`, `scan_status`, `risk_tier`.
- **Content hashing algorithm** — deterministic, one-pass, Go dirhash-inspired. Defined by normative reference
  implementation (`moat_hash.py`), not pseudocode.
- **Hash format** — `<algorithm>:<hex>` with no length constraints.
- **Signature envelope format** — platform-agnostic signing model.
- **Trust tier model** — Dual-Attested / Signed / Unsigned. Absence of Dual-Attested is NOT a negative signal.
- **Client verification protocol** — what a conforming client must check on install.
- **Revocation mechanism** — `revocations` array in manifest (REQUIRED; empty if none), four reason values, client
  behavior rules. Normative client behavior when syncing a manifest update that adds a revocation entry for
  already-installed content:

  | Revocation source | Required client behavior |
  |---|---|
  | Registry | MUST hard-block all use of that content. Client refuses to load or execute the item. Block is in effect until the End User explicitly removes the content or installs a non-revoked version. |
  | Publisher | MUST warn on next use attempt with revocation reason. MAY allow use with explicit per-session End User confirmation. MUST NOT silently continue. |

  In both cases, the client MUST surface the revocation reason and the registry that issued the revocation.
- **Lineage model** — `derived_from` for forks and adaptations.
- **Version semantics** — `version` is an optional display label; content hash is normative identity; `attested_at` for
  freshness.
- **`scan_status` structure** — per-item manifest field; `not_scanned` is valid. The `scanners` array entry schema:

  ```json
  { "name": "string", "version": "string", "result": "pass|fail|inconclusive", "scanned_at": "ISO8601" }
  ```

  `name` is a controlled value — registries MUST use the canonical name for well-known scanners (e.g.
  `"snyk-mcp-scan"`, `"semgrep"`) to enable aggregation. Additional fields are permitted. Free-form scanner name
  strings defeat cross-registry aggregation and do not conform.
- **`risk_tier` definition** — per-item manifest field; registry-assigned, never publisher self-declared. Valid values
  and their normative criteria:

  | Value | Meaning | Observable criteria |
  |---|---|---|
  | `L0` | No analysis performed | No scanner entries in `scan_status`; no human review on record |
  | `L1` | Automated scan only | At least one entry in `scan_status.scanners` with a machine-generated result |
  | `L2` | Automated scan + registry human review | Scanner entries present; registry records a human review of scan output |
  | `L3` | Independent security review | Third-party security audit on record; registry provides a review reference URL |
  | `not_analyzed` | Registry has not yet assessed this item | Absence of analysis; expected for newly indexed content |
  | `indeterminate` | Assessment was inconclusive | Registry ran analysis but could not assign a definitive tier |

  A registry assigning `L2` without documented human review, or `L3` without a third-party audit reference, is not
  conforming. Two registries assigning different tiers to the same `content_hash` is not a protocol error — registries
  may have different review practices. Clients that gate on `risk_tier` SHOULD surface the assigning registry identity
  alongside the tier value.

### Reference implementations (normative behavior, separate artifacts)

- **`moat_hash.py`** — Python reference implementation. A conforming implementation produces identical output for all
  test vectors. Two independent implementations in different languages must pass all test vectors before the spec
  advances beyond Draft.
- **`moat-verify`** — Standalone verification script. Spec: [`specs/moat-verify.md`](../specs/moat-verify.md)
- **Publisher Action** — GitHub Actions workflow for source repos. Spec:
  [`specs/publisher-action.md`](../specs/publisher-action.md)

### Informative profiles

- **Sigstore profile** — keyless OIDC signing via Fulcio/Rekor.
- **SSH profile** — SSH key signing for individual operators.

---

## Publisher Action

The Publisher Action is the primary adoption mechanism for the `Dual-Attested` tier. Any source repo adds a single
workflow file — no key management, no MOAT-specific knowledge required.

The Publisher Action is publisher-side CI tooling. It is not a registry, not a conforming client, and not an AI
agent runtime.

On push, it discovers content items, computes content hashes, signs each with `cosign sign-blob` via Sigstore keyless
OIDC, and writes `moat-attestation.json` to the repo root with Rekor references. The commit is guarded against
triggering recursive runs.

Publisher revocation also flows through this action: publishers add a revocation entry, trigger the workflow, and
optionally notify registries by webhook. Publisher revocations are warnings, not hard blocks.

**Full specification:** [`specs/publisher-action.md`](../specs/publisher-action.md)

---

## moat-verify

`moat-verify` is a standalone Python 3.9+ verification tool. It imports `moat_hash.py` directly, requires `cosign` on
PATH, and lets anyone verify MOAT-attested content without depending on a specific client implementation.

`moat-verify` is a diagnostic verification tool. It is not a conforming client because it does not install or manage
content, and it is not a runtime because it does not execute content.

Usage:

```bash
moat-verify <directory> --registry <url> [--source <uri>] [--json]
```

Verification flow: compute content hash → fetch registry manifest → look up hash → verify registry Rekor attestation →
optionally verify publisher Rekor attestation. Rekor unavailability is always a hard failure, never a silent pass.

Every run ends with a required "NOT verified" block so readers do not mistake cryptographic verification for a safety
guarantee.

**Full specification:** [`specs/moat-verify.md`](../specs/moat-verify.md)

---

## Discovery

A community-owned registry index repo can list known registries, with Syllago shipping one default discovery source.
That creates a de facto trust root for discovery and therefore needs explicit governance before the spec advances.

---

## Open Issues

Resolved decisions are archived in [`docs/decisions/resolved.md`](decisions/resolved.md).

**Issue 4: Registry manifest size and pagination** For large registries, the manifest could become unwieldy. Candidate
resolution: no pagination (split into sub-registries if needed); pagination is a MAY for future extensibility.
Requires an explicit decision before Draft.

**Issue 9: Registry index governance** If one index ships as the default discovery source, it becomes a legitimacy root
whether named as such or not. Inclusion criteria, removal policy, incident response, namespace disputes, appeals, and
signing all need explicit governance.

**Issue 10: Publisher authentication model** How publishers authenticate to registries and how clients authenticate to
private registries is still open. OIDC should be the primary path; long-lived tokens, if allowed, must be clearly
treated as the weaker compatibility path.

**Issue 11: Federation security** Federation introduces SSRF risk, trust laundering risk, and upstream-input
sanitization risk. Response size limits and timeouts should be conformance requirements when federation exists.

**Issue 12: Algorithm deprecation guidance** The `<alg>:<hex>` format supports agility but does not yet define forbidden
algorithms, deprecation signaling, or required client behavior for deprecated algorithms.

**Issue 13: Offline verification** Clients need a conforming offline verification model for already-installed content:
cached manifests, lockfile behavior, proof retention, and staleness handling all need specification.

**Issue 14: Cross-registry blocklist federation** Client-side cross-registry revocation matching exists conceptually,
but a registry-side sharing format for urgent revocation signals is still undefined.

~~**Issue 15: Trust anchor ambiguity**~~ **Resolved.** Per-item Rekor entry is the authoritative trust anchor. Manifest
signature establishes index integrity. Both required. See Trust Anchor Model in the Trust Model section.

**Issue 16: Anti-rollback / anti-freeze model** Current freshness guidance does not defend against replay of old but
still valid manifests. Either MOAT adopts explicit freshness semantics or it explicitly disclaims that threat class.

**Issue 17: "No central infrastructure" language** Operating a registry does not require central infrastructure, but
verifying Signed content depends on Rekor availability. The spec language needs to keep that distinction explicit.

**Issue 18: Publisher Action source repo mutation** Writing `moat-attestation.json` back to source repos creates commit
churn and policy friction. The alternative of bundles or release artifacts needs evaluation before the Publisher Action
spec is finalized.

**Issue 19: GitHub identity verification claims** GitHub exposes richer OIDC claims than the current simple
subject-pattern check. The spec needs to decide which claims are authoritative and whether stable IDs should be
preferred over mutable names.

**Issue 20: Binary revocation states (REVOKED / YANKED)** Third-party feedback proposes collapsing the four revocation
reason codes (`malicious`, `compromised`, `deprecated`, `policy_violation`) into two machine-actionable states:
`REVOKED` (hard block) and `YANKED` (warn, allow). The current four-code model preserves more human context, but the
client behavior is already effectively binary. Decision needed: keep the taxonomy, or collapse to states plus a
mandatory `details_url`.

**Issue 21: Threat feeds vs cross-registry revocation** Third-party feedback argues that any trusted registry being able
to warn about content from another registry creates trust bleeding and DoS potential. The proposed alternative is a
standardized optional `threat-feed.json` maintained by a trusted community or security operator. That may be cleaner,
but it reintroduces central infrastructure and governance. Decision needed: keep cross-registry revocation, replace it
with threat feeds, or support both with different trust semantics.

**Issue 22: Archive hashing vs directory hashing** Third-party feedback recommends deterministic archive hashing instead
of hashing directory contents directly. That fits ecosystems where publishers hand registries canonical archives, but
MOAT's current model is registry-side crawling of source content. If MOAT ever grows creator-side packaging tooling,
archive hashing should be reconsidered. This issue is recorded mainly to preserve the rationale behind the current
direction.

**Issue 23: SSH profile retention vs CI-only mandate** Third-party feedback recommends removing the SSH signing profile
and making CI-backed signing the only path to a Signed tier. That would raise the trust floor but also raise adoption
friction. Decision needed: whether SSH remains an informative profile, disappears entirely, or survives with a visibly
lower trust signal than CI-backed keyless signing.

**Issue 24: Runtime dependency scope** Third-party feedback argues that unlocked runtime dependencies outside the
content directory make MOAT's signing guarantee incomplete. The current design explicitly scopes trust to the content
directory and defers dependency graphs to a future version. Decision needed: whether the spec should add stronger
disclaimer language
now and whether companion specs should require declaration of external dependencies so clients can surface them.

---

## OWASP Alignment

MOAT is validated against six OWASP standards: CI/CD Security Top 10 (critical), Top 10 for Agentic Applications 2026
(critical), Top 10:2025 (high), LLM Top 10:2025 (high), Agentic Skills Top 10:2026 (high), and API Security Top 10:2023
(medium).

Core coverage: ASI04, CICD-SEC-9, AST01, AST02, LLM03:2025, A03:2025, and A08:2025.

Active gaps map to open issues: CICD-SEC-8 (federation), API2:2023 (publisher authentication), API7:2023 (SSRF in
federation), and A04:2025 (cryptographic requirements).

**Full alignment map:** [`docs/owasp-alignment.md`](owasp-alignment.md)

---

## What This Is Not

- Not a package manager
- Not a central registry
- Not a gating mechanism that forbids unsigned content
- Not a replacement for tool-specific content formats
- Not a metadata sidecar format
- Not a per-file attestation system
- Not a runtime execution or sandboxing spec for AI agent tools
- Not a content-format spec
