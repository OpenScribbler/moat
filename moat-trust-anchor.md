# MOAT Trust Anchor: Sigstore OIDC + `source_repo` Binding

## What This Document Is

A completed design record for the trust anchor mechanism in MOAT v0.2.0. Documents the cryptographic chain from content hashing through source binding, how it works for each publisher type, honest adoption constraints, and the design decisions behind spec changes.

This document was developed through deep research (4 parallel agents on OIDC formats, SSH APIs, Sigstore federation, and supply chain trust models) followed by a 5-agent adversarial panel discussion (3 rounds, 18 bus entries). All panel decisions have been applied to this document and integrated into the MOAT specification (`moat-spec.md` v0.2.0). Panel artifacts are in `panel/` (message-bus.jsonl, consensus.md, personas.md).

**Status:** Design complete. Spec updated. This document is now a reference for the rationale behind v0.2.0's trust anchor additions.

---

## The Problem Being Solved

MOAT currently verifies two things: content integrity (the files match the hash) and metadata integrity (the metadata matches its hash). What it does not verify is whether the signer is *authorized* — there is a gap between "signature verified" and "signature verified against someone I trust."

An attacker can create a `meta.yaml` claiming `source_repo: github.com/alice/trusted-skill`, compute valid hashes, sign with their own OIDC identity, and pass every current verification check. The claimed source is never checked against the actual signer.

This document describes closing that gap by binding the Sigstore OIDC identity to the `source_repo` field already present in `meta.yaml`.

---

## Core Insight

`source_repo` is already integrity-bound inside `meta_hash`. Git providers (GitHub, GitLab, Forgejo) already issue OIDC tokens that encode the repository identity in a structured, predictable format. The trust anchor is already in the data — this change makes the binding normative.

**Before:** signature verified = "some valid OIDC identity signed this"
**After:** signature verified = "the owner of the claimed `source_repo` signed this"

---

## The Cryptographic Chain

The chain has four links. Each depends on the previous. Break any one and verification fails.

### Link 1: Content → `content_hash`
**Who:** Publisher tooling (CLI, CI/CD workflow)
**When:** Publish time, against files in their final form
**What:** SHA-256 of the directory tree manifest — every file path and its hash, sorted and concatenated, then hashed again
**Guarantee:** These exact files were present when this hash was computed

### Link 2: `content_hash` → `meta_hash`
**Who:** Same publisher tooling, immediately after link 1
**When:** Publish time, `content_hash` must exist first
**What:** SHA-256 of all provenance fields including `content_hash`, serialized as canonical JSON (JCS)
**Guarantee:** This metadata cannot be detached from the content it describes. Pairing this `meta.yaml` with different content invalidates `meta_hash`.

### Link 3: `meta_hash` → signature
**Who:** CI/CD runner (e.g. GitHub Actions) via Sigstore/Fulcio/Rekor
**When:** Publish time, after both hashes are written into `meta.yaml`
**What:** The runner requests an OIDC token from the git provider, presents it to Fulcio which issues an ephemeral 10-minute signing certificate, signs `MOAT-V1:{content_hash}\n{meta_hash}`, logs the result permanently in Rekor
**Guarantee:** A specific identity endorsed these exact hashes at a specific moment. The Rekor entry is permanent and public.

### Link 4: Signature → `source_repo` (+ `publisher_identity`)
**Who:** Consumer tooling at verify time
**When:** Verify time, after signature cryptographic validity is confirmed
**What:** Extract the Source Repository URI from the Fulcio certificate's OID extension `1.3.6.1.4.1.57264.1.12`. Strip `https://` and compare to `source_repo` in `meta.yaml` using exact string equality. If `publisher_identity` is present, the signing identity represents the publisher (a platform acting on behalf of the content author), not the author directly.
**Guarantee:** The signer is demonstrably the operator of the claimed source repository. When `publisher_identity` is present, consumers know this is delegated publishing and can apply appropriate trust policies.

### The Verify-Time Mirror

Verify time is the inverse of publish time, performed independently by the consumer:

1. Recompute `content_hash` from the local files — does it match `meta.yaml`?
2. Recompute `meta_hash` from the `meta.yaml` fields — does it match?
3. Fetch the signing certificate from Rekor by `log_index`, reconstruct the signing input, verify the signature cryptographically
4. Extract Source Repository URI from the certificate (OID `1.3.6.1.4.1.57264.1.12`), strip `https://`, compare to `source_repo`
5. If `publisher_identity` is present, surface this to the user — this is delegated publishing, not direct authorship

The consumer trusts nothing except the math and the OIDC infrastructure. They re-derive everything from scratch. That independence is what makes the chain meaningful.

### In One Sentence

**The content hashes to a value, that value is bound to metadata, that metadata is signed by an identity, and that identity is constrained to match the claimed source.**

---

## The Matching Rule

This is normative and must be specified precisely. Structural matching only — substring or `contains()` matching is explicitly prohibited because it is exploitable (an attacker controlling `github.com/alice-evil/skill` could pass a substring check for `github.com/alice/`).

**Extraction algorithm:**
1. Extract the Source Repository URI from the Fulcio signing certificate's OID extension `1.3.6.1.4.1.57264.1.12`
2. Strip the `https://` scheme prefix
3. Compare to `source_repo` with exact string equality

This is simpler and more robust than parsing the OIDC `sub` claim, which is customizable (GitHub orgs can change its composition via REST API) and formatted differently per provider. The Fulcio OID extension is populated from the `repository` claim (GitHub) or `project_path` claim (GitLab) and handles subgroups naturally.

**Provider certificate extension values:**

| Provider | OID 1.3.6.1.4.1.57264.1.12 Value | Matches `source_repo` |
|---|---|---|
| GitHub Actions | `https://github.com/{owner}/{repo}` | `github.com/{owner}/{repo}` |
| GitLab CI/CD | `https://gitlab.com/{group}/{project}` | `gitlab.com/{group}/{project}` |
| Custom OIDC | Consumer policy governs | — |

**Additional Fulcio OID extensions available for verification:**

| OID | Name | Use |
|-----|------|-----|
| `1.3.6.1.4.1.57264.1.12` | Source Repository URI | Primary `source_repo` binding (REQUIRED) |
| `1.3.6.1.4.1.57264.1.15` | Source Repository Identifier | Numeric repo ID (immutable, for hardening) |
| `1.3.6.1.4.1.57264.1.16` | Source Repository Owner URI | Owner-level binding |
| `1.3.6.1.4.1.57264.1.17` | Source Repository Owner Identifier | Numeric owner ID (for `repository_owner_id`) |

---

## Publisher Identity: Direct vs. Delegated Publishing

When a publisher signs content directly from their own repository, the Fulcio signing identity naturally matches `source_repo`. This is the common case — a solo developer or organization publishing from their own CI/CD pipeline.

When a **platform publishes on behalf of a user** (e.g., Claude.ai managing `github.com/syllago/community-skills/alice`), the platform is both the signing identity and the `source_repo` owner. The trust chain is intact — the platform's OIDC identity matches the platform-managed repo — but the trust *semantics* differ. A consumer trusting "Alice published this herself" is making a different judgment from "Platform X published this on Alice's behalf."

### The `publisher_identity` field

`publisher_identity` is a field in `meta.yaml` that makes delegated publishing explicit:

- **REQUIRED** when the signing identity differs from the `source_repo` owner — i.e., when the entity controlling the Fulcio certificate is not the natural author of the content
- **Absent** for direct-publish (the common case for solo developers and organizations)

The field value is a human-readable identifier for the publishing platform (e.g., `claude.ai`, `syllago-community`).

**How "differs" is determined programmatically:** Compare the Source Repository URI from Fulcio OID `1.3.6.1.4.1.57264.1.12` against `source_repo`. If the repository owner (the organizational entity) in the certificate matches the expected owner of `source_repo`, this is direct publishing. If the repository owner is a platform namespace (e.g., `syllago/community-skills/*`), `publisher_identity` is required.

### Verifier obligations

Verifiers MUST surface the `publisher_identity` distinction to users. Delegated publishing and direct publishing are not equivalent trust signals and MUST NOT be presented identically. A consumer's trust policy may treat them differently — for example, requiring additional review for platform-published content.

When `publisher_identity` is absent, verifiers MAY assume direct publishing.

---

## Who Actually Publishes With MOAT

This is the most important thing to be honest about. MOAT is a **platform-side and tooling-side spec**, not a user-side spec. The people who implement it are:

- **Tool vendors** (Anthropic, OpenAI, Cursor, Windsurf, etc.) building publishing pipelines
- **Registry operators** building distribution infrastructure
- **Organizations** managing internal skill libraries with DevOps resources
- **Developer-publishers** who live in the GitHub ecosystem and are comfortable with CI/CD

The individual non-coder creating a skill in a chat interface is never going to interact with MOAT directly. That's not a failure of the spec — it's the correct layering. MOAT is the interoperability contract between platforms. It defines what a signed skill looks like so that a skill published through Claude.ai can be verified by a consumer using Cursor, or Windsurf, or a registry. The user doesn't interact with it any more than they interact with TLS when they visit a website.

The spec should say this explicitly in Section 2, before the reader hits any normative detail.

---

## How It Works for Each Publisher Type

### Platform-Mediated (Non-Coder, Web App)

The user clicks "Publish" in a web interface. The platform:
1. Holds a managed git repo on the user's behalf (e.g. `github.com/syllago/community-skills/alice`)
2. Computes `content_hash` and `meta_hash`
3. Runs its own signing workflow using its OIDC identity
4. Writes the completed `meta.yaml`

The user never sees any of it. Trust model: *"this platform verified that Alice (authenticated via platform account) published this content at this time."* The platform's trustworthiness is the trust anchor. That's honest — it's what it actually is.

`source_repo` points to the platform-managed repo. The OIDC identity matches. The chain is complete.

### Solo Developer-Publisher (GitHub Workflow)

Has a GitHub account, comfortable with repos but not necessarily cryptography. The viable path:

1. **One-click template repo** — syllago publishes a template with `publish.yml` pre-built. User clicks "Use this template."
2. **Edit three fields in `meta.yaml`** — `name`, `type`, `authors`. `source_repo` is auto-filled by the workflow from `${{ github.repository }}`.
3. **Upload their content file** via GitHub web UI.
4. **Commit** — workflow triggers, computes everything, commits completed `meta.yaml` back. Green checkmark.

Updates: edit the file in GitHub web UI, bump `version`, commit. Workflow handles the rest.

This path works but it is not zero friction — the user has to understand GitHub at a basic level. It is the right path for the developer audience, not for the non-coder audience. The distinction matters.

### CI/CD Pipeline (Organization or Serious Individual)

MOAT is designed for this case. The workflow is a native part of their pipeline. Full control. Nothing to explain.

---

## Content Without a Git Repo

For content that lives entirely outside a platform — written in a text editor, shared via Slack — provenance is either:

- **Absent** — no `meta.yaml`, no provenance, consumer treats it accordingly
- **Hash-only** — publisher ran local tooling, hashes present, no signature
- **Platform-attested** — uploaded somewhere that signed it on their behalf

There is no realistic path to cryptographically signed provenance for this content without platform intermediation. The spec already handles this correctly: permissive consumers surface unsigned content as a distinct status rather than rejecting it. The spec should say explicitly — in Section 2 — that individual unsigned content is a legitimate and expected use case, not a failure state.

---

## Self-Hosted Instances: The Trust Root Problem

Self-hosted git instances (Forgejo, Gitea, GitLab CE) can be at arbitrary domains. Even when OIDC signing is available, the consumer has no basis for trusting the issuer without additional context.

**Note on Forgejo:** Forgejo Actions does not currently support OIDC tokens (`id_tokens`), and Fulcio has no Forgejo issuer type. Forgejo cannot participate in Sigstore keyless signing today. If this changes in the future, the self-hosted trust problem below still applies.

**Why this is hard:** GitHub and GitLab (SaaS) are trusted not because of anything in MOAT but because they are centralized services with known, stable OIDC issuer URLs, audited security practices, and abuse response infrastructure. A self-hosted instance at `git.alicecorp.com` could be a corporate installation with strong access controls or a personal server with no authentication. A valid OIDC token does not distinguish them.

**The spec position:** Consumer policy governs for self-hosted instances. The spec notes the ambiguity without prescribing a solution. Known providers (GitHub, GitLab SaaS) are trusted by default. Custom hosts require explicit consumer configuration via `sigstore_trust_root`.

**The enterprise path:** Run a self-hosted Fulcio instance, sign against an internal CA, configure consumer trust at the CA level via `sigstore_trust_root` in registry manifests. This is the independent Sigstore deployment model — each deployment has its own TUF root, and no federation mechanism exists. Consumers must explicitly configure trust per instance. It adds setup complexity but is architecturally sound.

---

## Residual Risks

**Repo takeover.** If an account is compromised, the attacker controls the repo and can obtain valid OIDC tokens for it. Failure mode maps to: "trust the owner of this GitHub account" — which is exactly how consumers already reason about GitHub repos. Not worse than key-based systems.

**Repo transfer.** New repo owner can sign with a valid matching OIDC identity. Old signed content still verifies. Registry namespace management is the mitigation — out of spec scope.

**Org repos with multiple contributors.** `source_repo` binds to the repo, not a specific person within it. Any team member with Actions write access can trigger signing. Mitigation: branch protection and required reviewers — operational, not spec.

**Workflow file manipulation.** An attacker with repo write access can add a signing workflow. Same mitigation: branch protection.

**Provider OIDC compromise.** Systemic risk, not MOAT-specific. Rekor transparency log provides partial detection via anomaly visibility at scale.

**Version rollback (WARNING).** The trust anchor makes rollback attacks *more* convincing, not less. An older, signed version of content passes all verification checks — including source binding. A v1.0 artifact from six months ago looks identical to a current artifact under the trust anchor model. Rekor timestamps attest *signing time*, not currency — a valid timestamp proves when content was signed, not whether a newer version exists. Source binding does not imply the content is the most recent valid version.

Registries SHOULD maintain a signed latest-version manifest per content package, enabling consumers to detect when they are being served stale content. This is a registry-layer responsibility — the trust anchor spec binds identity to source, not content to time. Consumers that require freshness guarantees SHOULD query the registry's latest-version endpoint and compare against the Rekor timestamp of the content they received.

---

## Implementation Decisions

**1. `source_repo` binding enforcement level**
- Strict consumers: REQUIRED. Mismatch between OIDC prefix and `source_repo` MUST fail verification.
- Permissive consumers: RECOMMENDED. Mismatch SHOULD surface as a distinct warning but does not block.

**2. Sigstore signature present, `source_repo` absent**
Signature verification and trust anchor check are two distinct outcomes. A consumer MUST:
- Report the signature as cryptographically valid (if it is)
- Report the trust anchor check as failed (source binding unavailable)
- MUST NOT treat "valid signature, no source binding" identically to "valid signature, source binding confirmed"

Strict consumers treat missing `source_repo` with a Sigstore signature as a trust anchor failure. Permissive consumers surface it as a distinct warning.

**3. Sigstore trust root advertisement**
Registry manifests and content bundles SHOULD include a `sigstore_trust_root` field referencing the TUF root used for signing. This enables consumers to verify content signed against any Sigstore instance, not just the public-good one.

The public-good Sigstore instance (`tuf-repo-cdn.sigstore.dev`) is the recommended default for open registries and community content. Enterprise deployments running private Sigstore instances use the same field to advertise their TUF root. Consumers configure which trust roots to accept based on their own policy.

No Sigstore federation mechanism exists — each deployment is an independent trust domain with its own TUF root. Trust roots are distributed out-of-band. The spec defines the advertisement mechanism; consumer policy governs which roots to accept.

**4. Self-hosted instance OIDC issuer trust**
Out of spec scope. The spec notes the ambiguity. Known providers (GitHub, GitLab SaaS) are trusted by default. Custom hosts require explicit consumer configuration via `sigstore_trust_root`. The self-hosted Fulcio path is documented as the enterprise solution.

**5. First-publish trust (TOFU)**
On first publish, `source_repo` is self-asserted — there is no prior state to validate against. This is an inherent property of decentralized systems without a central pre-registration authority.

Verifiers MUST treat the first-publish `source_repo` binding as an unvalidated claim until the signer has an established publish history. Subsequent publishes from the same signing identity and `source_repo` reinforce the binding. A change in signing identity for the same `source_repo` is a red flag that consumers SHOULD surface prominently.

Registries SHOULD implement their own first-publish authorization policies. Centralized registries MAY require explicit pre-registration (similar to PyPI Trusted Publishers). Community registries MAY accept TOFU with additional review. The spec does not mandate a specific first-publish policy — it documents the limitation and delegates policy to registries.

**6. `repository_owner_id` (account resurrection protection)**
Publishers SHOULD include `repository_owner_id` in `meta.yaml` — the numeric, immutable platform identifier for the repository owner (e.g., GitHub's numeric user/org ID from Fulcio OID `1.3.6.1.4.1.57264.1.17`). This protects against account resurrection attacks: if a username is deleted and re-registered, the numeric ID changes, making the impersonation detectable.

This field is RECOMMENDED, not REQUIRED. Not all platforms provide stable numeric identifiers. Registries that enforce identity stability SHOULD check this field when present.

---

## Related Work: sigstore-a2a

The [sigstore-a2a](https://github.com/sigstore/sigstore-a2a) project signs AI Agent Cards using Sigstore keyless infrastructure — cryptographically binding agent metadata to source repositories. This is conceptually close to MOAT's content package signing but addresses a different layer:

- **sigstore-a2a** signs agent cards — runtime identity and capability declarations for AI agents
- **MOAT** signs content packages — installable artifacts (skills, rules, hooks) for AI coding tools

The signing infrastructure is shared (Fulcio, Rekor, TUF), providing implicit compatibility at the verification toolchain level. No explicit format coupling or alignment is needed at v1 — the specs serve different artifact types with different trust requirements.

MOAT uses Fulcio OID extension `1.3.6.1.4.1.57264.1.12` for source binding. If sigstore-a2a uses the same extension, the extraction logic is compatible by construction. The specs should coordinate on OID extension usage to prevent divergence — this is the one surface where incompatibility would create real integration cost.

---

## Spec Changes Required

### Section 2 (Introduction) — Add two things

**Platform-first framing:** MOAT is designed to be implemented by platforms and tooling, not by end users directly. Individual content creators interact with MOAT through the platforms and tools they use, not by managing cryptographic operations themselves.

**The trust chain narrative:** A short walkthrough of all four links before the reader hits normative detail. The dependency order must be explicit. The `source_repo` binding should read as the natural completion of the chain, not as a security addendum.

### Section 9.2 — Sigstore Verification, add step 5a-5b

```
5a. Verify source_repo binding. Extract the Source Repository URI from
    the Fulcio signing certificate's OID extension 1.3.6.1.4.1.57264.1.12.
    Strip the https:// scheme prefix. This value MUST exactly equal the
    source_repo field value using exact string equality. Substring matching
    and contains() checks are explicitly prohibited. Strict consumers MUST
    fail verification if source_repo is absent or if the values do not
    match. Permissive consumers SHOULD surface a distinct warning. In both
    cases, the cryptographic signature validity and the source binding
    check are separate outcomes and MUST be reported separately.

5b. Check publisher_identity. If publisher_identity is present in
    meta.yaml, verifiers MUST surface this to the user — this content
    was published by a platform on behalf of the author, not by the
    author directly. Verifiers MUST NOT present delegated and direct
    publishing identically.
```

### Section 9.2 — Add first-publish TOFU acknowledgment

```
Note: On first publish, source_repo is self-asserted. Verifiers MUST
treat this as an unvalidated claim until the signer has an established
publish history. Registries SHOULD implement their own first-publish
authorization policies.
```

### Section 11 — Security Considerations, add subsections

1. Repo takeover, repo transfer, org multi-committer, and workflow manipulation as residual risks under this model. Branch protection as the recommended operational mitigation. Self-hosted instance OIDC trust as a consumer policy decision with the self-hosted Fulcio path as the enterprise solution.

2. Version rollback WARNING: Source binding amplifies rollback risk. Rekor timestamps attest signing time, not currency. Registries SHOULD maintain signed latest-version manifests.

3. First-publish trust: TOFU semantics with documented limitations. `repository_owner_id` as RECOMMENDED hardening for account resurrection protection.

### New fields in `meta.yaml`

| Field | Normative Level | When Required |
|-------|----------------|---------------|
| `publisher_identity` | REQUIRED when signing identity ≠ source_repo owner | Platform-managed/delegated publishing |
| `repository_owner_id` | RECOMMENDED | Always (when platform provides numeric IDs) |
| `sigstore_trust_root` | SHOULD (in registry manifests) | When using non-default Sigstore instance |

### Appendix D (new) — Provider OIDC Formats + Related Work

The Fulcio OID extension table above, marked informative. Note that custom OIDC issuers are consumer-policy territory. Document the independent Sigstore deployment model for enterprise self-hosted setups as a non-normative pattern. Reference sigstore-a2a as related work with scope differentiation.

---

## What Does Not Change

- Hash algorithms
- `meta_hash` computation
- `content_hash` computation
- Signing input format (`MOAT-V1:...`)
- SSH signing method — SSH has no `source_repo` binding equivalent and no `publisher_identity` mechanism; consumers rely on their own key trust mechanisms for SSH-signed content. Optional platform key discovery (GitHub `/users/{username}/ssh_signing_keys`, GitLab `/api/v4/users/:id/keys`) can provide partial verification but checks current key state, not state at signing time.
- All existing test vectors