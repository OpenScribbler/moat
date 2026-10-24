# Model for Origin Attestation and Trust (MOAT) Specification

**Version:** 0.8.0 (Draft)
**Status:** Draft
**Date:** 2026-09-30
**Editor:** Holden Hewett
**License:** Apache-2.0 (https://www.apache.org/licenses/LICENSE-2.0)
**Repository:** https://github.com/OpenScribbler/moat
**Sub-specs:** [`specs/github/publisher-action.md`](specs/github/publisher-action.md), [`specs/github/registry-action.md`](specs/github/registry-action.md), [`specs/moat-verify.md`](specs/moat-verify.md), [`specs/npm-distribution.md`](specs/npm-distribution.md)
**OWASP alignment:** [`docs/owasp-alignment.md`](docs/owasp-alignment.md)

### Document Status

This is a Draft specification. It represents a complete architectural revision from v0.3.0, which defined a per-item
sidecar metadata format (`meta.yaml`). This version redefines MOAT as a registry distribution protocol for AI agent
content. The v0.3.0 specification is archived as [`archive/moat-spec-v0.3.0.md`](archive/moat-spec-v0.3.0.md).

This draft has not been validated by any implementations. Before advancing beyond Draft status, the registry manifest
format and content hashing algorithm MUST be confirmed by at least two independent implementations in different
languages.

> **Adoption status:** Zero adopters. No implementations exist beyond draft tooling concepts. This is a greenfield spec.
> Design for correctness, not continuity.

Copyright 2026 Holden Hewett. Licensed under the Apache License, Version 2.0. You may obtain a copy of the license at
https://www.apache.org/licenses/LICENSE-2.0.

---

## What MOAT Is

**Model for Origin Attestation and Trust** is a protocol for secure distribution of AI agent content through registries.

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

---

## MOAT is not

MOAT is scoped to registry-distributed content — attestation, install-time verification, lockfiles, and revocation
signaling.

MOAT is explicitly NOT:

- A package manager
- A central registry
- A gating mechanism that forbids unsigned content
- A replacement for tool-specific content formats
- A metadata sidecar format
- A per-file attestation system
- A runtime execution or sandboxing spec for AI agent tools
- A content-format spec

### Out of scope

MOAT's trust guarantee covers the content directory as a unit. Dependencies outside that directory are outside the
guarantee and need to be surfaced by companion specs and conforming clients.

The following are outside MOAT's signing guarantee and therefore out of scope for the core spec:

- Informally shared standalone files
- Per-file metadata inside content items
- Content format definitions such as SKILL.md schemas
- AI agent runtimes and execution environments
- Runtime sandboxing or permission enforcement
- Cross-item dependency graphs

Runtime dependencies, such as external packages fetched at execution time, remote resources loaded by scripts, or any
resource resolved outside the attested content directory, are outside MOAT's signing guarantee. Content that appears
clean at install time may load untrusted resources at runtime. Conforming clients SHOULD surface this boundary
explicitly to End Users at install time. Companion specs MAY require publishers to declare known external dependencies
so clients can present them before the End User confirms an install.

---

## Actors

MOAT involves five distinct actors. They are not interchangeable.

**End User** — The human who chooses which registries to trust and approves installs or use of content through a
conforming client. This includes individual users and team or enterprise administrators enforcing local policy. MOAT
requires clients to surface trust tier and revocation state clearly so the End User can make an informed decision.

**Publisher** — Creates content and keeps it in a source repository. Wants accurate source attribution, visible lineage
for forks, and an optional low-friction way to co-attest content from the source repository. A publisher may adopt the
[Publisher Action](specs/github/publisher-action.md) to produce source-side attestations, but MOAT does not require the
publisher to run a registry or implement client behavior.

**Registry Operator** — Runs a registry that crawls or ingests content from source repositories, computes content
hashes, signs registry metadata, and publishes a manifest for clients to consume. The Registry Operator is the party
making the registry-level attestation and is responsible for curation in their own domain.

**Conforming Client** — The install and management tool that implements MOAT's normative client behavior. Fetches
manifests, verifies signatures and content hashes, maintains a lockfile, checks revocations, and surfaces trust signals
before install or use — consistently for the End User. A conforming client is not an AI agent runtime.

**AI Agent Runtime** — A system such as Claude Code, Gemini, Cursor, or Windsurf that loads or executes
already-installed content after a conforming client has completed verification and placement. AI agent runtimes are
outside the MOAT protocol boundary. MOAT intentionally defines no runtime behavior, sandboxing, permission
enforcement, or execution semantics for it; it appears here to make that boundary explicit.

> **Informative note — role combinations:** The actors above are roles, not individuals or organizations. A
> single person or team may occupy multiple roles simultaneously:
>
> - **Publisher only** — Creates content; relies on a third-party registry to distribute and attest it.
> - **Registry Operator only** — Indexes and attests content from external publishers; does not create content.
> - **Publisher + Registry Operator (self-publishing)** — Creates and distributes their own content from a
>   single repository. The Publisher Action and Registry Action run from the same repo, producing two distinct
>   Rekor entries under two distinct signer subjects (one per workflow file path). This is valid Dual-Attested —
>   the independence comes from the signer subject binding, not from organizational separation. The manifest's
>   `self_published` field discloses this configuration to End Users. A Self-Publisher MAY instead produce the
>   publisher attestation with an Author Key held outside CI; see [Author-Key Profile](#author-key-profile).
> - **Publisher + Registry Operator + Conforming Client** — A team that creates content, operates a registry,
>   and ships a client that installs from it. Common in closed-ecosystem tools. MOAT's trust model still applies:
>   the End User retains the ability to verify all attestations independently.

## Conforming specs

MOAT is a protocol specification, not an implementation. It defines normative behavior for conforming clients and
registries, but it does not define any specific implementation. The following companion specs are normative parts of the
MOAT ecosystem:

**[moat-verify](specs/moat-verify.md)** — A standalone verification tool that lets any reader independently audit the
MOAT trust chain for a content item without installing or executing it. Its use case is diagnosis, validation, and
interoperability testing. It is therefore not a conforming client and not a runtime.

**[Publisher Action](specs/github/publisher-action.md)** — A GitHub Actions workflow that publishers can adopt to generate
source-side attestations. This is normative for the Dual-Attested trust tier, but it is not required to run a registry
or be a conforming client. Registries that want to support Dual-Attested content MUST be able to consume attestations
produced by the Publisher Action.

**[Registry Action](specs/github/registry-action.md)** — A GitHub Actions workflow that registry operators adopt to crawl
publisher sources, compute content hashes, determine trust tiers, sign the manifest, and publish it. This is the
normative mechanism for producing a MOAT registry manifest. A publisher who also runs the Registry Action from the same
repository is a self-publishing operator.

### Reference implementations

**[`reference/generate_test_vectors.py`](reference/generate_test_vectors.py)** — **Normative.** The test vectors produced by this script are the authoritative specification of correct hashing output. When a conforming implementation and a test vector disagree, the implementation is non-conforming. When `moat_hash.py` and a test vector disagree, `moat_hash.py` has a bug — the test vector is correct.

**[`reference/moat_hash.py`](reference/moat_hash.py)** — **Informative.** Python reference implementation of the MOAT content hashing algorithm. Useful as a starting point for implementations in other languages, and as a cross-check during development. It is not the normative specification — the test vectors are. Two independent implementations in different languages must pass all test vectors before the spec advances beyond Draft.

**[`reference/moat_author_key.py`](reference/moat_author_key.py)** — **Informative.** Python reference implementation of the
Author-Key Profile's verification rules: fingerprints, allowed-signers parsing, list digests, item and list-change
messages, and SSHSIG verification for the accepted key types. Not constant-time; it verifies and must not be used to
sign with real keys.

**[`reference/moat_verify.py`](reference/moat_verify.py)** — Python reference implementation of `moat-verify` —
standalone verification tool supporting online (`--registry`) and offline (`--lockfile`) modes.

**[`reference/moat-publisher.yml`](reference/moat-publisher.yml)** — Publisher Action workflow template. Drop into `.github/workflows/`
to produce source-side attestations and qualify for the Dual-Attested tier.

**[`reference/moat-registry.yml`](reference/moat-registry.yml)** — Registry Action workflow template. Drop into
`.github/workflows/` to run a MOAT registry.

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
[`specs/github/publisher-action.md`](specs/github/publisher-action.md)

### 3. Conforming Clients

A conforming client is the install and management layer that implements MOAT's normative client behavior. It may be a
package manager, CLI installer, IDE-side content manager, or similar tool. It is not an AI agent runtime such as
Claude Code, Gemini, Cursor, or Windsurf.

The spec defines what a conforming client must do on install and sync:

- Require explicit End User action to add a trusted registry
- Verify the registry manifest using the declared signing profile
- Verify content hashes against the manifest on install
- Maintain a local lockfile of installed content hashes. See [Lockfile](#lockfile) for the minimum conforming
  schema, field definitions, and interoperability requirements.
- Surface trust tier before install confirmation
- Surface revocation source attribution and treat publisher revocations as warnings, registry revocations as the gating
  signal
- MUST NOT use a cached registry manifest for revocation checks when the cached copy is stale. A manifest is
  stale when the current time exceeds `expires` (if present) or exceeds `fetched_at + 72 hours` (if `expires`
  is absent). When stale, the client MUST sync the manifest before performing revocation checks. A failed
  refresh MUST NOT reset the staleness clock.
- On manifest sync: check all installed content hashes against the updated `revocations` array; apply hard-block for
  registry revocations and warn-on-use for publisher revocations (see Revocation mechanism above)
- **Private content isolation:** Conforming clients MUST NOT automatically index or submit content from private or
  internal source repositories to public registries. When a client operation would route such content to a public
  registry, it MUST require explicit End User confirmation and MUST surface the source repository's visibility before
  proceeding. This is a design requirement for client implementors — there is no external audit mechanism, but
  violating it constitutes a failure to meet the spec's intent.

The conforming client is the component responsible for trust decisions at install or load time; the runtime consumes
content only after that step.

---

## Content Types

MOAT currently defines four normative content types, with two more deferred:

| Type       | Category dir | Notes                                                         |
|------------|--------------|---------------------------------------------------------------|
| `command`  | `commands/`  | User-invoked slash commands                                   |
| `hook`     | `hooks/`     | Deferred — directory reserved, type not yet normative         |
| `mcp`      | `mcp/`       | Deferred — directory reserved, type not yet normative         |
| `rules`    | `rules/`     | Behavior configuration files and rule bundles                 |
| `skill`    | `skills/`    | Reusable instruction sets                                     |
| `agent`    | `agents/`    | Specialized persona definitions with controlled tools/context |

Each subdirectory within a category directory is one content item. The content hash covers that subdirectory as a unit.

### Repository Layout

Canonical layout:

```text
commands/
hooks/
mcp/
rules/
skills/
agents/
```

The [Publisher Action](specs/github/publisher-action.md) uses a two-tier discovery model:

- **Tier 1:** Canonical category directories
- **Tier 2:** `.moat/publisher.yml` for custom layouts; it supplements Tier 1, so the action discovers items from both. List only items outside the canonical directories in it, since an item listed in both tiers is discovered twice.

`moat-attestation.json` is a reserved filename. The [Publisher Action](specs/github/publisher-action.md) writes this file to a
dedicated `moat-attestation` branch — it is never present in the source branch and is therefore never included in
content hashing. Publishers MUST NOT create files named `moat-attestation.json` anywhere in their source branch; such
files have no protocol meaning and their presence is a conformance error.

Registries discover publisher attestations at the canonical URL:

```
https://raw.githubusercontent.com/{owner}/{repo}/moat-attestation/moat-attestation.json
```

---

## Trust Model

### Trust Tiers

| Tier              | Meaning                                                                                    |
|-------------------|--------------------------------------------------------------------------------------------|
| **Dual-Attested** | Registry-signed and independently attested by the Publisher for the same content hash      |
| **Signed**        | Registry-signed with a Rekor transparency log entry. Tamper-evident. Registry-attested.    |
| **Unsigned**      | No MOAT attestation. Works, but labeled clearly.                                           |

`Dual-Attested` will be rare at launch. Its absence is not a negative signal; `Signed` is the standard tier.

The publisher attestation of a Dual-Attested item comes from one of two mechanisms: keyless signing in the source
repository's CI (the Publisher Action), or an Author Key under the [Author-Key Profile](#author-key-profile). Both
yield the same tier; the Author-Key Profile is not a separate tier, and the registry's own attestation is keyless in
both cases.

### Registry Trust

- Adding a registry is an explicit End User decision
- Registry signing identity is declared in `registry_signing_profile` and verifiable via the manifest bundle
- Conforming clients MUST track `registry_signing_profile` per trusted registry; changes on a subsequent fetch
  require End User re-approval before the updated manifest is accepted
- `operator` and `name` are display labels — changes to these fields MUST NOT be treated as signing identity
  changes and MUST NOT trigger re-approval
- Registries are responsible for curation in their own domain
- **First-install trust boundary:** For registries discovered through a Registry Index, the index entry's
  `registry_signing_profile` establishes the expected signing identity before first manifest fetch. For
  manually-added registries, the signing identity is accepted from the manifest on first fetch — the End User's
  explicit add action is the bootstrap. This is a known TOFU boundary inherent to any PKI-like system.

### Content Hashing

The content hash identifies a content directory by canonical byte sequence using the normative
[`reference/moat_hash.py`](reference/moat_hash.py) reference implementation. Resolved normalization rules, exclusion
rules, and conformance expectations are defined by the reference implementation and its test vectors. This is the
directory algorithm, and it applies to every content item except an ACIF content item.

#### ACIF Content Items

An ACIF content item is a content item in the Agent Content Interchange Format ([ACIF](https://github.com/OpenScribbler/agent-content-interchange-format/blob/main/specs/core/spec.md)) whose
manifest entry carries the `acif` member. Its Content Hash is not computed by the directory algorithm. It is
`sha256:` followed by the item's ACIF attestation input digest: the value ACIF publishes as
`registry_section.attestation_hash`, whose construction ACIF defines in
[ACIF Registry Specification §6](https://github.com/OpenScribbler/agent-content-interchange-format/blob/main/specs/registry-spec/spec.md). That digest binds the item's ACIF `body_hash` and `metadata_hash`,
so one signature covers the item's body and the frontmatter declarations (such as an agent's tool, model, and MCP
server grants) that `body_hash` excludes. MOAT does not restate the construction; `reference/moat_hash.py`
(`acif_content_hash`) implements it and the [ACIF test vectors](#attestation-payload) pin it.

**Marker (normative).** A conforming client identifies an ACIF content item only by its manifest entry: the entry
carries `acif`, an object whose `entry_file` member is the item's canonical entry file as a path relative to the
item root (for example `SKILL.md`). A source repository declares its ACIF content items in the `acif` list of
`.moat/publisher.yml`, which the Publisher Action and Registry Action specifications define, and the registry sets
`acif` from that declaration. An entry without `acif` is not an ACIF content item, whatever its files contain, and
its Content Hash is computed by the directory algorithm. A conforming client MUST compute the Content Hash by
the method the marker selects. A wrong marker fails closed: the attestation input preimage begins with the line
`acif-attestation-input-v1`, which no directory-algorithm manifest line can equal, so the two methods agree on the
same bytes only through a SHA-256 collision.

**Computation (normative).** A conforming client MUST compute an ACIF content item's Content Hash over the bytes it
installs:

1. Compute `body_hash` over the installed item directory as [ACIF Core §7](https://github.com/OpenScribbler/agent-content-interchange-format/blob/main/specs/core/spec.md) defines, with `acif.entry_file`
   as the entry file. MOAT applies none of ACIF's canonicalization rewrites; the installed bytes are hashed as they
   are. These are the item bytes the client fetched. A client that renders the item into a provider's format before
   writing it hashes the fetched bytes, never the rendered output.
2. Derive the item's `publisher_section` from the installed item as [ACIF Publisher Specification §5](https://github.com/OpenScribbler/agent-content-interchange-format/blob/main/specs/publisher-spec/spec.md)
   defines, and compute `metadata_hash` from it as §6 of that specification defines. An item with no
   `publisher_section` has no `metadata_hash`.
3. Compute the attestation input digest from those two values as ACIF Registry Specification §6 defines.
4. Map the digest's `{algorithm, value}` to the Content Hash string `<algorithm>:<value>`. The algorithm MUST be
   `sha256` and the value MUST be 64 lowercase hexadecimal characters; any other value is a hard failure.

A conforming client MUST NOT take `body_hash`, `metadata_hash`, or `attestation_hash` from an ACIF record, a
sidecar, or a manifest field in place of recomputing them. A Content Hash matched against a record field alone
does not verify the item.

*Informative — relationship to the directory algorithm:* An ACIF content item's Content Hash never equals the
directory algorithm's output for the same bytes, because it is the digest of a different preimage. The underlying
`body_hash` also differs for a single-file item, because a single-file `body_hash` is the digest of the entry file's
frontmatter-stripped, LF-normalized text rather than of a manifest (TV-ACIF-01, TV-ACIF-02). For a multi-file item
the `body_hash` construction is the directory algorithm's manifest construction, so the two agree exactly when the
entry file carries no frontmatter and the item root holds no `acif-sidecar.yaml` (TV-ACIF-03); entry-file
frontmatter is stripped from the multi-file manifest too (TV-ACIF-04).

### Trust Anchor Model

**The per-item Rekor transparency log entry is the authoritative trust anchor for each content item.** The registry
manifest signature establishes integrity of the manifest index (the list of Rekor references). Both are required —
they serve different roles:

- **Manifest signature:** proves the registry published this index without tampering. Verified once per manifest fetch.
- **Per-item Rekor entry:** proves this specific `content_hash` was attested at a logged point in time. Verified for
  each item being installed or verified.

A conforming verifier such as [`moat-verify`](specs/moat-verify.md) MUST verify the manifest signature AND MUST verify
the per-item Rekor entry for each item under verification. Rekor unavailability is a hard failure — there is no fallback
to manifest-signature-only when Rekor is offline. This is a deliberate design choice: silent degradation to an
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

### Trusted-Root Acquisition

A conforming client cannot verify a Sigstore signature without a Sigstore trusted root — the Fulcio CA bundle, Rekor
public keys, and timestamp authorities that anchor the signing ecosystem. This section defines the acquisition modes
a conforming client MUST support and the staleness obligation that applies to each.

**Acquisition modes (normative):** conforming clients MUST support at least the three modes below. A client MAY
implement additional modes (for example, TUF-backed runtime refresh) provided the staleness obligation still applies.

| Mode | Source | Staleness obligation |
|---|---|---|
| **Bundled** | Trusted root embedded in the client binary at build time | Client MUST track calendar age of the bundle and surface it to the operator before verification fails silently against rotated keys. |
| **Per-registry override** | File path declared on the registry configuration entry | Client MUST verify the file parses as a valid Sigstore trusted root before accepting. Freshness is the operator's responsibility. |
| **Invocation override** | File path passed at command invocation | Same as per-registry: parse-on-load, operator-owned freshness. |

Precedence when more than one mode would apply: invocation override > per-registry override > bundled default. A
client MUST emit an auditor-visible signal (stderr line, log record, or structured event) whenever a non-bundled
acquisition mode is in effect, naming the path and the registry. Silent override is the attack surface; loud
override is the defense.

**Staleness policy for bundled roots (normative):** when a client ships a trusted root as a bundled asset, the
client MUST enforce a maximum calendar age beyond which verification refuses to proceed. The threshold value is an
implementation choice; the requirement is that the threshold exist and that age-at-failure be discoverable before
the threshold is crossed. The Sigstore public-good instance rotates Fulcio CA and Rekor keys every 6 to 12 months,
so a bundle older than the longest rotation interval cannot reliably verify newly-issued signing certificates.

**Staleness policy for override roots:** override paths are explicitly out of scope for the bundled-root staleness
policy — operators who supply their own trusted root accept responsibility for refreshing it. Conforming clients
MUST NOT apply the bundled-root cliff to override roots. Clients MAY apply a distinct validity check derived from
the root's own `certificateAuthorities[].validFor.end` if they wish to surface forthcoming CA expirations.

**Rationale:** The three modes cover three deployment realities. Bundled roots give first-run clients a usable
default without a network dependency. Per-registry overrides let enterprises pin a corporate Sigstore deployment
without affecting unrelated registries. Invocation overrides give operators a break-glass path for testing and
air-gapped environments. Collapsing the three into one — bundled only, or runtime-fetch only — forces every
adopter into a deployment posture that breaks at least one of the three realities.

### Freshness Guarantee and Replay Scope

MOAT adopts the TUF (The Update Framework) staleness model: the registry sets expiry, the client enforces it.

**Registry side:** Registries MAY include an `expires` field (RFC 3339 UTC) in the manifest. The Registry Action auto-populates `expires` during manifest generation. Registry operators MAY override the default value to enforce stricter freshness for their consumers.

**Client side:**
- If `expires` is present: conforming clients MUST NOT trust the manifest after the value of `expires`.
- If `expires` is absent: conforming clients apply a spec-defined default of **72 hours** from `fetched_at` (the client's own last successful manifest fetch timestamp, recorded in the lockfile `registries[url].fetched_at` field).
- Staleness is checked at **install time** — not continuously. A cached manifest is valid until the next install or sync operation triggers a staleness check.
- A failed manifest refresh MUST NOT reset the staleness clock. The clock runs from the last *successful* fetch. A client that cannot refresh a stale manifest MUST NOT proceed as if the manifest were fresh.

**`updated_at` vs `fetched_at`:** The manifest's `updated_at` field records when the registry last regenerated its manifest — it is for display and activity monitoring only. The staleness check MUST be computed against the client's own `fetched_at` timestamp, not against `updated_at`. A manifest whose `updated_at` is recent but which the client fetched 73 hours ago is stale; a manifest whose `updated_at` is seven days old but which the client fetched two hours ago is not.

**Why 72 hours:** The 72-hour default survives the weekend test (Friday 6pm to Monday 9am is 63 hours, within the 72-hour window). A 48-hour default would produce hard failures for every developer on Monday morning, driving MOAT disabling. A 7-day default provides an exploitation window of 8 days (7d + 24h registry crawl). 72 hours bounds the worst-case exploitation window to 96 hours (72h + 24h crawl delay) while avoiding the Monday morning failure mode. Security-conscious registries SHOULD set a shorter `expires` (4h, 24h, or 48h) regardless of the default — the default only affects registries that do not configure expiry.

**Air-gapped environments:** The same mechanism as TUF applies. Operators provision manifests with a long `expires` value during the provisioning step. The spec does not define a separate offline or degraded mode — any exemption triggered by network state creates an exploitation path for attackers who control network state.

**Clarifying note for existing manifests:** Manifests published before the `expires` field was added will not carry this field. Conforming clients apply the 72-hour default from `fetched_at`. This is a client-side policy, not a registry assertion — the registry has not declared an explicit expiry, so the client's default applies.

**No separate revocation endpoint (informative):** MOAT does not define a separate revocation-only endpoint or push notification mechanism. The `expires`-based freshness model bounds the revocation propagation window (96h worst case for default-expiry registries; 28h for 4h-expiry registries). Registries that require faster revocation propagation SHOULD set a shorter `expires` value rather than relying on a separate endpoint. This is simpler to implement, avoids new endpoint format and client polling logic, and provides equivalent security for registries that tune their expiry.

**No per-entry expiry (informative):** Per-entry `expires_at` fields are not defined in this version. Per-entry expiry is only meaningful when content items have individual fetch endpoints — without per-item URLs, any expired item triggers a full manifest refresh, making per-entry expiry equivalent to manifest-level expiry. Revisit if per-item fetch endpoints are added in a future version.

MOAT does not defend against manifest replay attacks within the valid window. For a replay attack to succeed, an attacker must be able to intercept or cache-poison a client's manifest fetch, a revocation must have been issued after the cached manifest was generated, and the client must not have refreshed within the staleness window.

### Signature Envelope

Sigstore keyless OIDC signing via Fulcio/Rekor is the normative signing mechanism for registry manifests,
registry per-item attestations, and Publisher Action attestations. A Publisher MAY instead produce its publisher
attestation under the [Author-Key Profile](#author-key-profile), which signs with an Author Key and records the
signature in Rekor. These are the only two normative signing mechanisms in this version.

**Bundle format (normative):** All cosign signatures produced by conforming Publisher Actions, Registry Actions, and any other MOAT-conforming signer MUST be Sigstore protobuf bundle v0.3 (`mediaType: application/vnd.dev.sigstore.bundle.v0.3+json`). Conforming signers invoking `cosign sign-blob` MUST pass `--new-bundle-format`. The legacy JSON bundle layout (top-level `base64Signature` / `cert` / `rekorBundle.Payload.logIndex`) is not supported by this version of MOAT — strict consumers (e.g., sigstore-go) reject it, and conforming clients MAY refuse to parse it. Verifiers locate the Rekor log identity at `verificationMaterial.tlogEntries[].logId.keyId` and the log index at `verificationMaterial.tlogEntries[].logIndex`.

**Signing input:** The registry CI signs the manifest JSON file with `cosign sign-blob`. The input to signing is
the raw bytes of the manifest file as it will be served — after any transport-layer decompression, with no
additional normalization. The manifest MUST be served as UTF-8 without a byte-order mark. Once signed and
published, the manifest file is byte-stable: any modification breaks the signature.

**Bundle placement:** The cosign bundle (signature, signing certificate, and Rekor transparency log entry) MUST be
served at `{manifest_uri}.sigstore`. This path is normative — conforming registries MUST serve the bundle there
and conforming clients MUST fetch it from there. The bundle MUST be served at the same availability level as the
manifest itself. A bundle at an ephemeral URL will produce verification failures when it expires.

**Per-item attestation:** For Signed and Dual-Attested items, the registry MUST create a per-item Rekor entry at
attestation time by signing a canonical payload with `cosign sign-blob`. See [Attestation Payload](#attestation-payload)
for the canonical format, serialization rules, and test vector.

**Manifest verification flow:**

1. Fetch the manifest at `manifest_uri`
2. Fetch the bundle at `{manifest_uri}.sigstore`
3. Verify the bundle covers the exact bytes of the downloaded manifest file
4. Confirm the signing certificate's OIDC issuer and signer subject (SAN) match the manifest's `registry_signing_profile`
5. Confirm the Rekor transparency log entry in the bundle is valid

Rekor unavailability is a hard failure — there is no fallback to bundle-only verification without Rekor
confirmation. See [Trust Anchor Model](#trust-anchor-model).

**Signing identity trust:**

- For registries discovered through a Registry Index: the index entry's `registry_signing_profile` establishes
  the expected signing identity before the manifest is fetched. Conforming clients SHOULD confirm the manifest's
  declared `registry_signing_profile` matches the index entry before accepting.
- For manually-added registries: the signing identity declared in the manifest is accepted on first fetch
  (trust-on-first-use). The End User's explicit action to add the registry is the trust bootstrap. Conforming
  clients MUST store the accepted `registry_signing_profile` and apply re-approval requirements on all
  subsequent fetches.
- On subsequent fetches: if `registry_signing_profile` has changed, conforming clients MUST require End User
  re-approval before accepting the manifest. `operator` and `name` changes do NOT trigger re-approval.

### Author-Key Profile

The Author-Key Profile lets a Publisher produce the publisher attestation of a Dual-Attested item with a key the
Publisher holds — an **Author Key** — instead of keyless signing in CI. It is the second attestation of the existing
Dual-Attested tier, not a new tier: the registry crawls, signs, and serves every item exactly as it does for a
keyless publisher attestation. *(Informative: the profile serves the Self-Publisher, whose source and registry are
one repository. An Author Key held outside CI gives that Publisher an attestation that push access to the repository
alone cannot produce.)*

**Signature scheme (normative).** An Author-Key signature is an OpenSSH SSHSIG signature
([PROTOCOL.sshsig](https://github.com/openssh/openssh-portable/blob/master/PROTOCOL.sshsig)) with namespace `file` and hash algorithm `sha512`, armored as `ssh-keygen -Y sign -n file`
writes it. The accepted key types are `ssh-ed25519`, `sk-ssh-ed25519@openssh.com`, and
`sk-ecdsa-sha2-nistp256@openssh.com`; Publishers SHOULD use one of the two security-key (`sk-`) types. Verifiers MUST
reject any other key type, namespace, or hash algorithm. For the `sk-` types, verifiers MUST reject a signature whose
flags byte lacks the user-presence bit (`0x01`). `ssh-keygen -Y verify` does not check that bit, so a verifier that
delegates signature checking to it MUST check the flag itself.

**Key fingerprint (normative).** An Author Key's fingerprint is `SHA256:` followed by the unpadded standard base64
encoding of the SHA-256 digest of the key's SSH public-key blob — the form `ssh-keygen -l` prints.

**Signed messages (normative).** An Author Key signs exactly two kinds of message. Each begins with a domain
separator line, so a signature over one kind never verifies as the other, as a bare
[Attestation Payload](#attestation-payload), or as any other file the same key has signed under namespace `file`:

| Message | Bytes |
|---|---|
| Item message | `moat-author-item-v1` LF, then the canonical Attestation Payload for the item's Content Hash |
| List-change message | `moat-allowed-signers-change-v1` LF, the previous list digest, LF, the new list digest, LF |

**Transparency log entry (normative).** The Publisher MUST record each item signature in Rekor as a `rekord` entry
with public-key format `ssh`, whose data is the item message, whose signature is the armored SSHSIG, and whose public
key is the Author Key in OpenSSH public-key form with no comment field. The entry identifies the signer only by the
key; its fingerprint is computed from it. The public key MUST NOT carry a comment, an email address, or any other
personal identifier, and verifiers MUST reject an entry whose public key carries a comment.

**Allowed-signers list (normative).** A source repository lists its Author Keys in `.moat/allowed_signers` at the
repository root. The file is UTF-8 text. Each line is blank, a comment beginning with `#`, or exactly three
whitespace-separated fields: the key's fingerprint, its key type, and its base64 public-key blob. The fingerprint
field MUST equal the fingerprint computed from the blob, and the key type MUST equal the blob's own type and be an
accepted type. A list with any other line, or with no key, is malformed, and verifiers MUST refuse a malformed list
as a whole. *(Informative: the format is a subset of OpenSSH's allowed-signers format with the fingerprint as the
principal, so `ssh-keygen -Y verify -f .moat/allowed_signers -I <fingerprint> -n file` checks a signature against
it.)* The list digest is `sha256:` followed by the lowercase hexadecimal SHA-256 of the list's canonical text: the
file bytes with a leading UTF-8 byte-order mark removed and each CRLF and lone CR replaced by LF.

**List changes (normative).** A change to the list is valid only when signed by a key the previous list allows. To
change the list, the Publisher signs the list-change message for the previous and new list digests with a key in
the previous list, and commits the armored signature as `.moat/allowed_signers.sig` beside the new list.

**Client verification (normative).** To accept the publisher attestation of an item whose `signing_profile` is in
key-fingerprint form, a conforming client MUST:

1. Compute the item's Content Hash over the bytes it installs.
2. Resolve the trusted allowed-signers list for the item's `source_uri` (below).
3. Locate the Publisher's Rekor entry by querying Rekor for entries whose data hash is the SHA-256 of the item
   message built from the Content Hash of step 1, and select the `rekord` entries whose public key's fingerprint
   equals `signing_profile.key_fingerprint`. Zero such entries is a verification failure.
4. Verify the selected entry's SSHSIG over that item message under the signature scheme above.
5. Confirm that `signing_profile.key_fingerprint` is in the trusted allowed-signers list.

A failure at any step is a verification hard failure: the client MUST refuse to install the item. A client MUST
refuse an item signed by a key that is not in the trusted list even when the signature is otherwise valid.

**Trust on first use (normative).** A conforming client keeps one trusted allowed-signers list per `source_uri`, in
the lockfile's `allowed_signers` map. When a key-fingerprint `signing_profile` names a `source_uri` with no trusted
list, the client MUST obtain explicit End User confirmation before installing any item from it, and MUST present:
the `source_uri`; the registry that served the list; each listed key's fingerprint and key type; for each key,
whether its type is a security-key (`sk-`) type; and the statement that a key type does not prove the private key is
held in hardware. On confirmation the client MUST record the list verbatim, its digest, the confirmation time, and
`confirmed_by: "end_user"`.

**List changes on the client (normative).** When `signing_profile.allowed_signers` differs from the trusted list
(by list digest), the client MUST accept the new list without End User confirmation only when
`signing_profile.allowed_signers_change` is a signature that verifies over the list-change message for the trusted
list's digest and the new list's digest, by a key in the trusted list. The client then records the new list with
`confirmed_by: "signed_change"` and SHOULD tell the End User which fingerprints were added and removed. Any other
change MUST be handled as a first sight: the client MUST NOT install items from that `source_uri` until the End User
confirms the new list, and MUST warn that the change was not signed by a previously trusted key. A client that
missed an intermediate list sees a change that does not chain from its record, which is also a first sight. The
trusted list is keyed by `source_uri`, not by registry, so a registry serving a different list than the one
recorded triggers this rule.

**Hardware backing (normative).** A verifier cannot establish from this profile that an Author Key's private key
is held in hardware. An `sk-` key type and the user-presence flag show that the signature passed through a FIDO
authenticator interface, but the profile carries no authenticator attestation, and software authenticators exist.
Conforming clients MUST NOT describe a key, a signature, or an item as hardware-backed, and MAY describe an `sk-`
key as a security-key type.

**Test vectors.** `reference/generate_test_vectors.py` prints the keys, lists, messages, and signatures below; every
key derives from a fixed seed and every signature is deterministic. Each item vector signs the item message for
TV-ACIF-04's Content Hash. `reference/test_author_key.py` checks the vectors against `ssh-keygen`.

| Vector | Case | Expected |
|---|---|---|
| TV-AK-01 | Item signed by `ssh-ed25519` key A; trusted list {A} | `ok` |
| TV-AK-02 | Item signed by key B; trusted list {A} | `signer_not_allowed` |
| TV-AK-03 | TV-AK-01's signature, checked after `scripts/run.sh` is changed, so the recomputed Content Hash differs | `signature_invalid` |
| TV-AK-04 | List change {A} → {A, B} signed by key B | `signer_not_allowed` |
| TV-AK-05 | List change {A} → {A, C} signed by key A | `ok` |
| TV-AK-05b | Item signed by key C after TV-AK-05's rotation; trusted list {A, C} | `ok` |
| TV-AK-06 | Item signed by `sk-ssh-ed25519@openssh.com` key D, user-presence flag set | `ok` |
| TV-AK-07 | Item signed by `sk-ecdsa-sha2-nistp256@openssh.com` key E, user-presence flag set | `ok` |
| TV-AK-08 | Item signed by key D with flags `0x00` | `signature_invalid` |
| TV-AK-09 | List line naming key B's fingerprint beside key A's blob | `allowed_signers_malformed` |

### Trust State Error Vocabulary

Conforming clients MUST expose a trust decision for every registry fetch. This section defines the normative
vocabulary for those decisions so that tooling, telemetry, and downstream integrations can interoperate without
each implementation inventing its own terms.

The vocabulary is a classification, not a wire format. A conforming client MAY surface these states via exit
codes, structured error objects, log fields, or UI labels; the identifiers below are the canonical names.

**Terminal states (per-fetch outcome):**

| Identifier                  | Meaning                                                                                         |
|-----------------------------|-------------------------------------------------------------------------------------------------|
| `MOAT_SIGNED`               | Manifest signature verified; signing identity matched the pinned `registry_signing_profile`.    |
| `MOAT_UNSIGNED`             | Manifest fetched without a `.sigstore` bundle and the registry has no pinned signing identity.  |
| `MOAT_INVALID`              | Manifest or bundle failed cryptographic verification (bad signature, bad Rekor entry, etc.).    |
| `MOAT_IDENTITY_MISMATCH`    | Signature verified but the signing identity does not match the pinned `registry_signing_profile`. |
| `MOAT_IDENTITY_UNPINNED`    | Manifest declares a `registry_signing_profile` but the client has no stored pin (first fetch).  |
| `MOAT_TRUSTED_ROOT_STALE`   | Verification refused because the trusted root used for verification is past its freshness cliff. |

**Reserved (not yet in use):**

- `MOAT_REVOKED` — reserved for a future revocation-propagation extension. Conforming clients MUST NOT emit
  `MOAT_REVOKED` in this version of the spec. Future revisions will define the signaling surface.

**Classification rules:**

- Every fetch MUST resolve to exactly one terminal state.
- `MOAT_SIGNED` and `MOAT_UNSIGNED` are the only success states. Every other identifier denotes a fetch that
  MUST NOT be accepted as authoritative without explicit End User override.
- `MOAT_INVALID` and `MOAT_IDENTITY_MISMATCH` are distinct: the former means "the crypto didn't check out";
  the latter means "the crypto checked out but the wrong party signed it." Tooling SHOULD surface them
  differently because the remediation differs (re-fetch vs. investigate publisher compromise).
- `MOAT_IDENTITY_UNPINNED` is reserved for the trust-on-first-use path. If a pin exists and does not match,
  emit `MOAT_IDENTITY_MISMATCH` instead.
- `MOAT_TRUSTED_ROOT_STALE` is a client-local state (the trusted root bundle has aged out), not a property
  of the fetched manifest. A fetch that would have been `MOAT_SIGNED` against a fresh root MUST be classified
  as `MOAT_TRUSTED_ROOT_STALE` if the root is past the freshness cliff — do not silently downgrade to
  `MOAT_UNSIGNED`.

Conforming clients MAY emit additional implementation-specific identifiers, but the six states above are
reserved names within the `MOAT_*` prefix and MUST carry the meanings defined here.

---

## Version Transition

This section defines how conforming clients handle schema version changes when the `_version` field in the Attestation Payload advances.

### Ordering: Content Hash Before `_version`

When verifying an attestation payload, conforming verifiers MUST check the `content_hash` value BEFORE accepting the `_version` field. The verification order is:

1. Verify `content_hash` matches the Content Hash computed locally over the installed content (by the directory algorithm, or for an ACIF content item as [ACIF Content Items](#acif-content-items) defines).
2. Verify `_version` is a recognized schema version.
3. Verify the Rekor certificate identity.

This ordering is load-bearing: checking `_version` first creates a window where a verifier accepts an old-format attestation for different content (a TOCTOU race). Checking content hash first ensures integrity before format acceptance.

### Grace Period for `_version` Transitions

When a new `_version` value is introduced:

1. Conforming clients MUST accept both the previous and new `_version` values for **6 months** after the new version ships.
2. After the grace period, the previous `_version` MUST be rejected.
3. Publisher re-attestation during the grace period: publishers run the Publisher Action on their source branch (or wait for their registry's next crawl). Old Rekor entries remain valid and independently verifiable for the duration of the grace period.

The 6-month window is calibrated to active-but-infrequent publishers: monthly CI checks cover active publishers; quarterly checks cover publishers who update seasonally. Extending beyond 6 months would increase the replay attack surface (old-format attestations accepted for longer); contracting below 6 months would break dormant-but-maintained repos.

### What Counts as a `_version` Bump

A `_version` bump is required when the Attestation Payload schema changes in a way that makes old payloads unverifiable. Additive-only changes (new optional fields) MAY be handled within the current `_version` using forward-compatibility rules. Breaking changes (field renames, removed fields, format changes) REQUIRE a `_version` bump and a corresponding grace period.

---

## Fork and Lineage Handling

If a repo is forked and the content is unchanged, registries can preserve lineage with `derived_from` while attesting
the fork under a new identity. If the content changes, it becomes a new content hash with explicit lineage. Suspicious
attribution conflicts are surfaced to End Users; they are not automatic hard blocks.

---

## What the Spec Defines

### Normative core

These items are required for conformance. A conforming registry, a conforming client, and a conforming verifier such as
[`moat-verify`](specs/moat-verify.md) all implement exactly these.

- **Content type registry** — normative list of current types (`skill`, `agent`, `rules`, `command`), category
  directory names, and deferred types (`hook`, `mcp`).
- **Repository layout convention** — canonical directory structure and two-tier discovery model (`.moat/publisher.yml` supplements the canonical directories).
- **Registry manifest format** — the signed document a registry publishes. The core artifact of MOAT. Top-level
  fields: `schema_version`, `manifest_uri`, `name`, `operator`, `updated_at`, `registry_signing_profile`,
  `content`, `revocations`. Per-item entries: `name`, `display_name`, `content_hash`, `source_uri`, `attested_at`,
  `derived_from`, `scan_status`, and `signing_profile` (REQUIRED for Dual-Attested items; omitted for Signed and
  Unsigned). See [Registry Manifest](#registry-manifest).
- **Content hashing algorithm** — deterministic, one-pass, Go dirhash-inspired. Defined by normative reference
  implementation ([`reference/moat_hash.py`](reference/moat_hash.py)), not pseudocode. An ACIF content item's
  Content Hash is instead the ACIF attestation input digest; see [ACIF Content Items](#acif-content-items).
- **Hash format** — `<algorithm>:<hex>` with no length constraints.
- **Algorithm requirements** — `sha256` is the REQUIRED algorithm; conforming implementations MUST support it.
  `sha512` is OPTIONAL. The following algorithms are FORBIDDEN and MUST NOT appear in content hashes: `sha1`,
  `md5`, and any algorithm with known practical collision attacks. Conforming clients MUST reject content hashes
  using a forbidden algorithm — this is a hard failure, not a warning. Conforming clients that encounter an
  unrecognized algorithm MUST refuse to verify rather than silently pass.
- **Signature envelope format** — platform-agnostic signing model.
- **Trust tier model** — Dual-Attested / Signed / Unsigned. Absence of Dual-Attested is NOT a negative signal.
- **Publisher signing identity model** — For Dual-Attested items, the registry manifest entry MUST include a
  `signing_profile` field declaring the publisher's expected CI signing identity. See [signing_profile](#signing_profile)
  for the format and known CI provider values.

  A publisher signing identity takes one of two forms. The keyless form is an OIDC issuer URL and a signer
  subject — the values captured in the Fulcio certificate at signing time. The signer subject is the certificate's
  Subject Alternative Name (SAN) URI, which Fulcio derives from provider-specific token claims (see
  [signing_profile](#signing_profile)); it is never the OIDC token's `sub` claim, which does not appear in the
  certificate. This form is provider-agnostic; any CI platform Fulcio supports produces these fields. The
  key-fingerprint form names an Author Key by its fingerprint and is defined by the
  [Author-Key Profile](#author-key-profile). Registries populate `signing_profile` from the publisher's
  `moat-attestation.json` when indexing a Dual-Attested item. For the keyless form, conforming clients MUST verify
  that the Rekor certificate's OIDC issuer and SAN match the declared `signing_profile`. For the key-fingerprint
  form, conforming clients MUST verify the publisher attestation as the Author-Key Profile defines. This check is
  load-bearing for the Dual-Attested tier — without it there is no interoperability guarantee that clients are
  verifying the correct publisher identity.

  **Rename-attack binding (normative for GitHub Actions issuer):** Signer subjects derived from repository names
  are vulnerable to rename and transfer attacks. If a publisher renames or transfers their repository, the signer
  subject changes, and an attacker who claims the old name could produce matching attestations. For signatures whose
  issuer is `https://token.actions.githubusercontent.com`, conforming clients MUST match the immutable numeric
  repository ID and repository owner ID embedded as OIDC extensions on the Fulcio certificate, in addition to the
  signer subject match. Mismatch on any dimension (issuer, signer subject, repository ID, owner ID) is a
  verification hard failure.

  The authoritative OID references are:

  | OID | Extension | Value |
  |---|---|---|
  | `1.3.6.1.4.1.57264.1.15` | `sourceRepositoryIdentifier` | Immutable numeric repository ID (decimal string) |
  | `1.3.6.1.4.1.57264.1.17` | `sourceRepositoryOwnerIdentifier` | Immutable numeric repository-owner ID (decimal string) |

  These extensions are stable across repository renames, transfers, and owner renames. The adjacent OIDs
  `1.3.6.1.4.1.57264.1.12` (`sourceRepositoryURI`) and `1.3.6.1.4.1.57264.1.13` (`sourceRepositoryDigest`) are NOT
  immutable — they carry the human-readable URL and the git commit SHA and change when the repository is renamed
  or the signing commit moves. The rename-attack binding MUST use `.1.15` and `.1.17`.

  For signatures issued by other OIDC providers (GitLab, Buildkite, etc.), equivalent stable-identifier bindings
  are encouraged but remain out of scope of this version of the spec. Conforming clients MAY implement additional
  provider-specific bindings; the GitHub Actions binding is the MUST-level floor.

  **Schema:** `signing_profile.repository_id` and `signing_profile.repository_owner_id` — see
  [signing_profile](#signing_profile) for the data format.

- **Client verification protocol** — what a conforming client must check on install.
- **Revocation mechanism** — `revocations` array in manifest (REQUIRED; empty if none). Each entry MUST include:
  `content_hash`, `reason`, and `details_url` (REQUIRED for registry revocations; OPTIONAL for publisher
  revocations). Reason values (informational only — they do NOT determine client behavior): `malicious`,
  `compromised`, `deprecated`, `policy_violation`. Unknown future reason values MUST be accepted without error.

  **Reason code meanings (informational — for display to End Users and security operators):**

  | Reason | Meaning | Urgency signal |
  |---|---|---|
  | `malicious` | Content has been identified as having malicious behavior (e.g., prompt injection, exfiltration, destructive side effects) | High — surface prominently |
  | `compromised` | The publisher's account, signing key, or distribution channel is believed compromised; content may not be malicious but cannot be trusted as authentic | High — surface prominently |
  | `deprecated` | Publisher has formally deprecated this content in favor of a successor; no security concern | Low — may be surfaced passively |
  | `policy_violation` | Content was removed for registry policy reasons; security posture unspecified | Informational |

  Conforming clients SHOULD surface reason descriptions in user-facing output. The urgency signal is advisory —
  it informs how prominently a client presents the revocation to the End User, not whether the enforcement
  behavior applies.

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
- **Non-interactive client behavior:** Conforming clients operating in non-interactive environments (CI/CD pipelines, fleet management, headless install scripts) MUST exit non-zero and MUST provide a machine-distinguishable error signal when any of the following conditions are encountered. The signal MUST indicate the failure class — the exact mechanism (stderr prefix, structured JSON output, or distinct exit codes) is an implementation choice, but the failure class MUST be distinguishable by an automated caller:

  | Condition | Required client behavior |
  |-----------|-------------------------|
  | TOFU signing profile acceptance required (first registry add) | Exit non-zero. A trust decision that requires human judgment MUST NOT be made silently by a pipeline. |
  | `registry_signing_profile` change detected | Exit non-zero. A signing profile change could indicate registry key compromise. |
  | Publisher revocation encountered | Exit non-zero. Non-interactive clients MUST NOT proceed past revocation warnings. |
  | Allowed-signers confirmation required (first sight of an Author-Key source, or a list change not signed by a trusted key) | Exit non-zero. Trusting an Author Key is a human judgment. |
  | Manifest staleness exceeded | Exit non-zero. A stale manifest means the pipeline is operating on potentially outdated trust data. |

  A conforming non-interactive client MUST NOT auto-accept any trust decision that requires human judgment. A pre-approval mechanism — so operators can authorize registries and signing-profile changes out-of-band, letting pipelines consume them without interactive prompts — is deferred work; see [ROADMAP.md](ROADMAP.md#non-interactive-trust-onboarding).

- **Revocation archival:** Registries MAY prune revocation entries for content no longer present in their manifest after a configurable retention period. The recommended minimum retention period is **180 days**. Pruning before 180 days is non-conforming; registries MAY retain revocations indefinitely.

  **Lockfile is authoritative for pruned revocations.** When a client has previously recorded a revocation in its lockfile `revoked_hashes` array and that revocation entry subsequently disappears from the registry manifest (due to pruning), the lockfile entry persists. The hard-block continues. A client MUST NOT remove a `revoked_hashes` entry because the manifest no longer carries the revocation.

  **Tombstone rule (normative for Registry Action):** Registries MUST NOT re-list a content item in the `content` array if a revocation entry for that item's `content_hash` has been pruned from the `revocations` array. A content hash that was once revoked and subsequently pruned is permanently tombstoned — it MUST NOT reappear as installable content. The Registry Action enforces this via a `revocation-tombstones.json` file in the `moat-registry` branch alongside the manifest. This file contains an array of content_hash strings that must never reappear in the `content` array. The file persists between crawl runs and is appended to (never shrunk) when revocations are pruned from the `revocations` array. This closes the gap for clients who never witnessed the revocation: a previously-revoked hash that reappears in the manifest with no revocation entry would bypass the client's lockfile guard for first-time installers.

  **180-day calibration:** Active developers sync at least monthly; 180 days covers dormant-but-maintained publishers who update quarterly and may sync less often. The recommended minimum ensures that even infrequent users have seen the revocation entry before pruning begins. Security-focused registries SHOULD retain revocations indefinitely.

- **Lineage model** — `derived_from` for forks and adaptations.
- **Version semantics** — `version` is an optional display label; content hash is normative identity; `attested_at` for
  freshness.
- **[`scan_status`](#scan_status) structure** — per-item manifest field. See [scan_status](#scan_status) for the
  full schema and field rules.

### Reference implementations (normative behavior, separate artifacts)

- **[`reference/moat_hash.py`](reference/moat_hash.py)** — Python reference implementation. A conforming implementation produces identical output for all
  test vectors. Two independent implementations in different languages must pass all test vectors before the spec
  advances beyond Draft.
- **[`reference/moat_verify.py`](reference/moat_verify.py)** — `moat-verify` reference implementation (Python). Spec: [`specs/moat-verify.md`](specs/moat-verify.md)
- **[`reference/moat-publisher.yml`](reference/moat-publisher.yml)** — Publisher Action workflow template. Spec: [`specs/github/publisher-action.md`](specs/github/publisher-action.md)
- **[`reference/moat-registry.yml`](reference/moat-registry.yml)** — Registry Action workflow template. Spec: [`specs/github/registry-action.md`](specs/github/registry-action.md)
- **[`reference/generate_test_vectors.py`](reference/generate_test_vectors.py)** — **Normative.** See [Reference implementations](#reference-implementations) above for the authoritative description.

### Informative profiles

- **Sigstore profile** — keyless OIDC signing via Fulcio/Rekor.

The [Author-Key Profile](#author-key-profile) is normative and defined in the Trust Model.

---

## Discovery

A registry index lists known registries and their manifest URLs, allowing conforming clients to present users with
available options without requiring manual URL entry. A community-owned index repo can serve this role.

### Registry Index Format (normative)

A valid registry index is a signed JSON document hosted at a stable URL. See [Registry Index](#registry-index) for
the minimum structure and field requirements.

### Index Operator Requirements (normative)

- Registry indices MUST be signed using the same Sigstore keyless OIDC mechanism used for registry manifests. The
  index signature MUST be logged to Rekor.
- Index operators MUST publish a public governance document at the URL declared in `governance_url`. The document
  MUST cover: inclusion criteria, removal policy, incident response process, dispute resolution, and signing key
  management. The governance document content is the index operator's responsibility — this spec requires it to exist,
  be public, and cover the listed topics; it does not dictate the specific policies.

### Client Requirements for Registry Indices (normative)

The operator that ships a default index source in a conforming client holds de facto discovery authority — their
curation determines which registries users are offered. The spec cannot govern index operator decisions, but it
governs how clients handle them:

- Conforming clients MUST surface which registry index(es) they use for discovery before presenting registry options
  to the End User.
- Conforming clients MUST support user-configurable index sources. Users MUST be able to add, remove, or replace any
  index source including any pre-configured defaults.
- Conforming clients MUST NOT treat any registry index as an authoritative or exclusive discovery source. Users MUST
  be able to add registries by direct manifest URL without using an index at all.
- Adding a registry discovered through an index requires the same explicit End User trust action required for all
  registries. The index shapes the discovery menu; it does not bypass the per-registry trust requirement.

---

## Data Formats

All normative data formats used in the MOAT protocol are defined here. Conceptual and normative sections link to
these definitions rather than embedding schemas inline.

### Registry Manifest

The registry manifest is the signed document a registry publishes — the central trust artifact conforming clients
verify on every install and sync.

Minimum structure:

```json
{
  "schema_version": 1,
  "manifest_uri": "https://example.com/moat-manifest.json",
  "name": "Example Registry",
  "operator": "Example Operator",
  "updated_at": "2026-04-09T00:00:00Z",
  "self_published": false,
  "registry_signing_profile": {
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "https://github.com/owner/repo/.github/workflows/moat-registry.yml@refs/heads/main"
  },
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
  ],
  "revocations": []
}
```

| Field                              | Required                                       | Description                                                                                                                                                                                                                     |
|------------------------------------|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `schema_version`                   | REQUIRED                                       | Manifest format version; currently `1` (integer)                                                                                                                                                                                |
| `manifest_uri`                     | REQUIRED                                       | Canonical URL at which this manifest is hosted. MUST be a stable path-based URL with no query parameters or fragments — the bundle URL is derived from it. Clients MAY use to detect substitution attacks.                      |
| `name`                             | REQUIRED                                       | Human-readable registry name                                                                                                                                                                                                    |
| `operator`                         | REQUIRED                                       | Human-readable name of the registry operator. Display label only — changes do NOT trigger re-approval.                                                                                                                          |
| `updated_at`                       | REQUIRED                                       | RFC 3339 UTC timestamp of when this manifest was last generated. For display and activity monitoring only — the staleness check uses the client's last-fetch timestamp, not this field.                                         |
| `expires`                          | OPTIONAL                                       | RFC 3339 UTC timestamp after which conforming clients MUST reject this manifest. The Registry Action auto-populates this field. See [Freshness Guarantee and Replay Scope](#freshness-guarantee-and-replay-scope).               |
| `self_published`                   | OPTIONAL                                       | `true` if the registry operator and publisher are the same entity (same repository runs both Publisher Action and Registry Action). Absent is equivalent to `false`. Conforming clients SHOULD surface this to End Users when `true`. |
| `registry_signing_profile`         | REQUIRED                                       | The registry's CI signing identity. Conforming clients MUST track this per registry; changes on a subsequent fetch require End User re-approval before the manifest is accepted. See [Signature Envelope](#signature-envelope). |
| `registry_signing_profile.issuer`  | REQUIRED                                       | OIDC issuer URL of the registry's CI provider                                                                                                                                                                                   |
| `registry_signing_profile.subject` | REQUIRED                                       | Signer subject: the Subject Alternative Name (SAN) URI in the registry's Fulcio signing certificate. See [signing_profile](#signing_profile) for the per-provider form.                                                        |
| `content`                          | REQUIRED                                       | Array of per-item entries                                                                                                                                                                                                       |
| `content[].name`                   | REQUIRED                                       | Canonical identifier for the content item                                                                                                                                                                                       |
| `content[].display_name`           | REQUIRED                                       | Human-readable name                                                                                                                                                                                                             |
| `content[].type`                   | REQUIRED                                       | One of: `skill`, `agent`, `rules`, `command`                                                                                                                                                                                 |
| `content[].content_hash`           | REQUIRED                                       | `<algorithm>:<hex>` — normative identity of the content                                                                                                                                                                         |
| `content[].source_uri`             | REQUIRED                                       | Source repository URI                                                                                                                                                                                                           |
| `content[].attested_at`            | REQUIRED                                       | Registry attestation timestamp (RFC 3339 UTC)                                                                                                                                                                                   |
| `content[].private_repo`           | REQUIRED                                       | `true` if sourced from a private or internal repository                                                                                                                                                                         |
| `content[].rekor_log_index`        | REQUIRED for Signed + Dual-Attested            | Integer index of the registry's Rekor transparency log entry attesting this content item. Absent for Unsigned items — its absence is the Unsigned tier signal.                                                                  |
| `content[].derived_from`           | OPTIONAL                                       | Source URI of the item this was forked or derived from                                                                                                                                                                          |
| `content[].version`                | OPTIONAL                                       | Display label only; `content_hash` is normative identity                                                                                                                                                                        |
| `content[].scan_status`            | OPTIONAL                                       | See [scan_status](#scan_status)                                                                                                                                                                                                 |
| `content[].signing_profile`        | REQUIRED for Dual-Attested                     | See [signing_profile](#signing_profile)                                                                                                                                                                                         |
| `content[].acif`                   | OPTIONAL                                       | Present only on an ACIF content item; its presence selects the [ACIF Content Items](#acif-content-items) Content Hash method |
| `content[].acif.entry_file`        | REQUIRED when `acif` is present                | The item's canonical entry file, as a path relative to the item root                                                                                                                                                          |
| `content[].attestation_hash_mismatch` | OPTIONAL                                    | `true` if the registry's computed hash for this item differed from the hash recorded in the publisher's `moat-attestation.json`. Present only when a mismatch was detected; absent otherwise. Indicates that the publisher's attestation does not cover the current content. |
| `revocations`                      | REQUIRED                                       | Array of revocation entries; empty array if none                                                                                                                                                                                |
| `revocations[].content_hash`       | REQUIRED                                       | Hash of the revoked content item                                                                                                                                                                                                |
| `revocations[].reason`             | REQUIRED                                       | One of: `malicious`, `compromised`, `deprecated`, `policy_violation`                                                                                                                                                            |
| `revocations[].details_url`        | REQUIRED for registry / OPTIONAL for publisher | URL to public revocation details                                                                                                                                                                                                |
| `revocations[].source`             | OPTIONAL                                       | Revocation source: `"registry"` or `"publisher"`. Absent defaults to `"registry"` (fail-closed). Determines client behavioral class — see [Revocation Mechanism](#revocation-mechanism).                                        |

**Field notes:**

- `registry_signing_profile` is the registry-level signing identity. It is structurally identical to the keyless
  form of per-item `signing_profile` (issuer + subject) but scoped to the manifest document itself, not to a
  publisher's content attestation. Conforming implementations MUST NOT conflate these two fields. A
  `registry_signing_profile` is always in keyless form.
- `operator` and `name` are display labels. Conforming clients MUST NOT treat changes to these fields as signing
  identity changes and MUST NOT require re-approval when they change.
- `updated_at` uses the registry's clock. The staleness check runs against the client's own `fetched_at`
  timestamp, not against `updated_at`. See [Freshness Guarantee and Replay Scope](#freshness-guarantee-and-replay-scope).
- `content[].name` + `content[].type` MUST be unique within a single manifest. The compound key `(name, type)` is the normative uniqueness constraint. A manifest with two entries sharing the same `name` and `type` is malformed — conforming registries MUST NOT publish such a manifest. If the same content appears under two different `name` values, both entries are valid. Cross-registry name collisions (same name+type appearing in two different registries) are handled by the conforming client, which SHOULD display `source_uri` alongside the content name to disambiguate. The `source_uri` field (REQUIRED on every manifest entry) provides all the disambiguation data needed.

### Lockfile

The lockfile is maintained by a conforming client to record all installed content and enforce revocation blocks.

Minimum structure:

```json
{
  "moat_lockfile_version": 1,
  "registries": {
    "https://example.com/moat-manifest.json": {
      "fetched_at": "2026-04-13T00:00:00Z"
    }
  },
  "entries": [
    {
      "name": "string",
      "type": "skill|agent|rules|command",
      "registry": "https://...",
      "content_hash": "sha256:<hex>",
      "trust_tier": "DUAL-ATTESTED|SIGNED|UNSIGNED",
      "attested_at": "RFC 3339 UTC",
      "pinned_at": "RFC 3339 UTC",
      "attestation_bundle": {},
      "signed_payload": {}
    }
  ],
  "revoked_hashes": [],
  "allowed_signers": {
    "https://github.com/owner/repo": {
      "list": "<allowed-signers file, verbatim>",
      "digest": "sha256:<hex>",
      "confirmed_at": "RFC 3339 UTC",
      "confirmed_by": "end_user|signed_change"
    }
  }
}
```

| Field                          | Required | Description                                                                                           |
|--------------------------------|----------|-------------------------------------------------------------------------------------------------------|
| `moat_lockfile_version`        | REQUIRED | Schema version; currently `1`                                                                         |
| `registries`                   | REQUIRED | Per-registry tracking object; keys are registry manifest URLs                                         |
| `registries[url].fetched_at`   | REQUIRED | RFC 3339 UTC timestamp of the client's last successful manifest fetch for this registry. Used for staleness enforcement and `moat-verify` staleness auditing. |
| `entries`                      | REQUIRED | Array of installed content records                                                                    |
| `entries[].name`               | REQUIRED | Content item name as recorded in the registry manifest                                                |
| `entries[].type`               | REQUIRED | Content type; closed set: `skill`, `agent`, `rules`, `command`                                     |
| `entries[].registry`           | REQUIRED | Registry manifest URL the item was installed from                                                     |
| `entries[].content_hash`       | REQUIRED | `<algorithm>:<hex>` — normative identity of the installed item                                        |
| `entries[].trust_tier`         | REQUIRED | Trust tier at install time: `DUAL-ATTESTED`, `SIGNED`, or `UNSIGNED`                                  |
| `entries[].attested_at`        | REQUIRED | Registry's attestation timestamp (registry clock, not client clock)                                   |
| `entries[].pinned_at`          | REQUIRED | Local install timestamp (client clock; not externally verifiable)                                     |
| `entries[].attestation_bundle` | REQUIRED | Full cosign bundle captured at install time; `null` for `UNSIGNED` content                            |
| `entries[].signed_payload`     | REQUIRED | The original payload passed to `cosign sign-blob` at attestation time; `null` for `UNSIGNED` content |
| `entries[].acif`               | REQUIRED for an ACIF content item | The manifest entry's `acif` object, copied verbatim; absent otherwise                     |
| `allowed_signers`              | REQUIRED once any list is trusted | Trusted allowed-signers lists keyed by `source_uri`; see [Author-Key Profile](#author-key-profile). Absent is equivalent to empty |
| `allowed_signers[uri].list`    | REQUIRED | The trusted list, verbatim                                                                    |
| `allowed_signers[uri].digest`  | REQUIRED | List digest of `list`                                                                         |
| `allowed_signers[uri].confirmed_at` | REQUIRED | RFC 3339 UTC time the list became trusted (client clock)                                 |
| `allowed_signers[uri].confirmed_by` | REQUIRED | `end_user` (confirmed by the End User) or `signed_change` (accepted as a signed list change) |
| `revoked_hashes`               | REQUIRED | Array of hard-blocked content hash strings; empty array if none                                       |

**Field notes:**

- `entries[].attested_at` is the registry's clock, not the client's — do not build freshness logic on it.
- `entries[].trust_tier` records the trust tier as determined at install time. It does not update automatically if the registry changes the tier after installation.
- `entries[].attestation_bundle` is the signature, signing certificate, and Rekor transparency log entry as a single embedded JSON object. Conforming clients MUST populate this field at install time — it is required for offline re-verification.
- `entries[].signed_payload` is the verbatim content passed to `cosign sign-blob` at attestation time, stored exactly as-is. Conforming clients MUST populate this field — `cosign verify-blob --offline` requires the original signed artifact. JSON serialization differences invalidate the signature; storing verbatim is the only safe approach. Before storing, conforming clients MUST confirm that `sha256(signed_payload.encode("utf-8"))` equals the `data.hash.value` field of the Rekor entry at `rekor_log_index`. If this check fails, the entry MUST NOT be written to the lockfile and the install MUST be aborted.
- `entries[].type` is a closed set in the current version. Conforming clients MUST accept entries with unrecognized type values without error — new types will be added in future versions.
- `entries[].registry` MUST be treated as permanently stable once published. A URL change invalidates all lockfile entries referencing it.
- `revoked_hashes` entries MUST NOT be silently removed. Clearing a revoked hash requires deliberate End User action. This prevents the remove-and-reinstall bypass: an attempt to reinstall a revoked hash is blocked by this record.

**Upgrade path:** If a conforming client reads a lockfile without the `registries` key (upgrade from a pre-staleness lockfile), it SHOULD initialize the key and set `fetched_at` to the current time on the next successful manifest fetch. This prevents clients from immediately treating all installed content as stale after upgrading.

Conforming clients MAY add additional fields to entries but MUST include all fields listed above. A lockfile from one
conforming client must be readable by another.

### Registry Index

A registry index lists known registries and their manifest URLs, enabling conforming clients to present users with
available options without requiring manual URL entry.

Minimum structure:

```json
{
  "schema_version": 1,
  "index_uri": "https://example.com/moat-index.json",
  "operator": "Example Registry Index",
  "governance_url": "https://example.com/moat-governance",
  "updated_at": "2026-04-08T00:00:00Z",
  "registries": [
    {
      "name": "Example Registry",
      "manifest_url": "https://example.com/moat-manifest.json",
      "registry_signing_profile": {
        "issuer": "https://token.actions.githubusercontent.com",
        "subject": "https://github.com/owner/repo/.github/workflows/moat-registry.yml@refs/heads/main"
      },
      "description": "A registry of example skills"
    }
  ]
}
```

| Field                                          | Required | Description                                          |
|------------------------------------------------|----------|------------------------------------------------------|
| `schema_version`                               | REQUIRED | Index format version; currently `1` (integer)        |
| `index_uri`                                    | REQUIRED | Canonical URL at which this index document is hosted |
| `operator`                                     | REQUIRED | Human-readable name of the index operator            |
| `governance_url`                               | REQUIRED | URL of the public governance document                |
| `updated_at`                                   | REQUIRED | RFC 3339 UTC timestamp of the last index update      |
| `registries`                                   | REQUIRED | Array of registry entries                            |
| `registries[].name`                            | REQUIRED | Human-readable registry name                         |
| `registries[].manifest_url`                    | REQUIRED | URL of the registry's signed manifest                |
| `registries[].registry_signing_profile`        | REQUIRED | Expected signing identity for this registry's manifest |
| `registries[].registry_signing_profile.issuer` | REQUIRED | OIDC issuer URL                                      |
| `registries[].registry_signing_profile.subject`| REQUIRED | Signer subject (Fulcio certificate SAN URI)          |
| `registries[].description`                     | OPTIONAL | Short description of the registry's scope or focus   |

**Field notes:**

- `governance_url` MUST reference a publicly accessible document covering: inclusion criteria, removal policy,
  incident response process, dispute resolution, and signing key management. The content is the operator's
  responsibility; this spec requires it to exist, be public, and cover the listed topics.
- `index_uri` MUST be the canonical URL at which this index is hosted. Clients MAY use this to detect index moves
  or substitution attacks.
- `registries[].registry_signing_profile` establishes the expected manifest signing identity for registries
  discovered through this index. Conforming clients SHOULD verify that the first-fetched manifest's
  `registry_signing_profile` matches this value before accepting the registry. This closes the first-fetch trust
  bootstrapping gap for discovered registries. For manually-added registries (not discovered through an index),
  the signing identity is accepted from the manifest on first fetch — the End User's explicit add action is the
  trust anchor. See [Signature Envelope](#signature-envelope).

### scan_status

`scan_status` is an optional per-item manifest field that records the result of a security scan performed by the
registry on a content item.

Minimum structure:

```json
{
  "result": "clean|findings|not_scanned",
  "scanner": [{ "name": "string", "version": "string" }],
  "scanned_at": "ISO8601",
  "findings_url": "https://..."
}
```

| Field          | Required                                        | Description                                                               |
|----------------|-------------------------------------------------|---------------------------------------------------------------------------|
| `result`       | REQUIRED                                        | One of: `clean`, `findings`, `not_scanned`                                |
| `scanner`      | REQUIRED when `result` is `clean` or `findings` | Array of scanner objects; omitted when `not_scanned`                      |
| `scanned_at`   | REQUIRED when `result` is `clean` or `findings` | RFC 3339 UTC scan timestamp; omitted when `not_scanned`                   |
| `findings_url` | OPTIONAL                                        | URL to a public findings report; only present when `result` is `findings` |

**Field notes:**

- `scanner[].name` MUST be the canonical name for well-known scanners (e.g. `"snyk-mcp-scan"`, `"semgrep"`) to
  enable cross-registry aggregation. Additional fields within scanner entries are permitted. Free-form name strings
  defeat aggregation and do not conform.

### signing_profile

`signing_profile` declares a publisher's expected signing identity on Dual-Attested manifest entries, in one of two
forms. A profile that carries `issuer` is in **keyless form**; a profile that carries `key_fingerprint` is in
**key-fingerprint form**. A profile that carries both, or neither, is malformed, and conforming clients MUST NOT
present the item as Dual-Attested.

For the keyless form, conforming clients MUST verify the Rekor certificate's OIDC issuer and SAN match this field.
When the issuer is GitHub Actions, conforming clients MUST additionally match the numeric repository and owner IDs —
see the [rename-attack binding](#publisher-signing-identity-model) requirement.

Minimum keyless structure (any OIDC provider):

```json
{
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "https://github.com/owner/repo/.github/workflows/moat-publisher.yml@refs/heads/main"
}
```

Required keyless structure when `issuer` is `https://token.actions.githubusercontent.com`:

```json
{
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "https://github.com/owner/repo/.github/workflows/moat-publisher.yml@refs/heads/main",
  "repository_id": "123456789",
  "repository_owner_id": "987654321"
}
```

| Field                  | Required                          | Description                                                                                   |
|------------------------|-----------------------------------|-----------------------------------------------------------------------------------------------|
| `issuer`               | REQUIRED in keyless form          | OIDC issuer URL from the CI provider                                                          |
| `subject`              | REQUIRED in keyless form          | Signer subject: the Fulcio certificate's SAN URI, in the form the known-provider table below gives. Not the OIDC token's `sub` claim |
| `repository_id`        | REQUIRED for GitHub Actions issuer; OPTIONAL for others | Decimal string matching the Fulcio cert extension at OID `1.3.6.1.4.1.57264.1.15`          |
| `repository_owner_id`  | REQUIRED for GitHub Actions issuer; OPTIONAL for others | Decimal string matching the Fulcio cert extension at OID `1.3.6.1.4.1.57264.1.17`          |
| `profile_version`      | OPTIONAL                          | Integer schema version for additive extensions; absent or `1` = baseline v1 shape. Current: 1 |
| `subject_regex`        | OPTIONAL                          | Regex alternative to exact `subject` match for publishers that sign across multiple refs      |
| `issuer_regex`         | OPTIONAL                          | Regex alternative to exact `issuer` match for organizations running multiple OIDC instances   |

Key-fingerprint structure ([Author-Key Profile](#author-key-profile)):

```json
{
  "key_fingerprint": "SHA256:c+9RtDpLaogkdIBaK4R83aEOVfIlPvftuiSpqVLOQA4",
  "allowed_signers": "SHA256:c+9RtDpLaogkdIBaK4R83aEOVfIlPvftuiSpqVLOQA4 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII5C8Sf8CM8ca7csOPFWeq4DJeLtXJEUFJ1C6C7CZ4Ig\n"
}
```

| Field                    | Required                         | Description |
|--------------------------|----------------------------------|-------------|
| `key_fingerprint`        | REQUIRED in key-fingerprint form | Fingerprint of the Author Key that signed the publisher attestation |
| `allowed_signers`        | REQUIRED in key-fingerprint form | The source repository's `.moat/allowed_signers` file at the crawled commit, verbatim, as a JSON string |
| `allowed_signers_change` | OPTIONAL                         | The source repository's `.moat/allowed_signers.sig` file at the crawled commit, verbatim: the armored list-change signature. Absent when the source has no such file |

In key-fingerprint form, `subject_regex`, `issuer_regex`, `repository_id`, and `repository_owner_id` MUST be absent.
A registry MUST NOT emit two entries for the same `source_uri` whose key-fingerprint profiles carry different
`allowed_signers` values in one manifest, and a conforming client that receives such a manifest MUST NOT install
any item from that `source_uri` from it. The npm distribution channel defines only the keyless form.

**Back-compatibility:** Profiles captured before versioning are treated as `profile_version: 1`. Conforming clients
MUST accept profiles without a `profile_version` field and MUST treat them as v1. The `profile_version` field bumps
to `2` or higher when new issuers add equivalent stable-identifier fields (e.g., GitLab `project_id`).

**Regex fields:** `subject_regex` and `issuer_regex` are convenience mechanisms for publishers who sign from
multiple branches or forked environments. When both `subject` and `subject_regex` are present, the client MUST
accept the signature if either the exact subject OR the regex matches. Regex fields MUST NOT relax the numeric-ID
binding requirement — they apply only to the issuer/subject dimensions.

*Informative — known CI provider values:*

| Provider | Issuer | Signer subject (certificate SAN) | Fulcio derives it from |
|----------|--------|----------------------------------|------------------------|
| GitHub Actions | `https://token.actions.githubusercontent.com` | `https://github.com/{owner}/{repo}/{workflow_path}@refs/heads/{branch}` | `job_workflow_ref`, prefixed with `https://github.com/` |
| GitLab CI (GitLab.com) | `https://gitlab.com` | `https://gitlab.com/{namespace}/{project}//{ci_config_path}@refs/heads/{branch}` | `ci_config_ref_uri`, prefixed with `https://` |

Source: Fulcio's OIDC documentation ([`docs/oidc.md`](https://github.com/sigstore/fulcio/blob/main/docs/oidc.md)) and its issuer configuration
([`config/identity/config.yaml`](https://github.com/sigstore/fulcio/blob/main/config/identity/config.yaml)), which map each issuer to the claim that becomes the SAN. Two
consequences follow. For GitHub Actions, `{workflow_path}` is the path of the workflow that ran the signing job,
such as `.github/workflows/moat-publisher.yml`; when that job runs in a reusable workflow, the SAN names the reusable
workflow, not the caller. For GitLab CI, the double slash before `{ci_config_path}` is part of the claim and is
preserved. A tag ref appears as `@refs/tags/{tag}` in both forms.

Other providers with OIDC support: the issuer is the provider's OIDC endpoint URL; the SAN form is defined by
Fulcio's configuration for that issuer. Providers are added to this table when their SAN form is verified against
Fulcio's issuer configuration and a working Sigstore implementation. Forgejo/Codeberg Actions OIDC support is not yet
shipped as of this writing (April 2026). Tracking: Gitea PR
[#36988](https://github.com/go-gitea/gitea/pull/36988) (draft, opened 2026-03-25) and Forgejo PR
[#5344](https://codeberg.org/forgejo/forgejo/pulls/5344) (closed 2025-02-02, no active successor). When either
ships, the issuer will be `<instance-url>/api/actions/oidc`; its SAN form is fixed only when Fulcio's issuer
configuration adds it. Check these PRs and that configuration before updating this table.

### Attestation Payload

The canonical payload signed by both the Registry Action and the Publisher Action to create per-item Rekor
entries. Signing identical payload bytes for the same content hash is what enables the Registry Action to verify
publisher attestations at crawl time — Publisher and Registry entries for the same item are distinguished by the
signer subject (certificate SAN) in the Rekor certificate (different workflow file paths), not by payload content.
Under the [Author-Key Profile](#author-key-profile) the Publisher signs this payload wrapped in a domain-separated
item message, and the entry is distinguished by the Author Key's fingerprint.

Minimum structure:

```json
{"_version":1,"content_hash":"sha256:<hex>"}
```

Serialization rules (normative):
- UTF-8 encoding, no BOM
- No trailing newline
- No whitespace inside or outside the JSON object
- Keys in lexicographic order (`_version` sorts before `content_hash`; underscore ASCII 95 < 'c' ASCII 99)
- Exactly two keys: `"_version"` (integer `1`) and `"content_hash"` with the `<algorithm>:<hex>` value from the manifest entry

Python canonical form:
```python
payload = json.dumps(
    {"_version": 1, "content_hash": content_hash},
    separators=(",", ":"),
    sort_keys=True,
).encode("utf-8")
```

**Test vector:**

| Field | Value |
|---|---|
| Input hash | `sha256:3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b` |
| Payload bytes | `{"_version":1,"content_hash":"sha256:3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b"}` |
| SHA-256 of payload | `b7d70330da474c9d32efe29dd4e23c4a0901a7ca222e12bdbc84d17e4e5f69a4` |

**Field notes:**

- `rekor_log_index` in each manifest entry is the log index returned by Rekor for this per-item signing operation.
  Conforming clients MUST store both the cosign bundle and this canonical payload as `attestation_bundle` and
  `signed_payload` in the lockfile entry — `cosign verify-blob --offline` requires the original signed bytes.
- `_version` enables format evolution without ambiguity. Verifiers that encounter an unrecognized `_version` value
  MUST fail the verification rather than proceeding against an unknown payload schema.
- This format attests exactly one fact (this content hash was signed at this schema version) and is reproducible
  from the manifest entry alone. Verifiers reconstruct the payload from the `content_hash` field and verify the
  signature without storing extra registry context in the Rekor record.

See [Publisher Action](specs/github/publisher-action.md#attestation-payload-schema-normative) for the publisher-side
signing requirement.

**ACIF test vectors:** The payload for an [ACIF content item](#acif-content-items) carries the attestation input
digest as its Content Hash. Item files, the `publisher_section` each `metadata_hash` is computed from, and the full
preimages are printed by `reference/generate_test_vectors.py`. Each skill's entry file is `SKILL.md`.

| Vector | Item | `body_hash` | `metadata_hash` | Content Hash | SHA-256 of payload |
|---|---|---|---|---|---|
| TV-ACIF-01 | Single-file, no frontmatter | `sha256:12d3cb2f53305b53fff6ca4ff1166fd1d063b1319642e0a0906a5539c8fa57b7` | absent | `sha256:609902f740f65673401adc2b6e3a549ae1ff77817791ba3e1c410c77b463cdda` | `b1d75a3ff67826bf67e7fe970450195f039884da2ab8a56e6210c745704d086a` |
| TV-ACIF-02 | Single-file, CRLF line endings, frontmatter | `sha256:12d3cb2f53305b53fff6ca4ff1166fd1d063b1319642e0a0906a5539c8fa57b7` | `sha256:b864cc13e7d6658f120ec10fa7ebf0da222487f5ba9440cee5221c5501021122` | `sha256:d76a2362e3672347120e74159450b38099b7bb4ba8bd648593c8eaa14abd87c8` | `e82b1b676791f7a044f05b18cf75193b2c0e1c2757740a0a478e3ffb55af6890` |
| TV-ACIF-03 | Multi-file, no frontmatter | `sha256:fef9a3e615ab4d41c1a990908bf9a3e5b47f70a73eaa16fc7e1578c9f4ab60df` | absent | `sha256:e42751ba6779bf949837e9bc88e84600909d6941c85185ae92f6ac5d9c13c34e` | `efbbcc1fb71c482d0254e76568f9baecf6fc87ae97db101f6a809531dd3f754c` |
| TV-ACIF-04 | Multi-file, entry-file frontmatter | `sha256:b08c2af8a9d5c2eced158b49a13bacfe3d0a22221b965bd2a46672bc5b8f9648` | `sha256:8f1d5123f9ef00c769939da3b95ba9708f6a4a98ad5fcffc0f89103727c44bb5` | `sha256:4cf794439192206d27c8137607b37884316f26f3fe52d725b1ac1dfcac58c2ff` | `e413a17e93045558f8ef62c35609b44464321851174f5e86d1d9bf4f3acad2f2` |

Payload bytes are `{"_version":1,"content_hash":"<Content Hash>"}` with the Content Hash from the table. The
generator cross-checks TV-ACIF-01..04 `body_hash` values against ACIF's own vectors and the attestation input
construction against ACIF's TV-L3 (e) cases.

---

## Security Considerations

### Revocation Propagation Worst Case

The revocation propagation time under MOAT's default-expiry model is bounded as follows:

**Default-expiry registries (72-hour `expires`):**
- Publisher revokes content.
- Registry next crawl picks up the revocation: up to **24 hours** (registry crawl interval).
- Client manifest expires and is refreshed on next install attempt: up to **72 hours** from last fetch.
- **Total worst case: 96 hours (4 days)** for default-expiry registries (72h expiry + 24h crawl).

The crawl delay and client expiry run in parallel, not sequentially — after the manifest expires, the client refreshes on the next install attempt and immediately receives the updated manifest containing the revocation. There is no additional window after expiry. In practice, active developers trigger install or sync operations daily; the typical propagation time is under 24 hours for active users.

**Security-critical registries (short `expires`, e.g., 4 hours):**
- Registry crawl: up to 24 hours.
- Client manifest expires and refreshes: up to 4 hours.
- **Total worst case: 28 hours.**
- For emergency revocations with immediate manifest regeneration: 0-hour crawl + 4-hour expiry = **4 hours**.

Registry operators handling sensitive content SHOULD set `expires` to 4 hours or less to minimize the exploitation window.

### Replay Attack Scope

MOAT does not defend against manifest replay attacks within the valid staleness window. A replay attack requires an attacker who can intercept or cache-poison a client's manifest fetch AND a revocation that was issued after the cached manifest was generated AND a client that has not refreshed within the staleness window. These conditions narrow the exploitable window significantly in practice.

### Trust Decision Attack Surface

TOFU (trust-on-first-use) for manually-added registries is a known attack surface. An attacker who can intercept the first manifest fetch for a new registry can inject a malicious `registry_signing_profile`. Registries discovered through a signed Registry Index close this gap — the Index entry establishes the expected signing identity before first fetch. For manually-added registries, the End User's explicit add action is the trust bootstrap; MOAT cannot provide a stronger guarantee without a pre-established PKI.

### Lockfile Integrity

The lockfile is not protected by a MAC or checksum. An attacker with local write access can modify the lockfile directly. However, an attacker with local write access can also modify the installed content directly — the lockfile is not the weakest link. Detection (via `moat-verify`) is the right approach: `moat-verify` re-hashes installed content and compares against the lockfile, detecting both content tampering and lockfile manipulation when the two diverge.

**Detection scope (precision note):** `moat-verify` detects accidental corruption and inconsistent modification — cases where the lockfile says hash X but content hashes to Y. It does NOT detect targeted tampering where an attacker modifies installed content AND updates the lockfile with matching hashes AND removes revocation entries consistently. This is an inherent limitation of any local-only integrity check without an external trust anchor. Users requiring stronger guarantees should verify against the registry manifest and Rekor log directly.

### Author-Key Trust

The Author-Key Profile moves the publisher trust decision from a CI identity to a key list, and its first-sight
confirmation is a TOFU boundary of the same kind as manually adding a registry: an attacker who controls the source
repository or the serving registry before the End User's first install can present their own key. After first
sight, a list change is accepted silently only when a trusted key signs it, so a stolen trusted key can rewrite the
list. Clients report accepted changes so an End User can notice one they did not expect, and a Publisher whose key
is compromised recovers through a registry revocation and End User re-confirmation, not through the list. The
profile does not prove a key is held in hardware; see the Hardware backing rule in the
[Author-Key Profile](#author-key-profile).

### ACIF Content Item Coverage

An ACIF content item's Content Hash covers its body and its declared metadata, including the frontmatter grants
that ACIF's `body_hash` alone excludes. A verifier that matched a signature against a `body_hash` or
`attestation_hash` copied from a record, instead of recomputing both hashes over installed bytes, would accept
content whose grants changed after signing. The [ACIF Content Items](#acif-content-items) computation rule forbids
that.

---

## OWASP Alignment

MOAT is validated against six OWASP standards: CI/CD Security Top 10 (critical), Top 10 for Agentic Applications 2026
(critical), Top 10:2025 (high), LLM Top 10:2025 (high), Agentic Skills Top 10:2026 (high), and API Security Top 10:2023
(medium).

Core coverage: ASI04, CICD-SEC-9, AST01, AST02, LLM03:2025, A03:2025, and A08:2025.

Remaining gaps — CICD-SEC-8 (federation), API2:2023 (publisher authentication), API7:2023 (SSRF in federation) —
are tracked as deferred features (Issues 10 and 11). These gaps are acknowledged v0.5.0 limitations; they will be
addressed in the version that introduces federation and private registry auth.

**Full alignment map:** [`docs/owasp-alignment.md`](docs/owasp-alignment.md)

