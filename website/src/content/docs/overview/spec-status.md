---
title: Spec status
description: Current status of the MOAT specification and advancement criteria.
---

MOAT is a working draft. The specifications are written and internally consistent, but there are zero known adopters and the reference implementation has not been validated against real production infrastructure.

---

## Current version

**Core spec:** v0.7.0 (Draft)

The core spec covers the registry manifest format, lockfile format, content hashing algorithm, trust tiers, and conforming client behavior requirements.

**Sub-specs (each versioned independently):**

| Spec | Version | Status |
|---|---|---|
| [Core spec](/spec/core) | 0.7.0 | Draft |
| [moat-verify](/spec/moat-verify) | 0.1.0 | Draft |
| [Publisher Action](/spec/publisher-action) | 0.1.0 | Draft |
| [Registry Action](/spec/registry-action) | 0.1.0 | Draft |

All four documents are complete enough to implement against. The version numbers reflect design maturity, not implementation coverage.

---

## What's complete

The following components are fully specified and have reference implementations:

**Core protocol**
- Registry manifest format (`registry.json`) with all required and optional fields defined
- Lockfile format with full schema and conforming client MUST requirements
- Content hashing algorithm — canonical, deterministic, with test vectors ([`reference/moat_hash.py`](https://github.com/OpenScribbler/moat/blob/main/reference/moat_hash.py))
- Trust tier model (`Dual-Attested`, `Signed`, `Unsigned`) with promotion criteria
- Revocation semantics and required client behavior on revocation

**Reference implementations**
- [`moat_verify.py`](https://github.com/OpenScribbler/moat/blob/main/reference/moat_verify.py) — the moat-verify reference implementation
- [`moat_hash.py`](https://github.com/OpenScribbler/moat/blob/main/reference/moat_hash.py) — the content hashing reference implementation
- `reference/moat-publisher.yml` — the Publisher Action workflow
- `reference/moat-registry.yml` — the Registry Action workflow

---

## What's in progress

**Draft advancement criteria**

Two gates must clear before the spec advances to Release Candidate:

1. **Second content hashing implementation** — a port of `moat_hash.py` to any language other than Python that passes all test vectors. The Python reference counts as one; a second independent implementation is required to confirm the algorithm is specified unambiguously.

2. **moat-verify validated against real infrastructure** — `moat_verify.py` must be tested against real Rekor entries and real lockfiles produced by a deployed Registry Action. The reference implementation has not yet been run against production Rekor entries outside of development scenarios.

There are currently no known independent implementations of the core spec.

---

## Deferred work

These are explicit scope decisions with documented rationale — not open questions.

**`hook` and `mcp` content types**
The `hooks/` and `mcp/` canonical directories are reserved but the content types are not yet normative. Hash semantics and discovery behavior for these types need design work.

**Freshness / anti-rollback**
The `expires` field in the manifest is OPTIONAL with a client-enforced 72-hour default (TUF model, added in v0.6.0). Making it REQUIRED is deferred until registries have demonstrated reliable automated manifest rotation — a mandatory expiry with brittle CI creates availability risk for the entire registry catalog.

**GitLab support**
The Publisher Action and moat-verify `--source` flag are GitHub-only. GitLab CI OIDC token format differences require separate design and testing. Both should ship together.

**Forgejo / Codeberg support**
Blocked on upstream — Forgejo/Codeberg Actions OIDC support is not yet shipped as of April 2026. Tracking: Gitea PR [#36988](https://github.com/go-gitea/gitea/pull/36988) and Forgejo PR [#5344](https://codeberg.org/forgejo/forgejo/pulls/5344).

**Federation and private registry auth**
Cross-registry content discovery and private registry authentication are deferred to a later design phase. Both touch the same trust boundary and are likely bundled.

---

## Acknowledged out-of-scope items

These will not be added to MOAT in any version. Listed to prevent re-raising:

- **Publisher identity verification** — MOAT verifies that content came from a specific OIDC identity. It does not verify that identity is the legitimate owner of the source repository. That judgment belongs to the user.
- **Content safety scoring** — MOAT is provenance and integrity, not behavioral analysis.
- **External dependency coverage** — MOAT's guarantee covers the content directory as a unit. MCP servers fetched at runtime or remote URLs referenced in skill files are outside the guarantee.
- **Registry operator trustworthiness** — MOAT provides tools to verify what a registry claims; it does not evaluate whether those claims are worth trusting. Registry selection is a user decision.
