# MOAT OWASP Alignment

**Status:** Research reference (extracted from moat-revised-outline.md)

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
| AST01 — Malicious Skills        | Content hash + Sigstore signing + Rekor transparency log                                                 | ✅ Covered                  |
| AST02 — Supply Chain Compromise | Transparency logs (Rekor), registry trust model, explicit registry add                                   | ✅ Covered                  |
| AST03 — Over-Privileged Skills  | Out of scope (content format concern, not registry protocol)                                             | —                          |
| AST04 — Insecure Metadata       | Registry signing covers manifest integrity; scan_status covers quality                                   | ⚠️ Partial (open issue #6) |
| AST05 — Unsafe Deserialization  | Out of scope (client implementation concern)                                                             | —                          |
| AST06 — Weak Isolation          | Out of scope (runtime concern)                                                                           | —                          |
| AST07 — Update Drift            | Content hash + lockfile model catches drift                                                              | ✅ Covered                  |
| AST08 — Poor Scanning           | `scan_status` REQUIRED in manifest (result: not_scanned valid); structured scanner array with scanned_at | ✅ Covered                  |
| AST09 — No Governance           | `risk_tier` REQUIRED in manifest (L0–L3 + not_analyzed + indeterminate); registry-assigned, advisory. Revocation mechanism provides the formal content lifecycle management AST09 explicitly prescribes. | ✅ Covered                  |
| AST10 — Cross-Platform Reuse    | MOAT is platform-agnostic by design                                                                      | ✅ Covered                  |

OWASP's Universal Skill Format embeds `content_hash`, `scan_status`, and `risk_tier` in individual skill files (SKILL.md frontmatter). MOAT's approach puts these in the registry manifest per-item entries instead — more sound architecturally (avoids self-referential hash problem) and consistent with how npm, Cargo, and Go handle this. The information is equivalent; the location differs.

### CI/CD Security Top 10 (CICD-SEC prefix)

The single most directly applicable list: MOAT is a domain-specific implementation of these controls for AI content registries.

| OWASP Risk                                          | MOAT Coverage                                                                                                                                                | Status                         |
|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|
| CICD-SEC-3 — Dependency Chain Abuse                 | Registry namespace enforcement + verified checksums block confusion/typosquatting + revocation prevents post-distribution persistence of compromised content | ✅ Covered                      |
| CICD-SEC-8 — Ungoverned 3rd Party Services          | Registry federation trust model; registries declare and vet upstream sources                                                                                 | ⚠️ Partial (not yet specified) |
| CICD-SEC-9 — Improper Artifact Integrity Validation | Signed manifests + hash pinning + lockfile = the prescribed control per CICD-SEC-9                                                                           | ✅ Covered                      |

### Top 10 for Agentic Applications (ASI prefix)

ASI04 explicitly names signed manifests + curated registries as the required mitigation — MOAT is the protocol that implements this.

| OWASP Risk                                   | MOAT Coverage                                                                                         | Status    |
|----------------------------------------------|-------------------------------------------------------------------------------------------------------|-----------|
| ASI04 — Agentic Supply Chain Vulnerabilities | Signed manifests, curated registry model, hash verification — the directly prescribed answer          | ✅ Covered |
| ASI07 — Insecure Inter-Agent Communication   | Out of scope for v1 (runtime communication, not distribution)                                         | —         |
| ASI10 — Rogue Agents                         | Registry signing establishes verifiable identity; rogue agents cannot impersonate MOAT-signed content | ✅ Covered |

### OWASP Top 10:2025 (Web Application)

A03 and A08 are the 2025 Top 10's explicit recognition that supply chain and artifact integrity are first-class concerns.

| OWASP Risk                                     | MOAT Coverage                                                                  | Status                    |
|------------------------------------------------|--------------------------------------------------------------------------------|---------------------------|
| A03:2025 — Software Supply Chain Failures      | Signed packages, provenance, attestation — MOAT's core design                  | ✅ Covered                 |
| A04:2025 — Cryptographic Failures              | Key management, algorithm selection, certificate lifecycle in signing profiles | ⚠️ Informative only in v1 |
| A08:2025 — Software or Data Integrity Failures | Content cannot be silently replaced between signing and installation           | ✅ Covered                 |

### LLM Top 10:2025 (LLM prefix)

LLM03 is the AI-specific restatement of supply chain failure — MOAT is the registry-layer control LLM03 says must exist.

| OWASP Risk                                | MOAT Coverage                                                                    | Status                              |
|-------------------------------------------|----------------------------------------------------------------------------------|-------------------------------------|
| LLM03:2025 — Supply Chain Vulnerabilities | Cryptographic verification + provenance tracking + trusted registry channel      | ✅ Covered                           |
| LLM04:2025 — Data and Model Poisoning     | Provenance chain covers behavioral specs in distributed content                  | ⚠️ Partial (content-type dependent) |
| LLM07:2025 — System Prompt Leakage        | Out of scope for protocol; referenced in "Sensitive Files" publisher requirement | —                                   |

### API Security Top 10:2023

MOAT's registry HTTP surface is an API; these controls apply to the publish/fetch endpoints.

| OWASP Risk                              | MOAT Coverage                                                                                        | Status               |
|-----------------------------------------|------------------------------------------------------------------------------------------------------|----------------------|
| API2:2023 — Broken Authentication       | Publisher and consumer auth is registry implementation concern; spec must define required auth model | ⚠️ Not yet specified |
| API7:2023 — Server Side Request Forgery | URI validation for external references (upstream registries, CDN mirrors)                            | ⚠️ Not yet specified |
| API10:2023 — Unsafe Consumption of APIs | Federation trust: treat upstream registry responses as untrusted input                               | ⚠️ Not yet specified |
