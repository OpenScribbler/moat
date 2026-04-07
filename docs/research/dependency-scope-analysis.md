# Dependency Scope Analysis

**Date:** 2026-04-07
**Status:** Resolved
**Source:** Coworker feedback review + panel analysis

---

## The Feedback

> "You sort of touch on it by saying 'the package is the trust unit', but this leaves me wondering — what if there are other files that affect the package?"

The concern: if a skill depends on another skill, a hook, or a bundled MCP server — content that exists outside the skill's own directory — does MOAT's trust guarantee cover that?

---

## Cases Analyzed

### Same-repo intra-content dependencies

**Skill A requires Skill B (same repo):**
Both are hashed separately by the registry. Trust is not at issue — both carry the same registry attestation from the same source. The dependency relationship doesn't create a trust gap.

**Skill C requires Hook A and Hook B (same repo):**
Same pattern. Trust is covered. What isn't covered is installation completeness and effective risk tier.

**Bundled MCP server (same repo, different content type):**
An MCP server is qualitatively different — likely `risk_tier: L3` by definition (network access, possible shell access). Installing a skill that quietly enables an L3 MCP server is a significant trust escalation that must be surfaced, not silently included.

### Out-of-repo dependencies

Files outside the content directory (shared configs, build inputs, cross-repo skills) are explicitly out of MOAT's scope. The registry hashes the content directory as a unit. What's outside is outside.

---

## The Real Problem: Risk Tier, Not Trust

Intra-repo dependencies are not a **trust** problem — they're a **risk communication** problem.

**Scenario:** Skill A is `risk_tier: L0` (read-only). Hook B is `risk_tier: L3` (shell execution). Skill A at runtime calls Hook B. User installs Skill A, sees "L0," and believes they're installing a safe tool. But they have L3 behavior on their system.

The spec already says "effective install-time tier = `max(tiers of dependencies)`" — but that math only works if the client knows the dependency exists. Without a dependency graph, the client can't compute it.

---

## Options Considered

### Option A: Add `requires` field to manifest
Registry auto-detects dependencies via static analysis, embeds them in the manifest.

**Rejected because:**
- Dependency detection accuracy is variable — missed dependencies give false L0 signals, which is worse than no signal
- Wrong answers baked into a signed manifest undermine the trust artifact
- MOAT is a trust protocol, not a package manager. Adding `requires` blurs this line (per Spec Purist)
- "The dependency graph is an implementation detail of how you compute risk_tier — not a protocol-level artifact" (SPu)

### Option B: Author-declared `requires` in companion spec
SKILL.md frontmatter (companion spec concern) carries `requires` declarations. Registry reads them as input when computing `risk_tier`.

**Rejected (standalone) because:**
- Historical data: 2,895 missing, 2,142 unparseable frontmatter entries out of 180,605 skills
- Authors won't declare dependencies they don't have to
- Doesn't solve the problem without tooling enforcement

### Option C (Resolved): Client-side install transparency
The client, not the manifest, is responsible for surfacing risk at install time. If a single install operation touches multiple content items, the client MUST surface all of their risk tiers before the user confirms.

---

## Resolution

**`requires` stays out of the MOAT manifest.**

The actual safety mechanism is a client conformance requirement:

> Conforming clients MUST surface the `risk_tier` of every content item being installed in a single operation, so a user installing Skill A that also pulls in Hook B sees both tiers before confirming.

This means:
- Authors do nothing extra
- Registries don't need accurate dependency detection
- The protocol stays a trust protocol, not a package manager
- The L0-that-calls-L3 risk is surfaced at install time through client transparency, not manifest metadata

**Scope boundary language (to be added to spec):**

Files outside the content directory — shared dependencies, auxiliary configs, build inputs, cross-repo content — are not covered by the content hash. MOAT's trust guarantee covers the content directory as a unit. Content with external dependencies should declare them via companion specs (e.g., SKILL.md `requires` field); clients computing install-time risk should surface each dependency's own MOAT-attested `risk_tier`.

---

## Panel Notes

- **Spec Purist:** "`requires` in the manifest is a category error. The dependency graph is an implementation detail of how the registry computed `risk_tier`."
- **Registry Operator:** "I can detect explicit declarations. I cannot detect runtime orchestration dependencies (dynamic calls). `indeterminate` is my escape valve for things I can't analyze."
- **Remy:** "The failure mode you're trying to prevent is 'user installs L0, gets L3 behavior without consent.' Fix that with install flow transparency, not a dependency graph in the manifest."
