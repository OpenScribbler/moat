# MOAT Revised Architecture — Working Outline

**Status:** Working design document — v0.4.0
**Sub-specs:** [`specs/publisher-action.md`](../specs/publisher-action.md), [`specs/moat-verify.md`](../specs/moat-verify.md)
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

**End User** - The human who chooses which registries to trust and who approves installs or use of content through a
conforming client. MOAT requires clients to surface trust tier and revocation state clearly so the End
User can make an informed decision.

**Publisher** - Creates content and keeps it in a source repository. A publisher may adopt the Publisher Action to
produce source-side attestations, but MOAT does not require the publisher to run a registry or implement client
behavior.

**Registry Operator** - Runs a registry that crawls or ingests content from source repositories, computes content
hashes, signs registry metadata, and publishes a manifest for clients to consume. The Registry Operator is the party
making the registry-level attestation.

**Conforming Client** - The install and management tool that implements MOAT's normative client behavior. A conforming
client fetches manifests, verifies signatures and content hashes, maintains a lockfile, checks revocations, and surfaces
trust signals before install or use. A conforming client is not an AI agent runtime.

**AI Agent Runtime** - A system such as Claude Code, Gemini, Cursor, or Windsurf that loads or executes content after
installation. AI agent runtimes are outside the MOAT protocol boundary. MOAT does not define runtime behavior,
sandboxing, permission enforcement, or execution semantics.

**moat-verify** - A standalone verification tool that audits the MOAT trust chain for a content item. It verifies, but
does not install, manage, or execute content. It is therefore not a conforming client and not a runtime.

### Use Cases

**End User** - Chooses which registries to trust and decides whether to install, load, or remove content based on the
trust tier and revocation state surfaced by a conforming client. This includes individual users and team
or enterprise administrators enforcing local policy.

**Publisher** - Wants accurate source attribution, visible lineage for forks, and an optional low-friction way to
co-attest content from the source repository.

**Registry Operator** - Publishes a curated catalog with verifiable registry attestations that any conforming client can
consume.

**Conforming Client** - Implements install-time and sync-time protocol behavior: fetch manifest, verify signatures and
hashes, maintain a lockfile, surface trust signals, and enforce revocation behavior consistently for the End User.

**AI Agent Runtime** - Loads or executes already-installed content after a conforming client has completed verification
and placement. It appears here to make the boundary explicit: MOAT intentionally defines no runtime behavior for it.

**moat-verify** - Lets any reader independently audit the trust chain for a specific content item without installing or
executing it. Its use case is diagnosis, validation, and interoperability testing rather than installation or runtime
management.

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
    "moat_lockfile_version": 1,
    "entries": [
      {
        "name": "string",
        "type": "skill|subagent|rules|command",
        "registry": "https://...",
        "content_hash": "sha256:<hex>",
        "attested_at": "RFC 3339 UTC",
        "pinned_at": "RFC 3339 UTC",
        "attestation_bundle": {}
      }
    ],
    "revoked_hashes": []
  }
  ```

  Field notes:
  - `content_hash` is the normative identity for the installed item.
  - `attested_at` is the registry's recorded attestation time, taken from the manifest item at install. It is the
    registry's clock, not the client's — do not build freshness logic on it.
  - `pinned_at` is the local install timestamp (client clock). It cannot be verified by a third party.
  - `attestation_bundle` is the complete attestation artifact captured during installation — the signature, signing
    certificate, and transparency log entry as a single embedded JSON object. For Sigstore-signed content this is the
    cosign bundle. Conforming clients MUST populate this field at install time; the data is available as a byproduct
    of the verification step that must already occur. This field enables complete offline re-verification of the
    original attestation without re-querying external services.
  - `type` is a v1 closed set of registered values (`skill`, `subagent`, `rules`, `command`). Conforming clients MUST
    accept entries with unrecognized type values without error — new types are added in future spec versions.
  - `registry` is a URL. Registries MUST treat their URL as permanently stable once published; a URL change
    invalidates all lockfile entries that reference it.
  - `revoked_hashes` is a REQUIRED top-level array of content hash strings for which a registry hard-block is in
    effect. Conforming clients MUST add a content hash to this array when a registry revocation is received and MUST
    refuse to install any hash present in this array. This field MUST be present even when empty. Entries MUST NOT be
    silently removed — clearing a revoked hash requires deliberate End User action. This prevents the
    remove-and-reinstall bypass: a user who removes revoked content and attempts to reinstall the same hash is blocked
    by this record.

  Conforming clients MAY add additional fields to entries but MUST include all seven entry fields. The top-level
  `revoked_hashes` array is also required (empty array if no revocations are in effect). Lockfile interoperability
  requires all conforming clients to use this schema — a lockfile from one conforming client must be readable by
  another.
- Surface trust tier before install confirmation
- Surface revocation source attribution and treat publisher revocations as warnings, registry revocations as the gating
  signal
- MUST NOT use a cached registry manifest for revocation checks when the cached copy exceeds a configurable
  staleness threshold (default: 24 hours). When the threshold is exceeded, the client MUST sync the manifest
  before performing revocation checks. Clients SHOULD NOT allow this threshold to be configured above 48 hours —
  doing so widens the replay window beyond what the protocol's freshness guarantees are designed around.
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

`moat-attestation.json` is a reserved filename. The file at the root of the content directory is excluded
from content hashing to avoid a circular dependency — the attestation file records content hashes, so
including it would cause the hash to change every time attestation is updated. A file named
`moat-attestation.json` at any subdirectory path is NOT excluded; it is included in the content hash
normally. Publishers MUST NOT place files named `moat-attestation.json` in subdirectories of a content
item — such files have no protocol meaning and their presence is a conformance error.

---

## Trust Model

### Trust Tiers

| Tier              | Meaning                                                                                    |
|-------------------|--------------------------------------------------------------------------------------------|
| **Dual-Attested** | Registry-signed and independently attested by the source repo CI for the same content hash |
| **Signed**        | Registry-signed with a Rekor transparency log entry. Tamper-evident. Registry-attested.    |
| **Unsigned**      | No MOAT attestation. Works, but labeled clearly.                                           |

`Dual-Attested` will be rare at launch. Its absence is not a negative signal; `Signed` is the standard tier.

### Registry Trust

- Adding a registry is an explicit End User decision
- Registry signing identity is declared and verifiable
- Signing identity changes require client re-approval
- Registries are responsible for curation in their own domain

### Content Hashing

The content hash identifies a content directory by canonical byte sequence using the normative `moat_hash.py` reference
implementation. Resolved normalization rules, exclusion rules, and conformance expectations are defined by the
reference implementation and its test vectors.

### Trust Anchor Model

**The per-item Rekor transparency log entry is the authoritative trust anchor for each content item.** The registry
manifest signature establishes integrity of the manifest index (the list of Rekor references). Both are required —
they serve different roles:

- **Manifest signature:** proves the registry published this index without tampering. Verified once per manifest fetch.
- **Per-item Rekor entry:** proves this specific `content_hash` was attested at a logged point in time. Verified for
  each item being installed or verified.

A conforming verifier such as `moat-verify` MUST verify the manifest signature AND MUST verify the per-item Rekor entry
for each item under verification. Rekor unavailability is a hard failure — there is no fallback to
manifest-signature-only when Rekor is offline. This is a deliberate design choice: silent degradation to an
unverified-transparency state creates a downgrade path attackers can exploit.

The Rekor instance URL is configurable. Organizations running a private Rekor-compatible instance satisfy the Rekor
connectivity requirement — there is no hard dependency on `rekor.sigstore.dev`.

**Offline verification of already-installed content** uses the lockfile rather than re-running the full verification
flow. In this mode, the lockfile is the trust anchor. Offline lockfile verification re-hashes the local content
directory and compares against `content_hash` in the lockfile entry, then verifies the original attestation using
the stored `attestation_bundle` — all without any network call. This provides the same attestation assurance as
online verification for the state of content at install time.

What offline mode cannot verify is current registry state: revocations issued since install, superseding versions,
and trust tier changes require a live manifest sync to reflect. Conforming clients SHOULD surface this distinction
when operating in lockfile mode.

This resolves Issue 15.

### Freshness Guarantee and Replay Scope

The 24-hour staleness threshold is MOAT's freshness guarantee. MOAT does not defend against manifest replay
attacks within that window. For a replay attack to succeed, an attacker must be able to intercept or
cache-poison a client's manifest fetch, a revocation must have been issued after the cached manifest was
generated, and the client must not have refreshed within the staleness threshold. These conditions narrow the
exploitable window significantly in practice.

Explicit manifest expiry with an `expires_at` field — where clients hard-reject manifests past their declared
expiry — is deferred to a future version. The prerequisite is registry infrastructure maturity: `expires_at`
creates a hard liveness dependency on the registry's CI pipeline, and a CI outage means the registry's entire
catalog goes dark for all clients. That trade-off is appropriate for registry operators with dedicated
infrastructure and monitoring; it is not appropriate to mandate for the hobbyist and small-team operators
that MOAT v1 targets.

### Signature Envelope

The core spec defines a platform-agnostic signing envelope. The normative signing profile for v1 is `sigstore`
— keyless OIDC signing via Fulcio/Rekor.

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

Runtime dependencies — external packages fetched at execution time, remote resources loaded by scripts, or any
resource resolved outside the attested content directory — are outside MOAT's signing guarantee. Content that
appears clean at install time may load untrusted resources at runtime. Conforming clients SHOULD surface this
boundary explicitly to End Users at install time. Companion specs MAY require publishers to declare known external
dependencies so clients can present them before the End User confirms an install.

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
  `name`, `display_name`, `content_hash`, `source_uri`, `attested_at`, `derived_from`, `scan_status`, and
  `signing_profile` (REQUIRED for Dual-Attested items; omitted for Signed and Unsigned).
- **Content hashing algorithm** — deterministic, one-pass, Go dirhash-inspired. Defined by normative reference
  implementation (`moat_hash.py`), not pseudocode.
- **Hash format** — `<algorithm>:<hex>` with no length constraints.
- **Algorithm requirements** — `sha256` is the REQUIRED algorithm; conforming implementations MUST support it.
  `sha512` is OPTIONAL. The following algorithms are FORBIDDEN and MUST NOT appear in content hashes: `sha1`,
  `md5`, and any algorithm with known practical collision attacks. Conforming clients MUST reject content hashes
  using a forbidden algorithm — this is a hard failure, not a warning. Conforming clients that encounter an
  unrecognized algorithm MUST refuse to verify rather than silently pass.
- **Signature envelope format** — platform-agnostic signing model.
- **Trust tier model** — Dual-Attested / Signed / Unsigned. Absence of Dual-Attested is NOT a negative signal.
- **Publisher signing identity model** — For Dual-Attested items, the registry manifest entry MUST include a
  `signing_profile` field declaring the publisher's expected CI signing identity:

  ```json
  { "issuer": "https://token.actions.githubusercontent.com", "subject": "repo:owner/repo:ref:refs/heads/main" }
  ```

  Signing identity is expressed as an OIDC issuer URL and subject claim — the values captured in the
  Rekor/Fulcio certificate at signing time. This model is provider-agnostic; any CI platform with OIDC support
  produces these fields. Registries populate `signing_profile` from the publisher's `moat-attestation.json`
  when indexing a Dual-Attested item. Conforming clients MUST verify that the Rekor certificate's OIDC issuer
  and subject match the declared `signing_profile`. This check is load-bearing for the Dual-Attested tier —
  without it there is no interoperability guarantee that clients are verifying the correct publisher identity.

  **Risk note:** OIDC subjects derived from repository names are vulnerable to rename attacks. If a publisher
  renames their repository, the subject claim changes, and an attacker who claims the old name could produce
  matching attestations. Stable numeric ID claims (`repository_id` on GitHub Actions, `project_id` on GitLab)
  avoid this problem, but verification against numeric IDs requires tooling support beyond standard `cosign`
  flags. This is a known limitation of the v1 Dual-Attested verification model.

  *Informative — known CI provider signing profiles:*

  | Provider | Issuer | Subject format |
  |----------|--------|----------------|
  | GitHub Actions | `https://token.actions.githubusercontent.com` | `repo:{owner}/{repo}:ref:refs/heads/{branch}` |
  | GitLab CI | `https://gitlab.com` | `project_path:{namespace}/{project}:ref_type:branch:ref:{branch}` |

  Other providers with OIDC support: the issuer is the provider's OIDC endpoint URL; the subject format is
  provider-defined. Consult the provider's OIDC documentation. Providers are added to this table when their
  subject format is verified against a working Sigstore implementation. Forgejo/Codeberg Actions OIDC support
  is not yet shipped as of this writing (April 2026). Tracking: Gitea PR
  [#36988](https://github.com/go-gitea/gitea/pull/36988) (draft, opened 2026-03-25) and Forgejo PR
  [#5344](https://codeberg.org/forgejo/forgejo/pulls/5344) (closed 2025-02-02, no active successor). When
  either ships, the issuer will be `<instance-url>/api/actions/oidc` and the subject format will mirror
  GitHub's. Check these PRs before updating this table.

- **Client verification protocol** — what a conforming client must check on install.
- **Revocation mechanism** — `revocations` array in manifest (REQUIRED; empty if none). Each entry MUST include:
  `content_hash`, `reason`, and `details_url` (REQUIRED for registry revocations; OPTIONAL for publisher
  revocations). Reason values (informational only — they do NOT determine client behavior): `malicious`,
  `compromised`, `deprecated`, `policy_violation`. Unknown future reason values MUST be accepted without error.

  **Client behavior is determined by revocation source, not reason code.** Normative behavior when syncing a
  manifest update that adds a revocation entry for already-installed content:

  | Revocation source | Required client behavior                                                                                                                                                                                                                                                                                                                       |
  |-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
  | Registry          | MUST hard-block all use of that content. Client refuses to load or execute the item. MUST present the reason, the `details_url` if present, and the registry that issued the revocation to the End User. Block is in effect until the End User explicitly removes the content or installs a non-revoked version. The revoked content hash MUST be added to `revoked_hashes` in the lockfile — see lockfile specification above. |
  | Publisher         | MUST present the reason, the `details_url` if present, and the registry that surfaced the revocation to the End User. MUST warn once per client session, recurring after any client restart. MAY allow use with explicit End User confirmation. MUST NOT silently continue.                                                                     |

  All conforming clients MUST, regardless of environment: exit with a non-zero exit code when revoked content is
  encountered, and write to stderr the content item name as recorded in the lockfile, the revocation reason, and the
  registry that issued the revocation. Interactive clients MAY additionally prompt for End User confirmation on
  publisher revocations. Non-interactive clients that cannot prompt MUST exit non-zero and MUST NOT proceed.

  Registry revocations are authoritative hard blocks because the registry is the trust unit in MOAT — clients verify
  what registries attest, and revocation is part of that attestation. This creates a named trade-off: a compromised
  registry operator can issue hard blocks against legitimate content. The End User's explicit opt-in to each registry
  (required for conforming clients) is the primary prevention; attribution — clients MUST surface which registry
  issued each revocation — is the primary detection mechanism after opt-in. A user who trusts only one registry has
  no cross-registry signal to compare against if that registry is compromised; this limitation cannot be addressed at
  the protocol level.
- **Lineage model** — `derived_from` for forks and adaptations.
- **Version semantics** — `version` is an optional display label; content hash is normative identity; `attested_at` for
  freshness.
- **`scan_status` structure** — per-item manifest field. Schema:

  ```json
  {
    "result": "clean|findings|not_scanned",
    "scanner": [{ "name": "string", "version": "string" }],
    "scanned_at": "ISO8601",
    "findings_url": "https://..."
  }
  ```

  Field rules:
  - `result` is REQUIRED. `not_scanned` is valid.
  - `scanner` and `scanned_at` are REQUIRED when `result` is `clean` or `findings`; omitted when `not_scanned`.
  - `findings_url` is OPTIONAL; only present when `result` is `findings` and a public report exists.
  - `scanner[].name` is a controlled value — registries MUST use the canonical name for well-known scanners
    (e.g. `"snyk-mcp-scan"`, `"semgrep"`) to enable cross-registry aggregation. Additional fields within
    scanner entries are permitted. Free-form scanner name strings defeat aggregation and do not conform.
### Reference implementations (normative behavior, separate artifacts)

- **`moat_hash.py`** — Python reference implementation. A conforming implementation produces identical output for all
  test vectors. Two independent implementations in different languages must pass all test vectors before the spec
  advances beyond Draft.
- **`moat-verify`** — Standalone verification script. Spec: [`specs/moat-verify.md`](../specs/moat-verify.md)
- **Publisher Action** — GitHub Actions workflow for source repos. Spec:
  [`specs/publisher-action.md`](../specs/publisher-action.md)

### Informative profiles

- **Sigstore profile** — keyless OIDC signing via Fulcio/Rekor.

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


~~**Issue 4: Registry manifest size and pagination**~~ **Resolved.** No pagination in v1. Registries serving large
catalogs should split into sub-registries. Pagination support is a MAY for future spec versions and client
implementations. This is consistent with the static-file registry model and avoids protocol complexity in v1.

**Issue 9: Registry index governance** If one index ships as the default discovery source, it becomes a legitimacy root
whether named as such or not. Inclusion criteria, removal policy, incident response, namespace disputes, appeals, and
signing all need explicit governance.

**Issue 10: Publisher authentication model** How publishers authenticate to registries and how clients authenticate to
private registries is still open. OIDC should be the primary path; long-lived tokens, if allowed, must be clearly
treated as the weaker compatibility path.

**Issue 11: Federation security** Federation introduces SSRF risk, trust laundering risk, and upstream-input
sanitization risk. Response size limits and timeouts should be conformance requirements when federation exists.

~~**Issue 12: Algorithm deprecation guidance**~~ **Resolved.** See Algorithm requirements in the normative core.
`sha256` required; `sha512` optional; `sha1` and `md5` forbidden (hard failure). Clients refuse to verify
unrecognized algorithms rather than silently passing.

~~**Issue 13: Offline verification**~~ **Resolved.** See Trust Anchor Model (offline lockfile verification) and the
conforming client manifest staleness requirement (24-hour default). Lockfile is the offline trust anchor;
`attestation_bundle` provides complete proof retention without network calls.

**Issue 14: Cross-registry blocklist federation** Client-side cross-registry revocation matching exists conceptually,
but a registry-side sharing format for urgent revocation signals is still undefined.

~~**Issue 15: Trust anchor ambiguity**~~ **Resolved.** Per-item Rekor entry is the authoritative trust anchor. Manifest
signature establishes index integrity. Both required. See Trust Anchor Model in the Trust Model section.

~~**Issue 16: Anti-rollback / anti-freeze model**~~ **Resolved.** See Freshness Guarantee and Replay Scope in the
Trust Model. The 24-hour staleness threshold is the v1 freshness guarantee. Manifest replay within that window
is an explicitly out-of-scope threat. Clients SHOULD NOT configure the threshold above 48 hours. Explicit
`expires_at` expiry is deferred to a future version pending registry infrastructure maturity.

~~**Issue 17: "No central infrastructure" language**~~ **Resolved.** Core Design Principles already reads: "No central
infrastructure required to operate a registry. A GitHub repo with a GitHub Action is enough to run one.
Verification of Signed content depends on Rekor availability." The distinction is explicit.

**Issue 18: Publisher Action source repo mutation** Writing `moat-attestation.json` back to source repos creates commit
churn and policy friction. The alternative of bundles or release artifacts needs evaluation before the Publisher Action
spec is finalized.

~~**Issue 19: GitHub identity verification claims**~~ **Resolved.** Signing identity is expressed as OIDC issuer
+ subject — provider-agnostic. `signing_profile` added as REQUIRED on Dual-Attested manifest items; conforming
clients MUST verify Rekor certificate issuer and subject match it. Mutable-name rename risk documented as a
known v1 limitation. Informative table covers GitHub Actions and GitLab CI; Forgejo/Codeberg excluded until
their OIDC Actions support ships.

~~**Issue 20: Binary revocation states (REVOKED / YANKED)**~~ **Resolved.** Client behavior is determined by
revocation source (registry = hard block, publisher = warn), not by reason code. The four reason codes
(`malicious`, `compromised`, `deprecated`, `policy_violation`) are informational — they carry urgency signal for
security operators and End Users but do not change client enforcement behavior. `details_url` added as REQUIRED
for registry revocations. Collapsing to REVOKED/YANKED would discard useful urgency signal without simplifying
client implementation.

**Issue 21: Threat feeds vs cross-registry revocation** Third-party feedback argues that any trusted registry being able
to warn about content from another registry creates trust bleeding and DoS potential. The proposed alternative is a
standardized optional `threat-feed.json` maintained by a trusted community or security operator. That may be cleaner,
but it reintroduces central infrastructure and governance. Decision needed: keep cross-registry revocation, replace it
with threat feeds, or support both with different trust semantics.

~~**Issue 22: Archive hashing vs directory hashing**~~ **Resolved (rationale preserved).** Directory hashing is
intentional — MOAT's model is registry-side crawling of source content, not publisher-side packaging. If MOAT adds
creator-side packaging tooling in a future version, archive hashing should be reconsidered at that point.
Deferred to v2.

~~**Issue 23: SSH profile retention vs CI-only mandate**~~ **Resolved.** SSH signing removed from the spec
entirely. Sigstore keyless OIDC is the only signing profile in v1. SSH key distribution is an unsolved
problem — no reliable mechanism exists to distribute and trust SSH public keys at ecosystem scale — and
air-gapped or private registry operators can satisfy the signing requirement with a private Rekor instance.

~~**Issue 24: Runtime dependency scope**~~ **Resolved.** Scope Boundary section now includes an explicit runtime
dependency disclaimer. Conforming clients SHOULD surface the boundary at install time; companion specs MAY require
external dependency declaration. Full dependency graphs deferred to a future version.

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
