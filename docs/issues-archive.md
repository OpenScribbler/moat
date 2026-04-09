# MOAT Issue Archive

All 16 open issues tracked against v0.4.0. All are resolved or deferred. This file is the authoritative decision log — the rationale here is the claim of record for reviewers and future contributors.

**Reference implementations referenced throughout:**
- **Content hashing:** [`moat_hash.py`](../moat_hash.py) — normative Python reference implementation
- **Publisher Action:** [`specs/publisher-action.md`](../specs/publisher-action.md) — GitHub Actions workflow for source-side co-signing
- **moat-verify:** [`specs/moat-verify.md`](../specs/moat-verify.md) — standalone verification tool

---

## Issue 4: Registry manifest size and pagination

**Status:** Resolved

No pagination in v1. Registries serving large catalogs should split into sub-registries. Pagination support is a MAY for future spec versions and client implementations. This is consistent with the static-file registry model and avoids protocol complexity in v1.

---

## Issue 9: Registry index governance

**Status:** Resolved

The spec defines the registry index format (signed JSON, stable URL), requires index operators to sign the index via Rekor and publish a public governance document covering inclusion criteria, removal policy, incident response, dispute resolution, and signing key management. Governance document content is explicitly outside spec scope — that belongs to the index operator.

The de facto trust root concern is addressed at the protocol layer: the index shapes the discovery menu but cannot bypass the per-registry explicit End User trust action that conforming clients already require. Client requirements: MUST surface which index(es) are in use, MUST support user-configurable sources, MUST allow removal of any default, MUST allow direct registry URL entry without using an index.

**Rationale for governance document requirement:** This follows the TUF model — the spec defines the mechanism (signing, required fields, stable URL) without dictating policy content. Requiring the document to exist and cover named topics sets a verifiable floor without over-specifying what a community-operated index must decide internally.

---

## Issue 10: Publisher authentication model

**Status:** Deferred to a future version

Publisher identity for the Dual-Attested tier is already handled by OIDC signing via Sigstore — the CI identity IS the publisher identity. Transport-layer auth for private registries is out of scope for v0.4.0; registry operators may use any mechanism they choose. Private content isolation — preventing accidental publishing of private repo content to public registries — is a conforming client responsibility addressed at the tooling layer (see [Publisher Action spec](../specs/publisher-action.md), Private Repository Guard section).

---

## Issue 11: Federation security

**Status:** Deferred to a future version

Federation is not defined in MOAT v0.4.0. SSRF mitigation, trust laundering prevention, upstream-input sanitization, response size limits, and timeout requirements will be specified in the version that introduces federation.

---

## Issue 12: Algorithm deprecation guidance

**Status:** Resolved

See Algorithm requirements in the normative core. `sha256` is required; `sha512` is optional; `sha1` and `md5` are forbidden (hard failure). Clients refuse to verify unrecognized algorithms rather than silently passing.

**Reference implementation:** [`moat_hash.py`](../moat_hash.py)

---

## Issue 13: Offline verification

**Status:** Resolved

See Trust Anchor Model (offline lockfile verification) and the conforming client manifest staleness requirement (24-hour default). The lockfile is the offline trust anchor; `attestation_bundle` provides complete proof retention without network calls.

**Reference implementation:** [`specs/moat-verify.md`](../specs/moat-verify.md)

---

## Issue 14: Cross-registry blocklist federation

**Status:** Resolved (closed by Issue 21)

Cross-registry revocation sharing requires either a shared authority no one has established or trust delegation users did not grant. Both undermine the per-registry trust model. Out of scope for v1. See Issue 21.

---

## Issue 15: Trust anchor ambiguity

**Status:** Resolved

Per-item Rekor transparency log entry is the authoritative trust anchor for each content item. The registry manifest signature establishes integrity of the manifest index. Both are required — they serve different roles and neither can substitute for the other.

---

## Issue 16: Anti-rollback / anti-freeze model

**Status:** Resolved

See Freshness Guarantee and Replay Scope in the Trust Model. The 24-hour staleness threshold is the v1 freshness guarantee. Manifest replay within that window is an explicitly out-of-scope threat. Clients SHOULD NOT configure the threshold above 48 hours. Explicit `expires_at` expiry is deferred to a future version pending registry infrastructure maturity — mandating hard expiry creates a liveness dependency on registry CI that is inappropriate for the hobbyist and small-team operators MOAT v1 targets.

---

## Issue 17: "No central infrastructure" language

**Status:** Resolved

Core Design Principles already reads: "No central infrastructure required to operate a registry. A GitHub repo with a GitHub Action is enough to run one. Verification of Signed content depends on Rekor availability." The distinction is explicit.

---

## Issue 18: Publisher Action source repo mutation

**Status:** Resolved

The Publisher Action writes `moat-attestation.json` to a dedicated `moat-attestation` branch instead of committing back to the source branch. This eliminates main branch protection friction and commit churn on the source branch. Pushing to a separate branch is structurally loop-safe — workflow triggers scoped to `main` do not fire on `moat-attestation` branch pushes. Registry discovery URL: `https://raw.githubusercontent.com/{owner}/{repo}/moat-attestation/moat-attestation.json`.

**Claim:** The commit-back model is adoption-blocking for enterprise publishers whose repos enforce branch protection on `main`. Most org-level GitHub configurations require PRs for pushes to `main`; the `GITHUB_TOKEN` cannot push to a protected branch without admin-granted bypass or a PAT. The dedicated branch model avoids `main` entirely — branch protection rules do not apply to a separate branch the action creates and manages. This follows the established pattern of GitHub Pages (`gh-pages`) and similar bot-managed branches.

**Reference implementation:** [`specs/publisher-action.md`](../specs/publisher-action.md)

---

## Issue 19: GitHub identity verification claims

**Status:** Resolved

Signing identity is expressed as an OIDC issuer URL and subject claim — provider-agnostic. `signing_profile` added as REQUIRED on Dual-Attested manifest items; conforming clients MUST verify that the Rekor certificate's OIDC issuer and subject match the declared `signing_profile`. Mutable-name rename risk (OIDC subjects derived from repository names are vulnerable if a publisher renames their repo) documented as a known v1 limitation. Informative table covers GitHub Actions and GitLab CI; Forgejo/Codeberg excluded until their OIDC Actions support ships (tracking: Gitea PR #36988, Forgejo PR #5344).

**Reference implementation:** [`specs/publisher-action.md`](../specs/publisher-action.md)

---

## Issue 20: Binary revocation states (REVOKED / YANKED)

**Status:** Resolved

Client behavior is determined by revocation source (registry = hard block, publisher = warn), not by reason code. The four reason codes (`malicious`, `compromised`, `deprecated`, `policy_violation`) are informational — they carry urgency signal for security operators and End Users but do not change client enforcement behavior. `details_url` is REQUIRED for registry revocations. Collapsing to REVOKED/YANKED would discard useful urgency signal without simplifying client implementation.

---

## Issue 21: Threat feeds vs cross-registry revocation

**Status:** Resolved

Cross-registry threat propagation is intentionally out of scope for MOAT v1. The per-registry trust model is a design property, not a limitation: users grant trust to specific registries, and revocation authority is scoped to the content each registry attests.

**Claim — trust bleeding:** Cross-registry revocation allows Registry A to issue revocations for content attested by Registry B. Users who trust Registry A did not grant Registry A authority over Registry B's content. This is trust bleeding: revocations from authorities users did not intend to grant. The failure mode is not adversarial — it is mundane policy divergence (Registry B is permissive, Registry A is conservative) producing alert fatigue or unintended content suppression.

**Claim — DoS vector:** The competitive-suppression DoS vector — a registry issuing cross-registry revocations against a competitor's content — is documented behavior from the CA ecosystem, where certificate authorities weaponized revocation complaints against competitors before governance rules were tightened.

**Claim — threat feeds fail at scale:** Threat feeds require sustained operational investment and governance. Analysis of the AI content aggregator ecosystem shows consistent failure: enthusiastic launch, three to six months of active maintenance, then abandonment without formal deprecation. Stale feeds harm users by blocking content on outdated signals with no explanation. The governance questions (who decides inclusions, removals, disputes) require an institutional body MOAT has no authority to create.

**Claim — the real-world signal path works without MOAT:** For npm, PyPI, and crates.io, malicious package discovery flows through security researcher → CVE / GitHub Security Advisory → community channels, not through protocol-level cross-registry mechanisms. This path functions without MOAT intermediation. MOAT's job is clean enforcement when a registry revokes its own content — which the current model already provides.

This decision also closes Issue 14.

---

## Issue 22: Archive hashing vs directory hashing

**Status:** Resolved (rationale preserved)

Directory hashing is intentional — MOAT's model is registry-side crawling of source content, not publisher-side packaging. If MOAT adds creator-side packaging tooling in a future version, archive hashing should be reconsidered at that point. Deferred to a future version.

**Reference implementation:** [`moat_hash.py`](../moat_hash.py)

---

## Issue 23: SSH profile retention vs CI-only mandate

**Status:** Resolved

SSH signing removed from the spec entirely. Sigstore keyless OIDC is the only signing profile in v1.

**Claim:** SSH key distribution is an unsolved problem at ecosystem scale. There is no reliable mechanism to distribute and verify SSH public keys across a decentralized content ecosystem — no equivalent of a certificate authority, no established key registry, no revocation path that does not require out-of-band coordination. Air-gapped or private registry operators who cannot use the public Sigstore instance can satisfy the signing requirement with a private Rekor instance. Sigstore keyless OIDC tying signing identity to an existing trusted identity provider (GitHub Actions OIDC) solves both the key distribution and revocation problems without new infrastructure.

**Reference implementation:** [`specs/publisher-action.md`](../specs/publisher-action.md)

---

## Issue 24: Runtime dependency scope

**Status:** Resolved

Scope Boundary section includes an explicit runtime dependency disclaimer. Conforming clients SHOULD surface the boundary at install time; companion specs MAY require external dependency declaration. Full dependency graphs deferred to a future version.
