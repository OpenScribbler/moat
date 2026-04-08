# MOAT OWASP Alignment

**Status:** Research reference (extracted from [moat-revised-outline.md](moat-revised-outline.md))

This document maps MOAT's design decisions against six OWASP standards.
Two are critical (direct design space); three are high (adjacent concerns);
one is a reference checklist.

Note: "Agentic Skills Top 10" (AST prefix) and "Top 10 for Agentic Applications"
(ASI prefix) are separate lists from different OWASP working groups.

---

MOAT is validated against six OWASP standards. Two are critical (direct design space); three are high (adjacent concerns); one is a reference checklist. Note: "Agentic Skills Top 10" (AST prefix) and "Top 10 for Agentic Applications" (ASI prefix) are separate lists from different OWASP working groups.

### Reference Standards

| Priority  | List                                           | URL                                                                              |
|-----------|------------------------------------------------|----------------------------------------------------------------------------------|
| Critical  | OWASP CI/CD Security Top 10 (2022)             | https://owasp.org/www-project-top-10-ci-cd-security-risks/                       |
| Critical  | OWASP Top 10 for Agentic Applications (2026)   | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ |
| High      | OWASP Top 10 (2025)                            | https://owasp.org/Top10/2025/                                                    |
| High      | OWASP LLM Top 10 (2025)                        | https://owasp.org/www-project-top-10-for-large-language-model-applications/      |
| High      | OWASP Agentic Skills Top 10 (2026)             | https://github.com/OWASP/www-project-agentic-skills-top-10                       |
| Medium    | OWASP API Security Top 10 (2023)               | https://owasp.org/www-project-api-security/                                      |
| Reference | OWASP Software Component Verification Standard | https://scvs.owasp.org                                                           |

### Agentic Skills Top 10 (AST prefix)

OWASP Agentic Skills Top 10 (v1.0, 2026) maps to MOAT as follows:

| OWASP Risk                      | MOAT Coverage                                                                                            | Status                     |
|---------------------------------|----------------------------------------------------------------------------------------------------------|----------------------------|
| AST01 — Malicious Skills        | Content hash + Sigstore signing + Rekor transparency log                                                 | ✅ Addressed in protocol    |
| AST02 — Supply Chain Compromise | Transparency logs (Rekor), registry trust model, explicit registry add                                   | ✅ Addressed in protocol    |
| AST03 — Over-Privileged Skills  | Out of scope (content format concern, not registry protocol)                                             | —                          |
| AST04 — Insecure Metadata       | Registry signing covers manifest integrity; scan_status covers quality                                   | ⚠️ Partially addressed (open issue #6) |
| AST05 — Unsafe Deserialization  | Out of scope (client implementation concern)                                                             | —                          |
| AST06 — Weak Isolation          | Out of scope (runtime concern)                                                                           | —                          |
| AST07 — Update Drift            | Content hash + lockfile model catches drift                                                              | ✅ Addressed in protocol    |
| AST08 — Poor Scanning           | `scan_status` REQUIRED in manifest with structured scanner array schema (name, version, result, scanned_at). `not_scanned` is a valid value — the spec makes scanning visible and auditable, not mandatory. **Note:** MOAT addresses *transparency about scanning*, not poor scanning itself. A registry can set `not_scanned` and remain conforming. This is appropriate — the spec is a distribution protocol, not a scanning mandate. | ⚠️ Partially addressed — scanning transparency yes, scanning requirement out of scope |
| AST09 — No Governance           | Revocation mechanism (`revocations` array REQUIRED, four reason codes, normative client behavior) provides formal content lifecycle management. Registry identity is declared and verifiable; signing identity changes require client re-approval. `risk_tier` was considered and dropped from v1 — content quality assessment is out of scope for a distribution protocol; `scan_status` provides scanning transparency instead. | ✅ Addressed in protocol    |
| AST10 — Cross-Platform Reuse    | MOAT is platform-agnostic by design                                                                      | ✅ Addressed in protocol    |

OWASP's Universal Skill Format embeds `content_hash` and `scan_status` in individual skill files (SKILL.md frontmatter). MOAT's approach puts these in the registry manifest per-item entries instead — more sound architecturally (avoids self-referential hash problem) and consistent with how npm, Cargo, and Go handle this. The information is equivalent; the location differs.

### CI/CD Security Top 10 (CICD-SEC prefix)

The single most directly applicable list: MOAT is a domain-specific implementation of these controls for AI content registries.

| OWASP Risk                                          | MOAT Coverage                                                                                                                                                | Status                         |
|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|
| CICD-SEC-3 — Dependency Chain Abuse                 | Verified checksums block content substitution once content is identified by hash. Revocation prevents post-distribution persistence. **Not addressed:** namespace enforcement — the spec defines a `name` field and `source_uri` per item but provides no mechanism preventing two registries from publishing content under the same name or preventing typosquatting within a registry. | ⚠️ Partially addressed — hash integrity yes, namespace enforcement not yet specified |
| CICD-SEC-8 — Ungoverned 3rd Party Services          | Registry federation trust model; registries declare and vet upstream sources                                                                                 | ⚠️ Partially addressed (not yet specified) |
| CICD-SEC-9 — Improper Artifact Integrity Validation | Signed manifests + hash pinning + lockfile = the prescribed control per CICD-SEC-9                                                                           | ✅ Addressed in protocol       |

### Top 10 for Agentic Applications (ASI prefix)

ASI04 explicitly names signed manifests + curated registries as the required mitigation — MOAT is the protocol that implements this.

| OWASP Risk                                   | MOAT Coverage                                                                                         | Status    |
|----------------------------------------------|-------------------------------------------------------------------------------------------------------|-----------|
| ASI04 — Agentic Supply Chain Vulnerabilities | Signed manifests, curated registry model, hash verification — the directly prescribed answer          | ✅ Addressed in protocol |
| ASI07 — Insecure Inter-Agent Communication   | Out of scope for v1 (runtime communication, not distribution)                                         | —         |
| ASI10 — Rogue Agents                         | Registry signing establishes verifiable identity; rogue agents cannot impersonate MOAT-signed content | ✅ Addressed in protocol |

### OWASP Top 10:2025 (Web Application)

A03 and A08 are the 2025 Top 10's explicit recognition that supply chain and artifact integrity are first-class concerns.

| OWASP Risk                                     | MOAT Coverage                                                                  | Status                    |
|------------------------------------------------|--------------------------------------------------------------------------------|---------------------------|
| A03:2025 — Software Supply Chain Failures      | Signed packages, attestation — MOAT's core design                             | ✅ Addressed in protocol  |
| A04:2025 — Cryptographic Failures              | Key management, algorithm selection, certificate lifecycle in signing profiles | ⚠️ Informative only in v1 |
| A08:2025 — Software or Data Integrity Failures | Content cannot be silently replaced between signing and installation           | ✅ Addressed in protocol  |

### LLM Top 10:2025 (LLM prefix)

LLM03 is the AI-specific restatement of supply chain failure — MOAT is the registry-layer control LLM03 says must exist.

| OWASP Risk                                | MOAT Coverage                                                                    | Status                              |
|-------------------------------------------|----------------------------------------------------------------------------------|-------------------------------------|
| LLM03:2025 — Supply Chain Vulnerabilities | Cryptographic verification + attestation tracking + trusted registry channel   | ✅ Addressed in protocol               |
| LLM04:2025 — Data and Model Poisoning     | Attestation chain covers behavioral specs in distributed content                | ⚠️ Partially addressed (content-type dependent) |
| LLM07:2025 — System Prompt Leakage        | Out of scope for protocol; referenced in "Sensitive Files" publisher requirement | —                                   |

### API Security Top 10:2023

MOAT's registry HTTP surface is an API; these controls apply to the publish/fetch endpoints.

| OWASP Risk                              | MOAT Coverage                                                                                        | Status               |
|-----------------------------------------|------------------------------------------------------------------------------------------------------|----------------------|
| API2:2023 — Broken Authentication       | Publisher and consumer auth is registry implementation concern; spec must define required auth model | ⚠️ Not yet specified |
| API7:2023 — Server Side Request Forgery | URI validation for external references (upstream registries, CDN mirrors)                            | ⚠️ Not yet specified |
| API10:2023 — Unsafe Consumption of APIs | Federation trust: treat upstream registry responses as untrusted input                               | ⚠️ Not yet specified |
