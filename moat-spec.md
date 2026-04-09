# Model for Origin Attestation and Trust (MOAT) Specification

**Version:** 0.4.0 (Draft)
**Status:** Draft
**Date:** 2026-04-08
**Editor:** Holden Hewett
**License:** Apache-2.0 (https://www.apache.org/licenses/LICENSE-2.0)
**Repository:** https://github.com/OpenScribbler/moat
**Sub-specs:** [`specs/publisher-action.md`](specs/publisher-action.md), [`specs/moat-verify.md`](specs/moat-verify.md)
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

MOAT involves six distinct actors. They are not interchangeable.

**End User** — The human who chooses which registries to trust and approves installs or use of content through a
conforming client. This includes individual users and team or enterprise administrators enforcing local policy. MOAT
requires clients to surface trust tier and revocation state clearly so the End User can make an informed decision.

**Publisher** — Creates content and keeps it in a source repository. Wants accurate source attribution, visible lineage
for forks, and an optional low-friction way to co-attest content from the source repository. A publisher may adopt the
[Publisher Action](specs/publisher-action.md) to produce source-side attestations, but MOAT does not require the
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

## Conforming specs

MOAT is a protocol specification, not an implementation. It defines normative behavior for conforming clients and
registries, but it does not define any specific implementation. The following companion specs are normative parts of the
MOAT ecosystem:

**[moat-verify](specs/moat-verify.md)** — A standalone verification tool that lets any reader independently audit the
MOAT trust chain for a content item without installing or executing it. Its use case is diagnosis, validation, and
interoperability testing. It is therefore not a conforming client and not a runtime.

**[Publisher Action](specs/publisher-action.md)** — A GitHub Actions workflow that publishers can adopt to generate
source-side attestations. This is normative for the Dual-Attested trust tier, but it is not required to run a registry
or be a conforming client. Registries that want to support Dual-Attested content MUST be able to consume attestations

### Reference implementations

**[`reference/moat_hash.py`](reference/moat_hash.py)** — Python reference implementation of the MOAT content hashing
algorithm. Conforming implementations in any language MUST produce identical output for all test vectors.

**[`reference/generate_test_vectors.py`](reference/generate_test_vectors.py)** — Generates the canonical test vector
suite used to validate conforming implementations of the content hashing algorithm.

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
[`specs/publisher-action.md`](specs/publisher-action.md)

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
- MUST NOT use a cached registry manifest for revocation checks when the cached copy exceeds a configurable
  staleness threshold (default: 24 hours). When the threshold is exceeded, the client MUST sync the manifest
  before performing revocation checks. Clients SHOULD NOT allow this threshold to be configured above 48 hours —
  doing so widens the replay window beyond what the protocol's freshness guarantees are designed around.
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
| `subagent` | `subagents/` | Specialized persona definitions with controlled tools/context |

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
```

The [Publisher Action](specs/publisher-action.md) uses a two-tier discovery model:

- **Tier 1:** Canonical category directories
- **Tier 2:** `moat.yml` for custom layouts; when present it overrides Tier 1

`moat-attestation.json` is a reserved filename. The [Publisher Action](specs/publisher-action.md) writes this file to a
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
| **Dual-Attested** | Registry-signed and independently attested by the source repo CI for the same content hash |
| **Signed**        | Registry-signed with a Rekor transparency log entry. Tamper-evident. Registry-attested.    |
| **Unsigned**      | No MOAT attestation. Works, but labeled clearly.                                           |

`Dual-Attested` will be rare at launch. Its absence is not a negative signal; `Signed` is the standard tier.

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
rules, and conformance expectations are defined by the reference implementation and its test vectors.

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

### Freshness Guarantee and Replay Scope

The 24-hour staleness threshold is MOAT's freshness guarantee. MOAT does not defend against manifest replay
attacks within that window. For a replay attack to succeed, an attacker must be able to intercept or
cache-poison a client's manifest fetch, a revocation must have been issued after the cached manifest was
generated, and the client must not have refreshed within the staleness threshold. These conditions narrow the
exploitable window significantly in practice.

**`updated_at` and the staleness threshold:** The manifest's `updated_at` field records when the registry last
regenerated its manifest and is for display and activity monitoring only. The 24-hour staleness threshold MUST be
computed against the client's own last-fetch timestamp — not against `updated_at`. A manifest whose `updated_at`
is recent but which the client fetched 25 hours ago is stale; a manifest whose `updated_at` is seven days old but
which the client fetched two hours ago is not.

Explicit manifest expiry with an `expires_at` field — where clients hard-reject manifests past their declared
expiry — is deferred to a future version. The prerequisite is registry infrastructure maturity: `expires_at`
creates a hard liveness dependency on the registry's CI pipeline, and a CI outage means the registry's entire
catalog goes dark for all clients. That trade-off is appropriate for registry operators with dedicated
infrastructure and monitoring; it is not appropriate to mandate for the hobbyist and small-team operators
that the current version targets.

### Signature Envelope

The normative signing mechanism for this version of MOAT is Sigstore keyless OIDC signing via Fulcio/Rekor.

**Signing input:** The registry CI signs the manifest JSON file with `cosign sign-blob`. The input to signing is
the raw bytes of the manifest file as it will be served — after any transport-layer decompression, with no
additional normalization. The manifest MUST be served as UTF-8 without a byte-order mark. Once signed and
published, the manifest file is byte-stable: any modification breaks the signature.

**Bundle placement:** The cosign bundle (signature, signing certificate, and Rekor transparency log entry) MUST be
served at `{manifest_uri}.sigstore`. This path is normative — conforming registries MUST serve the bundle there
and conforming clients MUST fetch it from there. The bundle MUST be served at the same availability level as the
manifest itself. A bundle at an ephemeral URL will produce verification failures when it expires.

**Per-item attestation payload:** For Signed and Dual-Attested items, the registry MUST create a per-item Rekor
entry at attestation time by signing a canonical payload with `cosign sign-blob`. The canonical payload format is:

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

| Field          | Value                                                                                        |
|----------------|----------------------------------------------------------------------------------------------|
| Input hash     | `sha256:3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b`                  |
| Payload bytes  | `{"_version":1,"content_hash":"sha256:3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b"}` |
| SHA-256 of payload | `b7d70330da474c9d32efe29dd4e23c4a0901a7ca222e12bdbc84d17e4e5f69a4`                  |

The `rekor_log_index` in each manifest entry is the log index returned by Rekor for this per-item signing
operation. Conforming clients MUST store both the cosign bundle and this canonical payload as `attestation_bundle`
and `signed_payload` in the lockfile entry — `cosign verify-blob --offline` requires the original signed bytes.

The `_version` field enables format evolution without ambiguity. Verifiers that encounter an unrecognized `_version`
value MUST fail the verification rather than proceeding against an unknown payload schema.

This format attests exactly one fact (this content hash was signed at this schema version) and is reproducible
from the manifest entry alone. Verifiers reconstruct the payload from the `content_hash` field and verify the
signature without storing extra registry context in the Rekor record.

**Manifest verification flow:**

1. Fetch the manifest at `manifest_uri`
2. Fetch the bundle at `{manifest_uri}.sigstore`
3. Verify the bundle covers the exact bytes of the downloaded manifest file
4. Confirm the signing certificate's OIDC issuer and subject match the manifest's `registry_signing_profile`
5. Confirm the Rekor transparency log entry in the bundle is valid

Rekor unavailability is a hard failure — there is no fallback to bundle-only verification without Rekor
confirmation. See [Trust Anchor Model](#trust-anchor-model).

**Signing identity trust:**

- For registries discovered through a Registry Index: the index entry's `registry_signing_profile` establishes
  the expected signing identity before the manifest is fetched. Conforming clients SHOULD confirm the manifest's
  declared `registry_signing_profile` matches the index entry before accepting.
- For manually-added registries: the signing identity declared in the manifest is accepted on first fetch. The
  End User's explicit action to add the registry is the trust bootstrap.
- On subsequent fetches: if `registry_signing_profile` has changed, conforming clients MUST require End User
  re-approval before accepting the manifest. `operator` and `name` changes do NOT trigger re-approval.

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

- **Content type registry** — normative list of current types (`skill`, `subagent`, `rules`, `command`), category
  directory names, and deferred types (`hook`, `mcp`).
- **Repository layout convention** — canonical directory structure and two-tier discovery model (`moat.yml` override).
- **Registry manifest format** — the signed document a registry publishes. The core artifact of MOAT. Top-level
  fields: `schema_version`, `manifest_uri`, `name`, `operator`, `updated_at`, `registry_signing_profile`,
  `content`, `revocations`. Per-item entries: `name`, `display_name`, `content_hash`, `source_uri`, `attested_at`,
  `derived_from`, `scan_status`, and `signing_profile` (REQUIRED for Dual-Attested items; omitted for Signed and
  Unsigned). See [Registry Manifest](#registry-manifest).
- **Content hashing algorithm** — deterministic, one-pass, Go dirhash-inspired. Defined by normative reference
  implementation ([`reference/moat_hash.py`](reference/moat_hash.py)), not pseudocode.
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
  flags. This is a known limitation of the current Dual-Attested verification model.

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
- **[`scan_status`](#scan_status) structure** — per-item manifest field. See [scan_status](#scan_status) for the
  full schema and field rules.

### Reference implementations (normative behavior, separate artifacts)

- **[`reference/moat_hash.py`](reference/moat_hash.py)** — Python reference implementation. A conforming implementation produces identical output for all
  test vectors. Two independent implementations in different languages must pass all test vectors before the spec
  advances beyond Draft.
- **[`reference/generate_test_vectors.py`](reference/generate_test_vectors.py)** — Generates the canonical test vector suite used to validate conforming implementations.
- **`moat-verify`** — Standalone verification script. Spec: [`specs/moat-verify.md`](specs/moat-verify.md)
- **Publisher Action** — GitHub Actions workflow for source repos. Spec:
  [`specs/publisher-action.md`](specs/publisher-action.md)

### Informative profiles

- **Sigstore profile** — keyless OIDC signing via Fulcio/Rekor.

---

## Publisher Action

The Publisher Action is the primary adoption mechanism for the `Dual-Attested` tier. Any source repo adds a single
workflow file — no key management, no MOAT-specific knowledge required.

The Publisher Action is publisher-side CI tooling. It is not a registry, not a conforming client, and not an AI
agent runtime.

On push, it discovers content items, computes content hashes, signs each with `cosign sign-blob` via Sigstore keyless
OIDC, and writes `moat-attestation.json` to the `moat-attestation` branch with Rekor references. Pushing to a
dedicated branch avoids main branch protection rules and eliminates commit churn on the source branch.

Publisher revocation also flows through this action: publishers add a revocation entry, trigger the workflow, and
optionally notify registries by webhook. Publisher revocations are warnings, not hard blocks.

**Full specification:** [`specs/publisher-action.md`](specs/publisher-action.md)

---

## moat-verify

`moat-verify` is a standalone Python 3.9+ verification tool. It imports [`reference/moat_hash.py`](reference/moat_hash.py) directly, requires `cosign` on
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

**Full specification:** [`specs/moat-verify.md`](specs/moat-verify.md)

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
  "registry_signing_profile": {
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:owner/repo:ref:refs/heads/main"
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
| `updated_at`                       | REQUIRED                                       | ISO 8601 UTC timestamp of when this manifest was last generated. For display and activity monitoring only — the staleness check uses the client's last-fetch timestamp, not this field.                                         |
| `registry_signing_profile`         | REQUIRED                                       | The registry's CI signing identity. Conforming clients MUST track this per registry; changes on a subsequent fetch require End User re-approval before the manifest is accepted. See [Signature Envelope](#signature-envelope). |
| `registry_signing_profile.issuer`  | REQUIRED                                       | OIDC issuer URL of the registry's CI provider                                                                                                                                                                                   |
| `registry_signing_profile.subject` | REQUIRED                                       | OIDC subject claim as produced by the registry's CI provider                                                                                                                                                                    |
| `content`                          | REQUIRED                                       | Array of per-item entries                                                                                                                                                                                                       |
| `content[].name`                   | REQUIRED                                       | Canonical identifier for the content item                                                                                                                                                                                       |
| `content[].display_name`           | REQUIRED                                       | Human-readable name                                                                                                                                                                                                             |
| `content[].type`                   | REQUIRED                                       | One of: `skill`, `subagent`, `rules`, `command`                                                                                                                                                                                 |
| `content[].content_hash`           | REQUIRED                                       | `<algorithm>:<hex>` — normative identity of the content                                                                                                                                                                         |
| `content[].source_uri`             | REQUIRED                                       | Source repository URI                                                                                                                                                                                                           |
| `content[].attested_at`            | REQUIRED                                       | Registry attestation timestamp (RFC 3339 UTC)                                                                                                                                                                                   |
| `content[].private_repo`           | REQUIRED                                       | `true` if sourced from a private or internal repository                                                                                                                                                                         |
| `content[].rekor_log_index`        | REQUIRED for Signed + Dual-Attested            | Integer index of the registry's Rekor transparency log entry attesting this content item. Absent for Unsigned items — its absence is the Unsigned tier signal.                                                                  |
| `content[].derived_from`           | OPTIONAL                                       | Source URI of the item this was forked or derived from                                                                                                                                                                          |
| `content[].version`                | OPTIONAL                                       | Display label only; `content_hash` is normative identity                                                                                                                                                                        |
| `content[].scan_status`            | OPTIONAL                                       | See [scan_status](#scan_status)                                                                                                                                                                                                 |
| `content[].signing_profile`        | REQUIRED for Dual-Attested                     | See [signing_profile](#signing_profile)                                                                                                                                                                                         |
| `revocations`                      | REQUIRED                                       | Array of revocation entries; empty array if none                                                                                                                                                                                |
| `revocations[].content_hash`       | REQUIRED                                       | Hash of the revoked content item                                                                                                                                                                                                |
| `revocations[].reason`             | REQUIRED                                       | One of: `malicious`, `compromised`, `deprecated`, `policy_violation`                                                                                                                                                            |
| `revocations[].details_url`        | REQUIRED for registry / OPTIONAL for publisher | URL to public revocation details                                                                                                                                                                                                |

**Field notes:**

- `registry_signing_profile` is the registry-level signing identity. It is structurally identical to per-item
  `signing_profile` (issuer + subject) but scoped to the manifest document itself, not to a publisher's content
  attestation. Conforming implementations MUST NOT conflate these two fields.
- `operator` and `name` are display labels. Conforming clients MUST NOT treat changes to these fields as signing
  identity changes and MUST NOT require re-approval when they change.
- `updated_at` uses the registry's clock. The 24-hour staleness threshold runs against the client's own last-fetch
  timestamp. See [Freshness Guarantee and Replay Scope](#freshness-guarantee-and-replay-scope).

### Lockfile

The lockfile is maintained by a conforming client to record all installed content and enforce revocation blocks.

Minimum structure:

```json
{
  "moat_lockfile_version": 1,
  "entries": [
    {
      "name": "string",
      "type": "skill|subagent|rules|command",
      "registry": "https://...",
      "content_hash": "sha256:<hex>",
      "trust_tier": "DUAL-ATTESTED|SIGNED|UNSIGNED",
      "attested_at": "RFC 3339 UTC",
      "pinned_at": "RFC 3339 UTC",
      "attestation_bundle": {},
      "signed_payload": {}
    }
  ],
  "revoked_hashes": []
}
```

| Field                          | Required | Description                                                                                           |
|--------------------------------|----------|-------------------------------------------------------------------------------------------------------|
| `moat_lockfile_version`        | REQUIRED | Schema version; currently `1`                                                                         |
| `entries`                      | REQUIRED | Array of installed content records                                                                    |
| `entries[].name`               | REQUIRED | Content item name as recorded in the registry manifest                                                |
| `entries[].type`               | REQUIRED | Content type; closed set: `skill`, `subagent`, `rules`, `command`                                     |
| `entries[].registry`           | REQUIRED | Registry manifest URL the item was installed from                                                     |
| `entries[].content_hash`       | REQUIRED | `<algorithm>:<hex>` — normative identity of the installed item                                        |
| `entries[].trust_tier`         | REQUIRED | Trust tier at install time: `DUAL-ATTESTED`, `SIGNED`, or `UNSIGNED`                                  |
| `entries[].attested_at`        | REQUIRED | Registry's attestation timestamp (registry clock, not client clock)                                   |
| `entries[].pinned_at`          | REQUIRED | Local install timestamp (client clock; not externally verifiable)                                     |
| `entries[].attestation_bundle` | REQUIRED | Full cosign bundle captured at install time; `null` for `UNSIGNED` content                            |
| `entries[].signed_payload`     | REQUIRED | The original payload passed to `cosign sign-blob` at attestation time; `null` for `UNSIGNED` content |
| `revoked_hashes`               | REQUIRED | Array of hard-blocked content hash strings; empty array if none                                       |

**Field notes:**

- `entries[].attested_at` is the registry's clock, not the client's — do not build freshness logic on it.
- `entries[].trust_tier` records the trust tier as determined at install time. It does not update automatically if the registry changes the tier after installation.
- `entries[].attestation_bundle` is the signature, signing certificate, and Rekor transparency log entry as a single embedded JSON object. Conforming clients MUST populate this field at install time — it is required for offline re-verification.
- `entries[].signed_payload` is the verbatim content passed to `cosign sign-blob` at attestation time, stored exactly as-is. Conforming clients MUST populate this field — `cosign verify-blob --offline` requires the original signed artifact. JSON serialization differences invalidate the signature; storing verbatim is the only safe approach. Before storing, conforming clients MUST confirm that `sha256(signed_payload.encode("utf-8"))` equals the `data.hash.value` field of the Rekor entry at `rekor_log_index`. If this check fails, the entry MUST NOT be written to the lockfile and the install MUST be aborted.
- `entries[].type` is a closed set in the current version. Conforming clients MUST accept entries with unrecognized type values without error — new types will be added in future versions.
- `entries[].registry` MUST be treated as permanently stable once published. A URL change invalidates all lockfile entries referencing it.
- `revoked_hashes` entries MUST NOT be silently removed. Clearing a revoked hash requires deliberate End User action. This prevents the remove-and-reinstall bypass: an attempt to reinstall a revoked hash is blocked by this record.

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
        "subject": "repo:owner/repo:ref:refs/heads/main"
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
| `updated_at`                                   | REQUIRED | ISO 8601 timestamp of the last index update          |
| `registries`                                   | REQUIRED | Array of registry entries                            |
| `registries[].name`                            | REQUIRED | Human-readable registry name                         |
| `registries[].manifest_url`                    | REQUIRED | URL of the registry's signed manifest                |
| `registries[].registry_signing_profile`        | REQUIRED | Expected signing identity for this registry's manifest |
| `registries[].registry_signing_profile.issuer` | REQUIRED | OIDC issuer URL                                      |
| `registries[].registry_signing_profile.subject`| REQUIRED | OIDC subject claim                                   |
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
| `scanned_at`   | REQUIRED when `result` is `clean` or `findings` | ISO 8601 scan timestamp; omitted when `not_scanned`                       |
| `findings_url` | OPTIONAL                                        | URL to a public findings report; only present when `result` is `findings` |

**Field notes:**

- `scanner[].name` MUST be the canonical name for well-known scanners (e.g. `"snyk-mcp-scan"`, `"semgrep"`) to
  enable cross-registry aggregation. Additional fields within scanner entries are permitted. Free-form name strings
  defeat aggregation and do not conform.

### signing_profile

`signing_profile` declares a publisher's expected CI signing identity on Dual-Attested manifest entries. Conforming
clients MUST verify the Rekor certificate's OIDC issuer and subject match this field.

Minimum structure:

```json
{
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:owner/repo:ref:refs/heads/main"
}
```

| Field     | Required | Description                                               |
|-----------|----------|-----------------------------------------------------------|
| `issuer`  | REQUIRED | OIDC issuer URL from the CI provider                      |
| `subject` | REQUIRED | OIDC subject claim as produced by the CI provider's token |

*Informative — known CI provider values:*

| Provider | Issuer | Subject format |
|----------|--------|----------------|
| GitHub Actions | `https://token.actions.githubusercontent.com` | `repo:{owner}/{repo}:ref:refs/heads/{branch}` |
| GitLab CI | `https://gitlab.com` | `project_path:{namespace}/{project}:ref_type:branch:ref:{branch}` |

Other providers with OIDC support: the issuer is the provider's OIDC endpoint URL; the subject format is
provider-defined. Consult the provider's OIDC documentation. Providers are added to this table when their subject
format is verified against a working Sigstore implementation. Forgejo/Codeberg Actions OIDC support is not yet
shipped as of this writing (April 2026). Tracking: Gitea PR
[#36988](https://github.com/go-gitea/gitea/pull/36988) (draft, opened 2026-03-25) and Forgejo PR
[#5344](https://codeberg.org/forgejo/forgejo/pulls/5344) (closed 2025-02-02, no active successor). When either
ships, the issuer will be `<instance-url>/api/actions/oidc` and the subject format will mirror GitHub's. Check
these PRs before updating this table.

---

## OWASP Alignment

MOAT is validated against six OWASP standards: CI/CD Security Top 10 (critical), Top 10 for Agentic Applications 2026
(critical), Top 10:2025 (high), LLM Top 10:2025 (high), Agentic Skills Top 10:2026 (high), and API Security Top 10:2023
(medium).

Core coverage: ASI04, CICD-SEC-9, AST01, AST02, LLM03:2025, A03:2025, and A08:2025.

Remaining gaps — CICD-SEC-8 (federation), API2:2023 (publisher authentication), API7:2023 (SSRF in federation) —
are tracked as deferred features (Issues 10 and 11). These gaps are acknowledged v0.4.0 limitations; they will be
addressed in the version that introduces federation and private registry auth.

**Full alignment map:** [`docs/owasp-alignment.md`](docs/owasp-alignment.md)

