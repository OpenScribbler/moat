# MOAT — Model for Origin Attestation and Trust

A protocol for publishing AI agent content through signed registries — no keys to manage.

| | |
|---|---|
| **Version** | 0.7.1 (Draft) |
| **Status** | Draft — spec complete; reference implementations in progress |
| **Specification** | [`moat-spec.md`](moat-spec.md) |
| **Changelog** | [`CHANGELOG.md`](CHANGELOG.md) |
| **License** | [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |

---

## What MOAT Is

MOAT is a registry distribution protocol for AI agent content — skills, agents, rules, hooks, MCP configurations, and commands. It defines how registries publish, sign, and distribute collections of content, and how conforming clients verify that content before installing it.

MOAT answers three questions at the registry level:

- **Who published this?** — Registry identity, signed and logged to a transparency log
- **Has it been tampered with?** — Content hashing verifies every install against the registry manifest
- **Where did it come from?** — Source URI, lineage, and optional source-repo co-attestation

MOAT does **not** define the internal format of content items. Skills, hooks, rules, and other content types have their own companion specs. MOAT is the distribution layer on top.

---

## Specifications

| Document | Description |
|---|---|
| [`moat-spec.md`](moat-spec.md) | Core specification — registry manifest format, content hashing, signing, lockfile, revocation |
| [`specs/moat-verify.md`](specs/moat-verify.md) | `moat-verify` — reference verification tool specification |
| [`specs/github/publisher-action.md`](specs/github/publisher-action.md) | Publisher Action — GitHub Actions workflow specification for source-repo attestation |
| [`specs/github/registry-action.md`](specs/github/registry-action.md) | Registry Action — GitHub Actions workflow specification for registry manifest publishing |

---

## Reference Implementations

Concrete implementations conformers can use directly or follow as authoritative examples.

| File | Description |
|---|---|
| [`reference/moat_hash.py`](reference/moat_hash.py) | Content hashing — canonical SHA-256 normalization algorithm (Python) |
| [`reference/moat_verify.py`](reference/moat_verify.py) | `moat-verify` — standalone verification tool, online and offline modes (Python) |
| [`reference/moat-publisher.yml`](reference/moat-publisher.yml) | Publisher Action workflow template — drop into `.github/workflows/` |
| [`reference/moat-registry.yml`](reference/moat-registry.yml) | Registry Action workflow template — drop into `.github/workflows/` |

---

## Use Cases

See [`docs/use-cases.md`](docs/use-cases.md) for concrete scenarios showing what each actor does (and doesn't do) in MOAT — from a publisher who shares skills and touches nothing, to a registry operator running a curated index, to a consumer verifying installs.

---

## Guides

Step-by-step documentation for each reference implementation. Guides cover setup, first run, and verification.

| Guide | Description |
|---|---|
| [`docs/guides/publisher.md`](docs/guides/publisher.md) | Publisher Action setup — adds co-signing to a source repository; companion to `reference/moat-publisher.yml` |
| [`docs/guides/registry.md`](docs/guides/registry.md) | Registry Action setup — runs a MOAT registry; companion to `reference/moat-registry.yml` |
| [`docs/guides/self-publishing.md`](docs/guides/self-publishing.md) | Self-publishing — running both actions from one repository |
| [`docs/guides/moat-verify.md`](docs/guides/moat-verify.md) | Testing `moat-verify` — online (`--registry`) and offline (`--lockfile`) modes; companion to `reference/moat_verify.py` |
| [`docs/guides/cosign-offline.md`](docs/guides/cosign-offline.md) | cosign offline verification — empirical test guide for `--lockfile` implementers |

---

## Core Concepts

### Keyless signing

MOAT uses [Sigstore](https://sigstore.dev) keyless signing — there are no private keys to generate, store, or rotate. The signing identity is the GitHub Actions OIDC token for the CI workflow that produced the signature. If GitHub says "this workflow ran in `owner/repo` on branch `main`," that statement *is* the identity, and it's permanently logged to a public transparency ledger. Publishers and registry operators never touch a key.

### Registry Manifest

The core artifact of MOAT. A signed document a registry publishes listing all its content with:
- Content hashes (SHA-256 of the canonical content directory)
- Per-item metadata: source URI, attestation timestamp, scan status, risk tier, lineage
- The registry's signature, logged to [Rekor](https://rekor.sigstore.dev)
- A `revocations` array for content lifecycle management

### Trust Tiers

| Tier | What it means |
|---|---|
| **Dual-Attested** | Registry-signed AND independently attested by the source repo's CI (two independent Rekor entries). Survives registry key compromise. |
| **Signed** | Registry-signed with a Rekor transparency log entry. Tamper-evident. The standard trust tier. |
| **Unsigned** | No MOAT provenance. Works, but labeled clearly. |

Absence of Dual-Attested is **not** a negative signal. Signed is the standard; Dual-Attested is additive confidence.

### Publisher Action

An optional GitHub Actions workflow any source repo adds to produce the `Dual-Attested` tier. On push, it auto-detects AI content, computes content hashes, and signs via Sigstore keyless OIDC — no key management, no MOAT-specific knowledge required.

### Registry Action

A GitHub Actions workflow that turns any repo into a MOAT registry. On a daily schedule (and immediately on config changes), it crawls source repositories, computes content hashes, determines trust tiers, signs the manifest, and commits it — no key management, no MOAT-specific knowledge required. A publisher who runs both the Publisher Action and the Registry Action from the same repository is a self-publishing operator producing valid `Dual-Attested` content.

### Role Combinations

Publishers, registry operators, and conforming clients are roles, not separate organizations. A single team may occupy multiple roles:

- **Publisher + Registry Operator** — Self-publishing: runs both the Publisher Action and Registry Action from one repository. Valid `Dual-Attested` — independence comes from distinct OIDC identities per workflow, not organizational separation.
- **Publisher + Registry Operator + Client** — Closed ecosystem: creates content, distributes it, and ships the install tool. MOAT's verification model still applies end-to-end.

### Revocation

Registries maintain a `revocations` array in the manifest. Four reason codes: `malicious`, `compromised`, `deprecated`, `policy_violation`. Clients block installs for security reasons and warn for informational ones. Cross-registry hash matching means a revocation from one trusted registry surfaces for content installed from any registry.

---

## Repository structure

| Path | Contents |
|---|---|
| `moat-spec.md` | Core specification |
| `specs/` | Sub-specifications: moat-verify, Publisher Action, Registry Action |
| `reference/` | Reference implementations: `moat_hash.py`, `moat_verify.py`, `moat-publisher.yml`, `moat-registry.yml`; test artifacts; `skills/hello-moat` test skill |
| `docs/guides/` | Guides: publisher, registry, self-publishing, moat-verify, cosign-offline |
| `archive/` | Previous spec versions |

---

## Versioning

MOAT uses [Semantic Versioning 2.0.0](https://semver.org/). Versions `0.x.y` carry no backwards-compatibility guarantees — compatibility guarantees begin at `1.0.0`. See [RELEASING.md](RELEASING.md) for the full versioning scheme, spec maturity stages, and release process.

---

## Contributing

Feedback is welcome via [GitHub Issues](https://github.com/OpenScribbler/moat/issues). See [CONTRIBUTING.md](CONTRIBUTING.md) for areas where input is especially valuable.

---

## License

Copyright 2026 Holden Hewett. Licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
