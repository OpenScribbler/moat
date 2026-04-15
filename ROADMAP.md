# MOAT Roadmap

This document tracks planned and deferred work. Completed work is in [CHANGELOG.md](CHANGELOG.md). The current spec version is in [moat-spec.md](moat-spec.md).

---

## Draft advancement criteria

The spec is at Draft status. Two gates must clear before it advances to Release Candidate. For the full versioning scheme and release process, see [RELEASING.md](RELEASING.md).

1. **Second content hashing implementation** — a port of [`reference/moat_hash.py`](reference/moat_hash.py) to any language other than Python that passes all test vectors from [`reference/generate_test_vectors.py`](reference/generate_test_vectors.py). The Python reference counts as one; a second independent implementation in a different language is required.

2. **`moat-verify` validated against real infrastructure** — the reference implementation ([`reference/moat_verify.py`](reference/moat_verify.py)) must be validated against real Rekor entries and real lockfiles before the spec advances.

---

## Deferred items

Explicitly deferred with documented rationale. These are scope decisions, not open questions.

### Content types

**`hook` and `mcp` content types**
Directories (`hooks/`, `mcp/`) are reserved in the canonical layout. The content types are not yet normative — hash semantics and discovery behavior for hooks and MCP configs need design work before they can be specified.

### Freshness and anti-rollback

**Making `expires_at` REQUIRED**
The `expires_at` field is currently OPTIONAL — registries that want strict freshness enforcement may opt in. Making it REQUIRED for all conforming registries is deferred: the field creates a hard liveness dependency on the registry's CI pipeline, and a CI outage would take the registry's entire catalog offline. The prerequisite is that registries have demonstrated reliable, automated manifest rotation before this dependency is mandated.

*Influenced by:* TUF's freshness semantics. See the Influences section in [moat-spec.md](moat-spec.md).

### Non-interactive trust onboarding

**CI/CD pre-approval mechanism**
Conforming clients MUST exit non-zero on TOFU acceptance, `registry_signing_profile` changes, and other trust decisions that require human judgment. This leaves CI/CD environments with no path to add new registries or accept routine profile rotations without interactive prompts. A pre-approval mechanism is needed: a committed file (e.g., `.moat/preapproved-registries.json`) mapping registry URLs to expected signing profiles, consulted by the client before exiting non-zero. The git history of the file serves as the audit record that interactive acceptance would otherwise provide.

Scope to lock before this can be specified:

- **File format and location** — fixed path vs. client-configurable.
- **Profile pinning granularity** — full `registry_signing_profile` object (strict; any rotation breaks CI until re-approved) vs. OIDC issuer/subject only (looser; wider trust surface).
- **Rotation handling** — single pinned profile (TOFU-equivalent semantics) vs. ordered list of N acceptable profiles (allows registry rotation without downstream CI edits at the cost of added complexity).
- **Expiry** — whether pre-approval entries carry an `expires_at` so abandoned pipelines don't trust indefinitely; mirrors the manifest staleness model.
- **Failure-mode signals** — machine-distinguishable signals for registry-not-listed, profile mismatch against listed entry, and expired entry; extends the existing non-interactive failure table.
- **`moat-verify` integration** — whether the standalone verify tool gains a `--preapproval <file>` flag for pipeline use or remains human-driven.

**Explicit non-override (normative, not a design knob):** revocation and manifest staleness MUST NOT be pre-approvable. Tolerating staleness in CI defeats the staleness guarantee; revocation is a hard block by design.

Shipping this requires a normative sub-spec, a reference implementation (per the spec rule that non-obvious requirements carry one), test vectors for each failure mode, and adversarial design review — with particular weight on whether ops teams will actually maintain the pre-approval file in practice.

*Influenced by:* TUF role separation and rotation ceremonies for the pinning and rotation decisions; the existing staleness model for expiry.

### Platform support

**GitLab support in Publisher Action and moat-verify**
The Publisher Action spec is GitHub Actions only. GitLab CI support requires OIDC token format differences, certificate subject format verification, and testing against a real GitLab CI environment. `moat-verify`'s `--source` flag has the same dependency — both should ship together.

**Forgejo/Codeberg OIDC**
Blocked on upstream — Forgejo/Codeberg Actions OIDC support is not yet shipped as of April 2026. Once it ships, the signing profiles informative table in moat-spec.md needs a verified entry. Tracking: Gitea PR [#36988](https://github.com/go-gitea/gitea/pull/36988) and Forgejo PR [#5344](https://codeberg.org/forgejo/forgejo/pulls/5344).

---

## Longer-term

Larger features with broader design implications. Not scoped to a specific version.

### Federation

**Cross-registry content discovery and trust propagation**
OWASP gap (Issues 10 and 11). Covers CICD-SEC-8 (federation security), API2:2023 (publisher authentication across registries), and API7:2023 (SSRF risk in federation fetch paths). This is the largest unresolved design area and will require its own dedicated design phase.

### Private registry authentication

**Private registry auth and access control**
Deferred alongside federation (Issues 10 and 11). Likely bundled with the federation milestone since both touch the same trust boundary.

---

## Infrastructure

**moatspec.org website**
Astro + Starlight. Four phases: project setup, content migration, blog, deploy. Hosting TBD (Vercel, Netlify, or GitHub Pages). Domain registration pending.

---

## Acknowledged limitations

Explicitly out of scope for MOAT. Listed here to prevent them from being re-raised as gaps.

- **Publisher identity verification** — MOAT verifies that content came from a specific OIDC identity and hasn't been tampered with. It does not verify that the OIDC identity is the legitimate owner of the source repository. That judgment belongs to the End User.
- **Content safety** — MOAT is provenance and integrity, not a safety scoring system. Whether content is safe to execute is out of scope.
- **External dependencies** — MOAT's trust guarantee covers the content directory as a unit. Dependencies outside that directory (e.g., MCP servers fetched at runtime, remote URLs in skill files) are outside the guarantee.
- **Registry operator trustworthiness** — MOAT provides the tools to verify what a registry claims; it does not evaluate whether those claims are worth trusting. Registry selection is a user decision.
