# MOAT Trust Anchor Research

**Date:** 2026-04-03
**Purpose:** Deep research synthesis to ground the trust anchor panel discussion. Covers OIDC subject formats, SSH signing key APIs, Sigstore federation, and supply chain trust model precedents.

---

## Table of Contents

1. [Critical Findings](#critical-findings)
2. [OIDC Subject Formats](#oidc-subject-formats)
3. [SSH Signing Key APIs](#ssh-signing-key-apis)
4. [Sigstore Federation](#sigstore-federation)
5. [Supply Chain Trust Models](#supply-chain-trust-models)
6. [Revised Panel Questions](#revised-panel-questions)

---

## Critical Findings

Six findings that reshape the trust anchor design.

### Finding 1: The Extraction Algorithm Must Change

The trust anchor doc says: *"Strip `https://` from the OIDC subject, split on `/`, take first 3 components."*

This is wrong on two levels:

- **Fulcio doesn't use `sub` for identity.** It extracts provider-specific claims and embeds them as OID extensions in the signing certificate. The relevant extension is `1.3.6.1.4.1.57264.1.12` (Source Repository URI), populated from the `repository` claim (GitHub) or `project_path` claim (GitLab).
- **The `sub` claim is customizable.** GitHub orgs can change the `sub` composition via REST API. GitLab's `sub` includes ref type and branch. Parsing `sub` is fragile.

**The correct algorithm:** Extract the Source Repository URI from the Fulcio certificate extension, strip the `https://` scheme, and compare to `source_repo` with exact string equality. No splitting, no "take first N components." The certificate extension already contains the clean repo identity.

| Provider | Certificate Extension Value | Matches `source_repo` |
|----------|---------------------------|----------------------|
| GitHub | `https://github.com/alice/code-review` | `github.com/alice/code-review` |
| GitLab | `https://gitlab.com/org/subgroup/project` | `gitlab.com/org/subgroup/project` |

This is simpler, more robust, and handles GitLab subgroups naturally.

### Finding 2: Forgejo Can't Sign Today

The trust anchor doc lists Forgejo with "OIDC support merged January 2026, full support expected in v15." Research found:

- Forgejo Actions does **not** support `id_tokens`/OIDC tokens
- Fulcio has **no** Forgejo issuer type in its codebase
- No open Fulcio issues requesting Forgejo support

The Appendix C table in the main spec also lists Forgejo. Both need correction.

### Finding 3: npm Already Solved This Problem

npm's provenance model is essentially identical to what MOAT is building:

1. Publisher declares source identity in metadata (`package.json` -> `repository.url`)
2. Signing certificate independently asserts source identity via OIDC (Fulcio extension)
3. Registry/verifier checks they match

npm also discovered the **bootstrap problem**: on first publish, the self-declared `source_repo` has no prior state to validate against. MOAT has the same issue.

PyPI went further with **explicit pre-registration** (Trusted Publishers) and uses `repository_owner_id` (numeric, immutable) for account resurrection protection.

### Finding 4: SSH Platform Key Discovery Is Viable

- GitHub: `GET /users/{username}/ssh_signing_keys` -- public, unauthenticated
- GitLab: `GET /api/v4/users/:id/keys` with `usage_type` filtering -- public without auth
- GitLab reverse lookup by fingerprint requires admin auth

Weakness: checking current key state, not state at signing time.

### Finding 5: No Sigstore Federation Exists

Each Sigstore deployment is an independent trust domain with its own TUF root. No mechanism to federate. Consumers must explicitly configure trust per instance.

### Finding 6: sigstore-a2a Exists

A Sigstore project for signing AI Agent Cards -- cryptographically binding agent metadata to source repos using keyless infrastructure. Conceptually very close to MOAT.

---

## OIDC Subject Formats

### Critical: Fulcio Does NOT Use `sub` Directly for CI Providers

Fulcio extracts **provider-specific claims** for the certificate's Subject Alternative Name (SAN), not the raw `sub` claim.

| Provider | SAN URI Source Claim | SAN URI Example |
|----------|---------------------|-----------------|
| GitHub Actions | `job_workflow_ref` | `https://github.com/octo-org/octo-repo/.github/workflows/release.yml@refs/heads/main` |
| GitLab CI | `ci_config_ref_uri` | `https://gitlab.com/my-group/my-project//path/to/.gitlab-ci.yml@refs/heads/main` |

The **repository identity** comes from these Fulcio OID extensions:

| OID | Name | Source Claim |
|-----|------|-------------|
| `1.3.6.1.4.1.57264.1.12` | Source Repository URI | `repository` / `project_path` |
| `1.3.6.1.4.1.57264.1.15` | Source Repository Identifier | `repository_id` / `project_id` |
| `1.3.6.1.4.1.57264.1.16` | Source Repository Owner URI | `repository_owner` |
| `1.3.6.1.4.1.57264.1.17` | Source Repository Owner Identifier | `repository_owner_id` |

### GitHub Actions

**Issuer (`iss`):** `https://token.actions.githubusercontent.com`

**Subject (`sub`) format -- default:** `repo:{owner}/{repo}:{context}`

| Trigger | `sub` format | Example |
|---------|-------------|---------|
| Environment deployment | `repo:{owner}/{repo}:environment:{env_name}` | `repo:octo-org/octo-repo:environment:Production` |
| Branch push | `repo:{owner}/{repo}:ref:refs/heads/{branch}` | `repo:octo-org/octo-repo:ref:refs/heads/main` |
| Tag push | `repo:{owner}/{repo}:ref:refs/tags/{tag}` | `repo:octo-org/octo-repo:ref:refs/tags/v1.0.0` |
| Pull request | `repo:{owner}/{repo}:pull_request` | `repo:octo-org/octo-repo:pull_request` |

**Subject claim customization:** Organizations can customize the `sub` composition via REST API using `include_claim_keys`. Default is `["repo", "context"]`. This is why parsing `sub` is unreliable.

**Key claims for repo identity extraction:**

| Claim | Example Value |
|-------|--------------|
| `repository` | `octo-org/octo-repo` |
| `repository_owner` | `octo-org` |
| `repository_id` | `123456789` |
| `repository_owner_id` | `987654321` |
| `repository_visibility` | `public` / `private` / `internal` |
| `ref` | `refs/heads/main` |
| `sha` | `abc123...` |
| `job_workflow_ref` | `octo-org/octo-repo/.github/workflows/release.yml@refs/heads/main` |
| `actor` | `username` |

**How to extract repo identity:** Use the `repository` claim directly (gives `owner/repo`). Always present regardless of subject claim customization.

### GitLab CI/CD

**Issuer (`iss`):** `https://gitlab.com` (or `https://{your-domain}` for self-hosted)

**Subject (`sub`) format -- default:** `project_path:{full/path}:ref_type:{type}:ref:{branch_name}`

**Nested subgroups are fully supported:**

| Scenario | `sub` value |
|----------|-------------|
| Simple group | `project_path:mygroup/myproject:ref_type:branch:ref:main` |
| One subgroup | `project_path:mygroup/mysubgroup/myproject:ref_type:branch:ref:main` |
| Deep nesting | `project_path:org/team/area/project:ref_type:branch:ref:main` |

**Key claims for repo identity extraction:**

| Claim | Example Value |
|-------|--------------|
| `project_path` | `mygroup/mysubgroup/myproject` |
| `project_id` | `12345` |
| `namespace_path` | `mygroup/mysubgroup` |
| `namespace_id` | `678` |
| `ci_config_ref_uri` | `gitlab.com/mygroup/mysubgroup/myproject//path/to/.gitlab-ci.yml@refs/heads/main` |

**How to extract repo identity:** Use `project_path` (gives full `group/[sub/]project` path).

### Forgejo

**Status: No OIDC token support for Actions workflows.**

- Forgejo Actions does NOT support `id_tokens` / OIDC tokens
- Fulcio has no Forgejo issuer in its codebase
- No open Fulcio issues requesting Forgejo/Gitea as trusted issuers

Forgejo cannot participate in Sigstore signing via native OIDC tokens today.

---

## SSH Signing Key APIs

### GitHub

| Method | Path | Auth Required | Notes |
|--------|------|---------------|-------|
| `GET` | `/users/{username}/ssh_signing_keys` | No | Public, unauthenticated |
| `GET` | `/user/ssh_signing_keys` | Yes (`read:ssh_signing_key`) | Authenticated user's own keys |
| `GET` | `/user/ssh_signing_keys/{id}` | Yes | Single key by ID |

**Response fields per key:** `id`, `key`, `title`, `created_at`

**Critical distinction:** GitHub maintains two completely separate key pools. Authentication keys (`/users/{username}/keys`) and signing keys (`/users/{username}/ssh_signing_keys`) are different API resources. The `https://github.com/{username}.keys` endpoint returns **only authentication keys**, not signing keys.

**Organization-level:** No org-level endpoint for signing keys. Must enumerate members and query individually.

### GitLab

| Method | Path | Auth Required | Notes |
|--------|------|---------------|-------|
| `GET` | `/api/v4/users/:id/keys` | No | Any user's keys (public) |
| `GET` | `/api/v4/keys?fingerprint={fp}` | Yes (admin) | Reverse lookup by fingerprint |

**The `usage_type` field (GitLab 15.7+):** `auth`, `signing`, or `auth_and_signing`. Unlike GitHub's separate pools, GitLab uses a single pool with a discriminator. Filter client-side for `signing` or `auth_and_signing`.

### Source-Binding Algorithm for SSH

1. Given content signed by SSH key with fingerprint `F`
2. Given claimed `source_repo` as `host/owner/repo`
3. Extract `owner` from `source_repo`
4. Fetch `GET /users/{owner}/ssh_signing_keys` (GitHub) or `/api/v4/users/:id/keys` (GitLab)
5. Compute fingerprints of returned keys
6. Check if `F` is in the set

**Limitations:**
- Checking current state, not state at signing time (keys can be added/removed)
- For org repos, must check org members' keys, not org name
- No standard protocol exists for this -- it would be novel to MOAT

### How Git SSH Signing Works

Requires Git 2.34+ and OpenSSH 8.1+. Git invokes `ssh-keygen -Y sign` with the private key. Verification uses an `allowed_signers` file mapping email identities to trusted public keys. Platform verification (GitHub/GitLab) additionally checks the signing key is registered to the pusher's account and the committer email matches.

### Related: sigstore-a2a

A new Sigstore project specifically for signing AI Agent Cards using keyless infrastructure. Binding agent metadata to source repos. Conceptually very close to MOAT but uses OIDC+Fulcio rather than SSH.

---

## Sigstore Federation

### Self-Hosted Fulcio

**Prerequisites:** A signing backend (KMS, HSM, or file-based key), a certificate chain (root CA + optional intermediate), optionally a CT log (Trillian + MySQL/MariaDB), and an OIDC provider.

**Custom OIDC connection:** Fulcio's config supports `oidc-issuers` (specific issuers) and `meta-issuers` (wildcard patterns for dynamic URLs like AWS EKS endpoints). CI providers use the `ci-provider` type with template-based metadata.

**Any OIDC provider works:** Keycloak, Okta, Azure AD, Forgejo's OIDC, GitLab OIDC -- all can be configured as Fulcio issuers.

### Self-Hosted Rekor

Requires Go, MySQL-compatible database, and Trillian. Technically optional alongside Fulcio, but practically necessary for audit trail. Without monitoring, "maintaining a private Sigstore deployment is just a project without any security benefit."

**Privacy motivation:** Public Rekor exposes provenance metadata (emails, repo URLs) to anyone. Private repos/artifacts typically need private Rekor.

### No Federation Exists

**There is no federation in the traditional sense.** Each Sigstore deployment has its own independent TUF root. No mechanism to "federate" into the public trust root.

The model is **independent PKI domains with explicit trust configuration:**
- Each deployment produces its own TUF root (`root.json`)
- Consumers must explicitly configure trust per instance
- No automatic discovery; trust roots distributed out-of-band

### Consumer Trust Configuration

Three approaches, in order of preference:

1. **TUF repository** (recommended): Private instance hosts a TUF mirror. Consumer runs `cosign initialize --mirror <TUF_MIRROR> --root <root.json>`.
2. **Trusted Root file**: Manually assembled via `cosign trusted-root create`, passed to `cosign verify --trusted-root <file>`.
3. **Environment variables** (last resort): `SIGSTORE_REKOR_PUBLIC_KEY`, `SIGSTORE_ROOT_FILE`, etc.

### The Public Sigstore TUF Root

Established through a public root key signing ceremony with 5 keyholders from different organizations. Published at `https://tuf-repo-cdn.sigstore.dev/`. Cosign ships with an embedded copy for bootstrapping.

**Cannot be extended for private instances.** Private deployments create their own independent TUF roots by design.

### Real-World Self-Hosted Deployments

- **Red Hat Trusted Artifact Signer**: Production-ready distribution for OpenShift, integrates with Keycloak
- **Chainguard Images Sigstore Bundle**: 17 container images, FIPS-compliant variants
- **sigstore-scaffolding**: Fastest path to a working private stack on Kubernetes
- **Challenges reported**: Monitoring, certificate/key rotation, TUF metadata expiration

### Implications for MOAT

1. **Consumers cannot verify Sigstore signatures without knowing which trust root to use.** The spec may need to acknowledge this.
2. **The public-good instance is the easy default, not the only option.**
3. **OIDC issuer diversity is well-supported.** The spec doesn't need to enumerate supported forges -- just specify OIDC token requirements.
4. **No federation means explicit trust.** The spec should define how registries/manifests advertise their Sigstore trust root (or defer this explicitly).

---

## Supply Chain Trust Models

### How Each Spec Answers "Who to Trust"

| Spec | Who Decides Trust | Where Trust Lives | Bootstrap |
|------|------------------|-------------------|-----------|
| **SLSA** | Verifier (registry or consumer) | Preconfigured trust root mapping | Manual config or registry default |
| **in-toto** | Project owner (via layout) | Signed layout listing functionary keys | Out-of-band (defers to TUF) |
| **TUF** | Repository operator | `root.json` shipped with client | Out-of-band (TOFU or trusted channel) |
| **npm** | Registry (server-side check) | Repository URL match + Trusted Publisher config | First publish establishes binding |
| **PyPI** | Package owner (explicit registration) | Trusted Publisher config on PyPI | Human login + pre-registration |

### SLSA (Supply-chain Levels for Software Artifacts)

**Trust anchor:** The verifier's preconfigured roots of trust -- a mapping from `(builder public key identity, builder.id)` to a SLSA Build Level.

**Key insight:** SLSA's approach of making the verifier responsible for maintaining a trust root mapping (rather than a global PKI) is practical but pushes complexity to consumers. The registry-as-verifier pattern is the dominant real-world deployment.

**Relevant to MOAT:** SLSA explicitly addresses the "valid signature vs. authorized signer" gap. A valid provenance signature only proves "this builder produced this artifact." The verifier must separately check builder identity, source repository, and build entry point match expectations.

### in-toto

**Trust anchor:** The project owner's public key, distributed out-of-band. Project owner signs a layout defining all steps and authorized functionaries per step.

**Key insight:** The most explicit authorization model. Each step lists exactly which keys are authorized. An unauthorized functionary's valid signature is rejected because their key isn't listed for that step. But it's heavyweight -- requires a trusted project owner to define policy. Over-engineered for a content package ecosystem.

### TUF (The Update Framework)

**Trust anchor:** The root metadata file (`root.json`), distributed out-of-band. Contains public keys and thresholds for all top-level roles.

**Key insight:** Path-based delegation model is directly relevant to MOAT. "This key is authorized for this namespace" maps to "this OIDC identity is authorized for this `source_repo`." Chain-of-trust rotation is elegant but requires long-lived infrastructure.

### npm Provenance

**Trust anchor:** Sigstore's public-good infrastructure + npm registry as verifier.

**Publisher authorization algorithm:**
1. Verify Sigstore bundle
2. Match `repository.url` in `package.json` against Source Repository URI in signing certificate
3. Verify certificate extensions match SLSA provenance statement
4. If all pass, registry signs a publish attestation

**Trusted Publishing (GA 2025, mandatory Dec 2025):** Publisher pre-registers a trust relationship: "GitHub Actions workflow `release.yml` in repo `org/package` is authorized to publish this package."

**Key insight:** Closest analogue to MOAT's `source_repo` binding. Same self-declared metadata problem -- `package.json` repository field has no prior state on first publish. npm solved this by making the registry the verifier.

### PyPI Trusted Publishers

**Trust anchor:** PyPI itself + OIDC identity providers.

**Explicit pre-registration:** Package owner logs into PyPI and configures a Trusted Publisher specifying: repository owner, repository name, workflow filename, and optionally environment name.

**Account resurrection protection:** Uses `repository_owner_id` (numeric, immutable) instead of just the repo name. If someone takes over a deleted GitHub username, the ID won't match.

**Key insight:** Strongest explicit authorization step. But requires a registry with accounts. For MOAT's decentralized model, this exact approach doesn't work. The `repository_owner_id` stability mechanism is worth studying.

### Cross-Cutting Patterns for MOAT

1. **npm's model is the closest analogue.** `source_repo` binding matched against Fulcio certificate extensions is the same pattern npm uses.
2. **The self-declared metadata problem.** Both npm and MOAT have a field declared by the publisher in a file they control. Trust works because it's integrity-bound post-signing, but first publish is self-asserted.
3. **Registry-as-verifier is dominant.** SLSA, npm, and PyPI converge on registry performing verification server-side. Individual consumer verification exists as defense in depth.
4. **Account resurrection / identity stability.** PyPI's `repository_owner_id` is a hardening worth considering.
5. **TUF's path-based delegation** maps to namespace authorization for future MOAT extensions.

---

## Revised Panel Questions

Based on the research, the panel should address:

1. **Platform-as-publisher + source_repo dual role** -- npm solved this with registry-as-verifier. PyPI added pre-registration. MOAT doesn't have a central registry. How does the trust model work without one? Does `source_repo` stay as one field or split?

2. **Host trust and Sigstore instance trust** -- No federation means explicit trust config. The spec defines *how* to verify but punts on *which hosts/instances to trust*. Is npm's model (registry decides) right for MOAT, or does MOAT need something different?

3. **Version rollback + trust anchor interaction** -- Does the trust anchor make rollback attacks more convincing? Should MOAT consider freshness recommendations?

4. **The bootstrap problem** -- First-publish `source_repo` is self-asserted. npm and PyPI both have this. How should MOAT handle it?

5. **sigstore-a2a alignment** -- Should MOAT align with, reference, or differentiate from the sigstore-a2a approach?

---

## Sources

### OIDC Formats
- [GitHub OIDC Token Claims](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [GitLab CI/CD OIDC](https://docs.gitlab.com/ee/ci/secrets/id_token_authentication.html)
- [Fulcio OIDC Configuration](https://github.com/sigstore/fulcio/blob/main/docs/oidc.md)
- [Fulcio CI Provider Streamlining](https://blog.sigstore.dev/fulcio-ci-provider/)
- [OIDC Usage in Fulcio](https://docs.sigstore.dev/certificate_authority/oidc-in-fulcio/)

### SSH Signing Keys
- [GitHub SSH Signing Keys API](https://docs.github.com/en/rest/users/ssh-signing-keys)
- [GitLab User Keys API](https://docs.gitlab.com/api/user_keys/)
- [GitLab Keys API (fingerprint lookup)](https://docs.gitlab.com/api/keys/)
- [sigstore-a2a](https://github.com/sigstore/sigstore-a2a)

### Sigstore Federation
- [Configuring Cosign with Custom Components](https://docs.sigstore.dev/cosign/system_config/custom_components/)
- [Sigstore Scaffolding](https://github.com/sigstore/scaffolding)
- [Sigstore BYO sTUF with TUF](https://blog.sigstore.dev/sigstore-bring-your-own-stuf-with-tuf-40febfd2badd/)
- [Running Sigstore Locally](https://blog.sigstore.dev/a-guide-to-running-sigstore-locally-f312dfac0682/)
- [Chainguard: sigstore, the local way](https://www.chainguard.dev/unchained/sigstore-the-local-way)
- [Sigstore Root Signing](https://github.com/sigstore/root-signing)
- [Policy Controller](https://docs.sigstore.dev/policy-controller/overview/)

### Supply Chain Trust Models
- [SLSA Specification v1.2](https://slsa.dev/spec/v1.2/)
- [SLSA Verifying Artifacts](https://slsa.dev/spec/v1.2/verifying-artifacts)
- [in-toto Specification](https://github.com/in-toto/docs/blob/master/in-toto-spec.md)
- [TUF Specification](https://theupdateframework.github.io/specification/latest/)
- [npm Provenance](https://github.com/npm/provenance)
- [npm Trusted Publishers](https://docs.npmjs.com/trusted-publishers/)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [PyPI Trusted Publishers Internals](https://docs.pypi.org/trusted-publishers/internals/)
- [OpenSSF Trusted Publishers for All Package Repositories](https://repos.openssf.org/trusted-publishers-for-all-package-repositories.html)
