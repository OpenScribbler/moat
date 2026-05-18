# MOAT — Ubiquitous Language

_Canonical domain vocabulary for this repo. When a term has a bold canonical name, use it verbatim in code, docs, tests, commit messages, and PR descriptions. If you see an "alias to avoid," do not use it._

_This lexicon is biased toward terms the upcoming `npm-distribution-spec` work will touch — the boundary between MOAT's existing GitHub-Actions-based world and the npm world is the most likely place for synonym drift. When npm has a near-synonym for a MOAT term (`package` vs `content item`, `tarball` vs `content directory`, `registry` in the npm sense vs `MOAT registry`), pick the MOAT term unless the context is explicitly the npm ecosystem._

## Protocol & Core Artifacts

| Term | Definition | Aliases to avoid |
|---|---|---|
| **MOAT** | Model for Origin Attestation and Trust — the registry distribution protocol specified by `moat-spec.md`. | "MOAT spec" (when meaning the protocol), "the framework" |
| **Registry Manifest** | The signed JSON document a registry publishes listing every content item it attests. The core artifact of MOAT. Served at `manifest_uri`. | "registry file", "registry manifest file", "the registry JSON", "the index" (see ambiguity) |
| **Registry Index** | A separately-signed JSON document that lists known registries and their `manifest_url`s, used by clients for discovery. NOT the same as a registry manifest. | "the index" (without qualification), "registry directory", "directory of registries" |
| **Lockfile** | The local file a conforming client maintains recording installed content hashes, attestation bundles, signed payloads, registry fetch timestamps, and revoked hashes. The trust anchor for offline verification. On the npm channel the MOAT Lockfile is stored at `.moat/npm-lockfile.json` (project-scoped, source-tree-checked-in); it is distinct from npm's own `package-lock.json`, which is the resolver-cache artifact that records the dependency-graph closure and does not carry MOAT attestations. | "lock", "install snapshot file" |
| **Content Hash** | The canonical SHA-256 (default algorithm) of a content item's directory, computed by the algorithm in `reference/moat_hash.py`. Format: `<algorithm>:<hex>`. The normative identity of a content item. | "directory hash", "package hash", "skill hash", "fingerprint" |
| **Attestation Payload** | The exact two-key JSON document `{"_version":1,"content_hash":"sha256:..."}` that is signed by both the Publisher Action and the Registry Action. Byte-identical for a given content hash regardless of who signs. | "signed blob", "payload JSON" |
| **Cosign Bundle** | The Sigstore protobuf bundle v0.3 produced by `cosign sign-blob --new-bundle-format`, containing the signature, signing certificate, and Rekor transparency log entry. Stored verbatim in the lockfile as `attestation_bundle`. | "sigstore bundle" (loose), "signature blob", "rekor bundle", "cosign blob" |
| **Attestation** | A signed claim that a specific content hash existed at a specific point in time, recorded as a per-item Rekor entry. A Dual-Attested item has two attestations (publisher and registry); a Signed item has one (registry only). | "signature" (when meaning the protocol-level claim — see Flagged ambiguities) |
| **Provenance** | Informal umbrella covering MOAT's job: "where did this come from and has it been tampered with?" Used in marketing/overview prose. NOT a normative protocol term — when speaking normatively, use **Attestation** plus **Source URI**. | (none — but do not use "provenance" inside the spec body where "attestation" or "signing identity" is meant) |
| **Trust Tier** | One of `Dual-Attested`, `Signed`, or `Unsigned` — the per-item trust label the registry assigns and a conforming client surfaces to the End User. | "trust level", "tier" (without "trust"), "verification level", "assurance level" |
| **Dual-Attested** | A content item with both a registry Rekor entry AND a verified publisher Rekor entry for the same `content_hash`. Spelled with hyphen and capitalized in user-facing prose. | "double-signed", "dual-signed", "co-attested", "twice-attested" |
| **Signed** | A content item with a registry Rekor entry only. The standard, default tier. | "registry-signed" (in body text where the tier name is meant) |
| **Unsigned** | A content item with no MOAT Rekor entry. Works, but labeled clearly. | "untrusted", "unattested", "no-tier" |
| **Revocation** | An entry in the manifest's `revocations` array that hard-blocks (registry-source) or warns about (publisher-source) a specific content hash. | "recall", "block", "deny entry" |
| **Tombstone** | A permanently-blocked content hash recorded in `revocation-tombstones.json` on the `moat-registry` branch. A hash that was once revoked and pruned MUST NOT reappear in `content`. | "blacklist entry", "permaban" |

## Actors & Roles

| Term | Definition | Aliases to avoid |
|---|---|---|
| **End User** | The human (or admin acting for a human) who chooses which registries to trust and approves installs. Capitalized as a two-word proper noun. | "user" (alone, when actor is meant), "consumer" (in normative spec; OK in marketing), "installer" (the person) |
| **Publisher** | The actor who creates content and keeps it in a source repository. Optionally adopts the Publisher Action. | "creator", "author" (in normative spec; OK informally), "source repo owner" |
| **Registry Operator** | The actor who runs a registry — operates a `.moat/registry.yml` config and the Registry Action workflow. | "registry maintainer", "registry admin", "curator" (loose) |
| **Conforming Client** | An install/management tool that implements MOAT's normative client behavior (fetch manifest, verify signatures, maintain lockfile, enforce revocations). NOT an AI agent runtime. | "MOAT client", "install tool" (when normative behavior is meant), "verifier" (use **moat-verify** for the standalone tool), "package manager" (loose) |
| **AI Agent Runtime** | A system like Claude Code, Gemini, Cursor, or Windsurf that loads or executes already-installed content. Outside the MOAT protocol boundary. | "runtime" (alone — ambiguous with cosign / OS runtime), "agent host", "AI tool" |
| **Index Operator** | The actor who runs a Registry Index — distinct role from a Registry Operator. | "discovery operator", "registry registry" |
| **Self-Publisher** | A single actor occupying both Publisher and Registry Operator roles, running both Actions from one repository. The manifest's `self_published: true` discloses this. | "self-hosted publisher", "solo registry" |

## Workflows & Actions (the GitHub-Actions-specific instances)

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Publisher Action** | The GitHub Actions workflow specified in `specs/github/publisher-action.md` and templated by `reference/moat-publisher.yml`. The mechanism, not a person. Capitalized; two words. | "publisher workflow" (when the spec'd Action is meant), "publish action", "the publisher" (the actor is the **Publisher**) |
| **Registry Action** | The GitHub Actions workflow specified in `specs/github/registry-action.md` and templated by `reference/moat-registry.yml`. The mechanism, not a person. | "registry workflow" (when the spec'd Action is meant), "the registry" (the actor is the **Registry Operator**; the artifact is the **Registry Manifest**) |
| **moat-attestation branch** | The dedicated git branch (`moat-attestation`) where the Publisher Action writes `moat-attestation.json`. Never merged into the source branch. | "attestation branch" (loose; ambiguous with the file), "publisher branch" |
| **moat-registry branch** | The dedicated git branch (`moat-registry`) where the Registry Action writes `registry.json` and `registry.json.sigstore`. Never merged into the source branch. | "registry branch" (loose), "manifest branch" |
| **moat-attestation.json** | The file the Publisher Action produces on the `moat-attestation` branch listing per-item Rekor references for the source repo. | "publisher manifest" (collides with **Registry Manifest**), "attestation file" |
| **`.moat/publisher.yml`** | The tier-2 publisher discovery config at the source repo root. Reserved location. | "moat.yml" (legacy v0.7.0− location, do not use) |
| **`.moat/registry.yml`** | The Registry Operator's config at the registry repo root listing sources and registry metadata. | "registry.yml" (without `.moat/` prefix when location matters), "registry config file" |
| **moat-verify** | The standalone verification tool (specified in `specs/moat-verify.md`, implemented in `reference/moat_verify.py`) that audits MOAT-attested content without installing it. NOT a conforming client. | "the verifier", "verify tool", "moat-cli" |
| **Tier-1 / Tier-2 Discovery** | The two-tier mechanism for finding content items: Tier-1 = canonical category directories; Tier-2 = `.moat/publisher.yml` overrides. | "manifest discovery", "auto-discovery" (loose) |

## Content & Layout

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Content Item** | One unit of attestable content — a single subdirectory under a category directory. The unit the content hash covers. | "package", "module", "artifact" (loose; all three are npm/packaging-domain terms that risk drift) |
| **Content Directory** | The directory on disk that contains one content item — the input to the content hashing algorithm. In the npm Distribution Channel, the field `tarballContentRoot` (in `package.json`) is one realization of this concept inside the unpacked tarball; the lexicon term remains the source of truth. `tarballContentRoot` is REQUIRED for cooperative Publishers; the tarball-root default (unpacked tarball root with the root `package.json` excluded) applies only to Registry-backfilled items. | "package directory", "package root", "content_root", "skill folder", "item directory" |
| **Content Type** | One of the four normative types: `skill`, `agent`, `rules`, `command`. (`hook` and `mcp` are deferred — directories reserved, types not yet normative.) | "kind", "category" (collides with **Category Directory**), "content kind" |
| **Category Directory** | A canonical top-level directory in the source repo holding content of one type: `skills/`, `agents/`, `rules/`, `commands/`. | "type directory", "content folder", "section directory" |
| **Source Repository** | The git repository where a publisher keeps content, identified in the manifest by `source_uri`. The protocol's unit of "where it came from." | "upstream repo", "publisher repo" (informal OK; use **Source Repository** in normative text), "origin" |
| **Source URI** | The canonical URL of the **source repository** (a git URL) for a content item, recorded as `content[].source_uri` in the manifest. Names *where the content was authored* — NOT where its bytes are fetched on a distribution channel. Distinct from **Distribution URI**: do not conflate. | "source URL" (use URI), "origin URL", "repo link", "tarball URL" (that is **Distribution URI**) |
| **Distribution URI** | The canonical, dereferenceable URL of a content item's bytes on a specific **distribution channel** — e.g. the npm tarball URL `https://registry.npmjs.org/<package>/-/<package>-<version>.tgz` on the npm channel, recorded as `moat.distribution_uri` in `package.json`. Names *where this version's bytes can be fetched on this channel* — NOT where the content was authored. Distinct from **Source URI**: do not conflate. | "tarball URL" (when meaning the protocol field), "fetch URL" (loose), "channel URL", "source_uri" (that is the authoring URL) |
| **Lineage** / **derived_from** | The optional `derived_from` field that records that a content item was forked or adapted from another source URI. | "parent", "ancestor", "fork-of" |

## Trust, Verification & Identity

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Signing Identity** | An OIDC issuer + subject pair (and on GitHub, immutable repo and owner numeric IDs) that identifies who produced a signature. Captured in the Fulcio certificate at signing time. | "signer", "publisher key" (no keys exist — keyless signing), "identity key" |
| **registry_signing_profile** | The manifest field declaring the registry's expected CI signing identity. Pinned per registry by conforming clients. | "registry identity" (loose), "registry signer" |
| **signing_profile** (per-item) | The manifest field on Dual-Attested items declaring the publisher's expected CI signing identity. Structurally identical to `registry_signing_profile` but scoped to publisher attestation. | "publisher profile", "publisher identity" (loose) |
| **Keyless Signing** | The Sigstore mechanism MOAT uses: signatures bound to an OIDC identity rather than a long-lived private key. No keys are generated, stored, or rotated. | "tokenless signing", "Sigstore signing" (use **Keyless Signing** when the property — no private keys — is the point) |
| **Rekor Entry** | A specific transparency-log record for one signed payload. The per-item Rekor entry is the authoritative trust anchor for each content item. | "transparency entry", "log entry" (loose), "rekord" |
| **Trusted Root** | The Sigstore Fulcio CA bundle, Rekor public keys, and timestamp authorities a conforming client uses to verify Sigstore signatures. Has bundled, per-registry, and invocation override modes. | "Sigstore root", "trust root", "CA bundle" (loose) |
| **TOFU (Trust-On-First-Use)** | The first-fetch trust bootstrap for manually-added registries: the End User's explicit add action accepts the manifest's declared `registry_signing_profile`. | "first-trust", "initial trust", "blind trust" |
| **Dual Attestation** | The property a content item has when both publisher and registry have signed the same canonical attestation payload, producing two independent Rekor entries. The Dual-Attested tier is the manifestation of this property. | "co-signing" (loose), "double attestation", "two-party signing" |
| **Hash Mismatch** | The condition where the registry's computed `content_hash` differs from the hash recorded in `moat-attestation.json`. Forces a downgrade to Signed and sets `attestation_hash_mismatch: true`. | "checksum mismatch", "hash failure" |

## Distribution Channels (where npm will live as a near-synonym landmine)

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Distribution Channel** | The medium through which content reaches an End User. In v0.7.x, the only normative channel is "registry manifest fetched over HTTPS, Rekor verified per-item." Future sub-specs MAY define additional channels (e.g., npm). | "delivery method", "transport" (loose) |
| **Registry** (MOAT) | A MOAT registry — the trust unit defined in `moat-spec.md`: a publisher of a signed registry manifest. | "MOAT registry" (redundant inside this repo — just **Registry**), "moat hub" |
| **npm Registry** | The npm-ecosystem package registry (e.g., registry.npmjs.org) — a third-party distribution surface MOAT may layer on top of. ALWAYS qualify with "npm" — the unqualified word "registry" inside this repo means a MOAT registry. | "registry" (unqualified, when npm is meant), "package registry" (ambiguous — could mean either) |
| **npm Package** | A unit of distribution in the npm ecosystem, packaged as a tarball with a `package.json`. Distinct from a MOAT **Content Item**, even when one npm package contains one content item. | "package" (unqualified — collides with content item in MOAT prose) |
| **Distribution Tarball** | (Reserved for npm sub-spec.) The npm `.tgz` artifact carrying one or more content items plus npm metadata. Use this term, not "package" alone, when the artifact is the topic. | "tgz", "package archive" (loose) |
| **Source Channel** | The channel by which content reaches a registry — currently always "git repository at `source_uri`." Distinct from the **Distribution Channel** by which content reaches an End User. | "ingestion channel", "input channel" |

## Reference Implementation & Conformance

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Reference Implementation** | A concrete implementation in `reference/` that conformers may use directly or follow as an authoritative example. Some are normative (`generate_test_vectors.py`); most are informative. | "sample code", "example implementation" |
| **Test Vector** | One of the canonical input/output pairs produced by `reference/generate_test_vectors.py`. Test vectors are the **normative** specification of correct hashing output — when implementation and vector disagree, the implementation is wrong. | "test case" (loose; test vectors are the normative artifact), "fixture" |
| **Conforming Implementation** | An implementation that produces output matching all test vectors (for hashing) and meets all MUST-level requirements (for clients, registries, verifiers). | "compliant implementation", "MOAT-compatible" |
| **Schema Version** | An integer version on the manifest, lockfile, registry index, or attestation payload that gates format evolution. Distinct from MOAT's overall spec semver version. | "version" (alone — collides with `content[].version` display label and the spec version), "format version" |
| **Spec Version** | The semver number of `moat-spec.md` itself (currently 0.7.1 Draft). Distinct from any `schema_version` field. | "MOAT version" (loose), "protocol version" |

## Relationships

- A **Publisher** publishes one or more **Content Items** in a **Source Repository**.
- A **Registry Operator** runs zero or more **Registry Actions** that produce exactly one **Registry Manifest** per registry.
- A **Registry Manifest** indexes zero or more **Content Items** (one entry per `(name, type)` pair) and carries zero or more **Revocations**.
- A **Content Item** has exactly one **Content Hash** and exactly one **Trust Tier** at a given point in time per registry.
- A **Dual-Attested** item has exactly two **Rekor Entries** for the same **Attestation Payload** under two distinct **Signing Identities**.
- A **Conforming Client** maintains exactly one **Lockfile** and trusts zero or more **Registries**.
- A **Registry Index** lists zero or more **Registries**; an **End User** MAY discover registries through it but MUST still take an explicit add action per registry.
- An **End User** trusts **Registries** (not publishers, not content items, not the AI agent runtime).

## Flagged ambiguities

The following are real conflicts found in this codebase. The npm-distribution sub-spec work is the natural moment to lock these down before npm vocabulary makes them worse.

- **"signature" vs "attestation" vs "provenance".** Used loosely as near-synonyms in `README.md`, `CLAUDE.md`, `ROADMAP.md`, and overview docs. They are not synonyms:
  - **Signature** = the cryptographic output of `cosign sign-blob` (a field inside the cosign bundle).
  - **Attestation** = the protocol-level claim that a `content_hash` existed at a logged time, manifested as a Rekor entry over the canonical Attestation Payload.
  - **Provenance** = an informal umbrella for "where did it come from + integrity," used in marketing prose.
  Recommend: in normative spec text use **Attestation** for the claim and **Signature** only when the bytes coming out of `cosign` are literally the topic. Reserve **Provenance** for `README.md`, the website, and `ROADMAP.md`'s "what MOAT is for" framing.

- **"registry" — MOAT registry vs npm registry vs registry index.** The unqualified word "registry" is overloaded three ways once npm enters scope:
  1. A MOAT **Registry** (the actor's output: a signed registry manifest).
  2. The **Registry Index** (a directory of registries — already aliased as "the index" in `moat-spec.md` §Discovery and §First-install trust boundary).
  3. The npm **package registry** (registry.npmjs.org and friends).
  Recommend: inside this repo, "registry" without qualification ALWAYS means a MOAT registry. Use **Registry Index** verbatim for #2, and **npm Registry** verbatim for #3 — never abbreviate either to just "registry" once written. Add a glossary note to the npm sub-spec's Terminology section reinforcing this.

- **"content directory" vs "package directory" vs "content_root".** `moat-spec.md` line 174 says "the package or content directory is the trust unit" — the only place "package" appears in this sense, and it leaks an npm/Cargo lens into a MOAT-native concept. The rest of the spec consistently uses "content directory." `content_root` does not appear in the codebase but is the kind of synonym npm work might invent. Recommend: standardize on **Content Directory** in the body and edit `moat-spec.md` line 174 to read "the content directory is the trust unit." If the npm sub-spec needs a term for "the directory inside the tarball that maps to a content item," use **Content Directory** with an "inside the npm package" qualifier — do not coin `content_root` or `package_root`.

- **"Publisher" vs "Publisher Action" vs "publisher workflow".** The actor and the workflow share a name root. `CLAUDE.md`, `docs/use-cases.md`, and the spec are mostly disciplined ("Publisher" capitalized = actor; "Publisher Action" capitalized two-word = workflow), but informal docs occasionally write "the publisher signs the content" when they mean "the Publisher Action signs on the publisher's behalf." Recommend: when the workflow is the subject of the sentence, write **Publisher Action** in full every time. When the human is the subject, write **Publisher**. Never write "publisher action" lowercase in normative text.

- **"Registry" vs "Registry Action" vs "Registry Operator".** Same shape as above, with the additional twist that "the registry" in the spec usually means the manifest-publishing system (an abstraction over the Action + the operator + the manifest). Recommend: in normative spec text prefer the precise term — **Registry Manifest** when speaking about the artifact, **Registry Action** when speaking about the workflow, **Registry Operator** when speaking about the human/org. Reserve unqualified "the registry" for prose where the abstraction is genuinely the right level (e.g., "the registry is the trust unit").

- **"conforming client" vs "install tool" vs "package manager" vs "verifier".** `CLAUDE.md` and `moat-spec.md` §Actors are explicit: a **Conforming Client** is the install-and-management layer; **moat-verify** is a standalone tool, not a client; an AI Agent Runtime is a downstream consumer, not a client. But `README.md` line 17 and `docs/guides/*` slip between "install tool" and "conforming client" freely. Recommend: in normative text always write **Conforming Client**. In friendly docs (`README.md`, guides) "install tool" is acceptable as a gloss; never call moat-verify a "client" or a "verifier client."

- **"Trust Tier" tier names — capitalization and hyphenation.** Examples in the codebase: `Dual-Attested`, `DUAL-ATTESTED` (lockfile field value), `dual-attested` (some prose). The lockfile schema uses ALL-CAPS (`"trust_tier": "DUAL-ATTESTED|SIGNED|UNSIGNED"`); the manifest and prose use Title-Case-Hyphenated. Recommend: lock **Dual-Attested**, **Signed**, **Unsigned** as the prose form, and keep the ALL-CAPS form ONLY as the literal value of `entries[].trust_tier` in the lockfile schema. Document this explicitly somewhere — implementers will guess wrong otherwise.

- **"index" — Registry Index vs `rekor_log_index` vs `content` array index.** Three distinct uses of the word "index" appear in `moat-spec.md`. Recommend: use **Registry Index** in full for the discovery document; keep `rekor_log_index` as the field name (it's a Rekor protocol term, not invented here); never use "index" alone to mean a position in the `content` array — write "manifest entry" instead.
