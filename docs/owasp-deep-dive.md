# OWASP Deep Dive: MOAT Applicability Analysis

**Status:** Working document  
**Date:** 2026-04-07  
**Author:** Holden Hewett + Maive  
**Purpose:** Deep research on each applicable OWASP risk — definitions, real-world incidents, ecosystem lessons, and implications for MOAT spec decisions.

---

## How to Read This Document

Each entry follows a consistent structure:

- **Status** — How well MOAT currently covers this risk (from the coverage map in `moat-revised-outline.md`)
- **What it is** — Brief definition and why it matters to a registry protocol
- **In the wild** — Real incidents and case studies from other ecosystems
- **What worked / What failed** — Ecosystem-level lessons
- **MOAT implications** — Where this should influence spec decisions

Coverage statuses from the outline:
- ✅ Covered — MOAT has an explicit design for this
- ⚠️ Partial — MOAT touches it but the spec doesn't fully resolve it
- — Out of scope for v1

---

## 1. OWASP CI/CD Security Top 10 (2022)

The single most directly applicable OWASP list. MOAT is effectively a domain-specific implementation of these controls for AI content registries.

**Reference:** https://owasp.org/www-project-top-10-ci-cd-security-risks/

---

### CICD-SEC-3 — Dependency Chain Abuse

**MOAT Status:** ✅ Covered  
**Reference:** https://owasp.org/www-project-top-10-ci-cd-security-risks/CICD-SEC-03-Dependency-Chain-Abuse

#### What It Is

Attackers exploit how build environments resolve packages from multiple sources — internal registries, public registries, and mirrors — to inject malicious packages. The four primary attack vectors are dependency confusion (namespace collision), dependency hijacking (account compromise), typosquatting (near-identical names), and brandjacking (impersonating trusted publishers).

#### In the Wild

**Dependency Confusion / Alex Birsan (2021):** Birsan published packages to public PyPI and npm with names matching internal packages at Fortune 500 companies, at artificially high version numbers (e.g., `6969.99.99`). The root cause was `pip`'s `--extra-index-url` flag, which merges public and private indexes and installs whichever has the higher version. This was a *known design flaw* with an open bug ticket since 2017. Affected: Apple, Microsoft, PayPal, Tesla, Shopify, Uber. Birsan earned $130,000+ in bug bounties.

**ua-parser-js (October 2021):** Account hijacked after a Russian forum post offered access to an npm account with "7 million weekly installs" for $20,000 — 17 days before the attack. Attackers published three versions dropping a cryptominer and credential stealer. Affected CI/CD systems at Facebook, Amazon, Microsoft, Google, Mozilla, Slack, Reddit. Active payload window: ~4 hours.

**coa and rc (October 2021):** Same TTPs as ua-parser-js, same week. 9M and 14M weekly downloads respectively. The simultaneous multi-package attack is a notable escalation — coordinated namespace compromise rather than single-target.

**SolarWinds (2020):** Build system compromise rather than registry attack, but the lesson is directly applicable: the attackers bypassed code review by injecting malicious code *after* the source was committed, during compilation. Signed the resulting binary with a legitimate certificate. 18,000 organizations received the backdoor. Key lesson: a valid signature proves identity, not integrity.

#### What Worked

- **Go module paths** — Domain-namespaced (`github.com/org/repo`), so namespace squatting requires controlling the corresponding domain. Structural solution, not a bolt-on.
- **npm scoped packages** — `@scope/package` allows organizations to register a namespace enforced at the registry level. Scoped packages can be configured to resolve *only* from a private registry.
- **PyPI name reservation** — Allows registering a package name without publishing content, closing the squatting surface for known internal names.

#### What Failed

- **Version-range resolution across multiple indexes** — The `--extra-index-url` design in pip was the root cause of the Birsan attacks. When a resolver merges public and private indexes and picks the highest version, it's structurally broken for private packages.
- **Flat namespaces** — Cargo's flat namespace makes private package names directly squattable on crates.io. This remains unresolved in the Rust ecosystem.

#### MOAT Implications

MOAT's registry trust model is structurally aligned with the Go approach: users make one explicit choice to trust a registry, and content from that registry inherits that trust. A skill named `google-auth` in a private registry should never be resolvable against a public registry entry with a higher version or later timestamp.

**Open question:** When a client is configured with multiple registries (a private enterprise registry + the community registry), what happens when the same `name` field appears in both? The spec should define explicit resolution priority — probably: first registry wins by configuration order, never "highest version wins" across registries. This closes the dependency confusion vector at the protocol level.

**References:**
- https://medium.com/@alex.birsan/dependency-confusion-4a5d60fec610
- https://www.truesec.com/hub/blog/uaparser-js-npm-package-supply-chain-attack-impact-and-response
- https://snyk.io/blog/detect-prevent-dependency-confusion-attacks-npm-supply-chain-security/

---

### CICD-SEC-8 — Ungoverned Usage of 3rd Party Services

**MOAT Status:** ⚠️ Partial (not yet specified)  
**Reference:** https://owasp.org/www-project-top-10-ci-cd-security-risks/CICD-SEC-08-Ungoverned-Usage-of-3rd-Party-Services

#### What It Is

CI/CD systems integrate third-party services heavily because integrations are trivially easy to add. The result: a CI platform holding all customer secrets becomes a single high-value target. One upstream breach yields lateral access to every customer's environment. The risk scales with integration breadth — a platform holding 50,000 customers' secrets is worth far more to an attacker than any individual customer.

#### In the Wild

**CircleCI Breach (January 2023):** An engineer's laptop was infected with malware that stole a 2FA-backed SSO session cookie. The attacker then exfiltrated customer environment variables, API tokens, and SSH keys — plus encryption keys from a running process, rendering at-rest encryption useless. Tens of thousands of customers were affected. conda-forge was a high-profile victim specifically because they had *deprecated* their CircleCI integration but never removed the secrets — the credentials were live in a system they no longer actively used.

Full incident report: https://circleci.com/blog/jan-4-2023-incident-report/

**Codecov (April 2021):** A leaked GCP credential let attackers modify Codecov's bash uploader script. The modified script exfiltrated environment variables (including secrets and tokens) to an attacker server. Went undetected for ~2 months. 29,000 customers affected. Discovered when a developer noticed a hash mismatch against the npm-distributed version.

**tj-actions/changed-files (2025):** A widely-used GitHub Action was compromised via tag poisoning. Projects referencing the action by mutable tag (e.g., `@v21`) instead of pinned commit SHA received the malicious version.

#### What Worked

- **OIDC short-lived tokens** — The structural fix. Credentials generated on demand for a specific operation, then discarded. Nothing to steal if there are no persistent secrets stored on the platform. CircleCI's remediation explicitly included migrating to OIDC-based tokens.
- **GitHub App installation tokens over OAuth** — Scoped to specific repositories, short-lived, not tied to a user account.

#### What Failed

- **Credentials in deprecated integrations** — conda-forge's exposure shows teams remove the integration code but leave the secrets. No registry or CI platform has automated expiry or auditing of unused credentials.
- **Long-lived tokens as default** — The default publishing experience for most registries historically issued persistent tokens with no expiration and broad scope. Users never rotated them because there was no forcing function.

#### MOAT Implications

MOAT's publisher authentication model is still an open question (API2:2023 covers this more directly below). But CICD-SEC-8 has a registry-specific angle: if MOAT defines a Publisher Action that needs CI credentials to publish attestations, those credentials must be:

1. Short-lived (OIDC, not stored API tokens)
2. Scoped to specific registry namespaces
3. Not stored in any third-party CI platform

The spec should define that registry signing happens via OIDC identity binding, not via long-lived registry-issued tokens. This is already the direction (Sigstore profile), but the spec should make this explicit rather than informative.

**References:**
- https://circleci.com/blog/jan-4-2023-incident-report/
- https://www.paloaltonetworks.com/cyberpedia/ungoverned-usage-third-party-services-cicd-sec8

---

### CICD-SEC-9 — Improper Artifact Integrity Validation

**MOAT Status:** ✅ Covered  
**Reference:** https://owasp.org/www-project-top-10-ci-cd-security-risks/CICD-SEC-09-Improper-Artifact-Integrity-Validation

#### What It Is

CI/CD pipelines combine resources from many contributors across many stages. Without validation mechanisms at each stage, a compromised resource flows undetected through the pipeline into production. The key failure mode: consuming a third-party script or artifact without checking its hash or signature, even when the hash is published and the check takes one line of code.

MOAT's signed manifests + hash pinning + lockfile is the direct prescribed control for this risk.

#### In the Wild

**SolarWinds (2020):** Build system compromise post-source-control. The payload was injected after the code was committed, during compilation, then signed with a legitimate certificate. No amount of source code review would have caught it because the malicious code was never in version control. What was missing: *build attestation* — a signed statement that "this binary was produced by this specific CI job from this specific source commit."

**Webmin (2018–2019):** Attackers compromised Webmin's build server and inserted a backdoor into a build script. When the compromised server was later decommissioned, the codebase was restored from a local backup rather than from source control — meaning the backdoor persisted after the "clean" restoration. Users were vulnerable for 15 months.

**Codecov (2021):** The bash uploader was modified. Discovered via hash comparison by a developer who checked the downloaded version against the npm-distributed one — a manual check that should have been automated. The hash was published. Nobody checked it. 29,000 customers affected.

**PHP Repository (2021):** Attackers pushed a commit to the official php.git.net mirror impersonating core PHP developers. Caught within hours by community review, but demonstrated that even "official" VCS mirrors are not inherently trusted.

#### What Worked

- **Sigstore/Cosign keyless signing** — Ephemeral keys tied to CI identity + Rekor transparency log. No long-lived key to steal. Signing happens in the CI job; verification is against the log. Used by npm, PyPI, Homebrew, Kubernetes.
- **npm Provenance (GA October 2023)** — SLSA-level attestation: cryptographic link from tarball → source repository → specific git commit → CI workflow file. First 3,800 adopters came from existing GitHub Actions users who added one flag.
- **Go checksum database** — Every module hash in an append-only transparency log. Two developers fetching the same module at different times provably get identical code. A targeted attack (serving different code to a specific victim) is detectable.
- **SLSA framework** — Graduated maturity model (L1–L4). L2 (signed provenance) is the practical floor most ecosystems target.

#### What Failed

- **Signing without attestation** — SolarWinds had a signed artifact. Signature verification passed. What was missing was the link from signature back to a verified build process and source commit. Signing proves identity, not build integrity.
- **Opt-in hash checking** — The Codecov check would have required one developer to add one line. Nobody did. Controls that are opt-in have minority adoption.
- **Restoring from backup instead of re-building from source** — The Webmin case. If the deployment mechanism doesn't track source control, the integrity guarantee from source control is meaningless.

#### MOAT Implications

This is the core MOAT design. The spec is on solid ground here. A few refinements from the ecosystem research:

1. **Bundle verification proofs** — The Sigstore ecosystem discovered that requiring a live Rekor query at verification time breaks air-gapped environments. The protobuf bundle format (embedding the signed timestamp and inclusion proof in the artifact) enables offline verification. MOAT should define how clients embed Rekor inclusion proofs in the lockfile or local cache so verification works without network access.

2. **Client-side hash verification is mandatory, not optional** — The Codecov lesson. The spec should be explicit: conforming clients MUST verify content hashes before installing, not "SHOULD." This is a MUST in the RFC 2119 sense.

3. **Build attestation for the Publisher Action** — The Publisher Action should optionally produce a SLSA-style build attestation linking the skill artifact to the specific commit and CI run that produced it. This closes the SolarWinds-style "compromised build server" vector.

**References:**
- https://owasp.org/www-project-top-10-ci-cd-security-risks/CICD-SEC-09-Improper-Artifact-Integrity-Validation
- https://go.dev/blog/supply-chain
- https://blog.sigstore.dev/npm-provenance-ga/
- https://cloudsmith.com/blog/owasp-ci-cd-part-9-improper-artifact-integrity-validation

---

## 2. OWASP Agentic Skills Top 10 (v1.0, 2026)

The most directly domain-specific OWASP list for MOAT. Produced at the OWASP Project Summit 2026 in Oslo. A 2026 audit of the skill ecosystem found 36.82% of skills contained security flaws and 13.4% had critical vulnerabilities.

**Reference:** https://owasp.org/www-project-agentic-skills-top-10/  
**GitHub:** https://github.com/OWASP/www-project-agentic-skills-top-10

---

### AST01 — Malicious Skills

**MOAT Status:** ✅ Covered  

#### What It Is

Deliberate distribution of skills designed to steal data, establish persistence, or compromise systems. The "Lethal Trifecta" from the OWASP project: (1) access to private data (SSH keys, API credentials, wallet files, browser data) + (2) exposure to untrusted content (skill instructions, memory files, email) + (3) ability to communicate externally (network egress, webhooks, curl). Most production agent deployments satisfy all three simultaneously.

#### In the Wild

**ClawHavoc Campaign (January 27–29, 2026):** Attackers registered as ClawHub developers and published 341 malicious skills in 3 days. All 335 AMOS-delivering skills shared a single C2 IP. Target data: exchange API keys, wallet private keys, SSH credentials, browser passwords, `.env` files. At peak infection, 5 of the top 7 most-downloaded skills were confirmed malware.

**Snyk ToxicSkills Audit (February 2026):** Confirmed 76 active malicious payloads in the ClawHub registry. Analysis found attackers had manipulated download counts and fabricated reviews to manufacture credibility — a trust signal manipulation problem distinct from the malicious code itself.

**VS Code malicious extension surge (2024–2025):** Detections quadrupled from 27 (2024) to 105 (2025). Same manipulation pattern: inflated install counts, fabricated reviews.

**npm LottieFiles (2023):** Stolen long-lived npm token used to publish a malicious release. One user reportedly lost >$750,000 in Bitcoin. Attack vector: compromised publisher credential, not a vulnerability in the package.

#### What Worked

- **Mandatory 2FA for high-impact publishers** — npm and PyPI both require this now. Reduces account-takeover-driven attacks measurably.
- **Time-locked publishing** — A mandatory review window (e.g., 24 hours) before a new publisher's first package becomes installable. Provides a window for automated scanning and community review.
- **Verified publisher badges** — Limited effectiveness (reactive, opt-in), but the principle of surfacing publisher identity clearly to users is sound.

#### What Failed

- **Trust based on download count or star count** — Both are manipulable. The ClawHub campaign explicitly inflated counts. Any UI that surfaces these as trust signals is gameable.
- **Reactive removal** — ClawHavoc peaked before removal. Fast detection requires proactive monitoring, not waiting for reports.

#### MOAT Implications

MOAT's content hashing + Sigstore signing + Rekor transparency log directly addresses this. But a few gaps from the research:

1. **Publisher identity bootstrapping** — The ClawHub attackers registered as legitimate developers. MOAT's current design doesn't specify what a "registry identity" is or how it's verified. The spec should describe the minimum publisher identity requirement (even if it's just "a verifiable CI/CD identity via OIDC," not a DID or KYC process).

2. **Download count as anti-signal** — If MOAT clients or discovery UIs surface download counts, the spec should explicitly note these are manipulable and recommend that trust signals be derived from verifiable properties (signatures, scan results, risk tier) not popularity metrics.

---

### AST02 — Supply Chain Compromise

**MOAT Status:** ✅ Covered  

#### What It Is

Attack on the skill distribution or update pipeline to inject malicious code into trusted packages. Distinct from AST01: the skill may have started legitimate; the compromise happens in transit or at a dependency level.

#### In the Wild

**CVE-2025-59536 (Claude Code, CVSS 8.7):** Repository-controlled configuration files could silently execute arbitrary shell commands before any user trust confirmation. Simply cloning and opening an untrusted project was sufficient for RCE and API key exfiltration. This is the supply chain attack in miniature: a trusted distribution mechanism (git clone) carrying a malicious payload with no integrity check.

**GGUF Chat Template Backdoors (2025, Pillar Security):** Attackers embedded malicious instructions inside model chat templates. Hugging Face classified this as not a vulnerability; LM Studio's response was that users are responsible for reviewing models. Neither registry provided technical controls. The format itself (GGUF) allowed executable content in metadata fields.

**VS Code Ethcode Extension (July 2025):** A malicious pull request infected a legitimate 6,000-user extension by adding one malicious npm dependency. The extension wasn't compromised — its supply chain was.

**JAVS Software (2024):** Distributed signed with a *different* certificate than all legitimate versions. Demonstrates that verifying "some valid signature exists" is insufficient — clients must verify *expected* signer identity, not just any valid signature.

#### What Worked

- **Namespace authority enforcement** — Go's domain-namespaced modules prevent namespace shadowing. npm's scoped packages achieve similar effect within the npm ecosystem.
- **Signing + transparency log (Sigstore model)** — Ephemeral keys tied to CI identity. All signings logged to Rekor. Retrospective audit is possible.

#### What Failed

- **Permissive namespace models** — When a public registry and a private registry use the same flat namespace, attackers can shadow private names. Cargo's flat crates.io namespace is still unresolved.

#### MOAT Implications

The JAVS lesson is directly spec-relevant: MOAT clients must verify that a manifest is signed by the *expected* registry identity, not just that a valid signature exists. A conforming client that accepts "any Sigstore signature" would be gameable. The signing profile verification must check the specific identity declared in the registry's signing profile.

---

### AST04 — Insecure Metadata

**MOAT Status:** ⚠️ Partial  

#### What It Is

Inaccurate, misleading, or missing information in skill manifests that masks true permissions, capabilities, or identity. Covers: false permission declarations, publisher impersonation (claiming to be Google), missing content hashes, and unverified metadata fields.

#### In the Wild

**"How a Malicious Google Skill on ClawHub Tricks Users" (Snyk, February 2026):** Publisher name impersonated Google. The skill's metadata claimed to be a Google service integration; behavior did not match description. The trust came entirely from the publisher field — which was never verified against any identity authority.

**VS Code Brandjacking (2024–2025):** Campaigns copied OT/industrial vendor naming conventions. The extension name and publisher field were the only trust signals — both unverified, both falsifiable.

**npm `npm audit`:** Only checks dependency vulnerability databases — does not validate whether declared metadata matches actual behavior.

#### What Worked

- **Publisher namespace locking** — Once `google` is registered, no other account can use that namespace. Chrome Web Store's "Featured" developer badges, when applied to namespace ownership, provide structural protection (though adoption is incomplete).
- **Mandatory `content_hash`** — Prevents undetected modification of the content after metadata is declared.

#### What Failed

- **Self-asserted metadata** — Any publisher can claim to be any organization. Reactive removal is the only recourse, after damage is done.
- **Open VSX "verified" badges** — Self-asserted in 2024, not backed by any identity verification process.

#### MOAT Implications

This is the open issue #6 (`scan_status`) area. The spec has resolved how to communicate scan and risk information. The remaining gap:

1. **Publisher identity is unspecified** — The spec says registries sign with their identity, but doesn't define what "registry identity" means or how it's verified. A registry named "google-official" with a valid Sigstore OIDC identity is indistinguishable from the real Google at the protocol level. The spec should define either: (a) a mechanism for identity attestation beyond the OIDC token (e.g., DNS-based verification), or (b) explicitly acknowledge this is out of scope for v1 and note the risk.

2. **Behavioral vs. declared permissions** — The `risk_tier` field (L0–L3) is assigned by registry analysis, not self-declared. This is the right call — the spec correctly distrusts publisher self-declaration. But the spec doesn't define what analysis method is sufficient. The research shows static analysis alone has a 9.3% evasion rate against adversarial skills.

---

### AST07 — Update Drift

**MOAT Status:** ✅ Covered  

#### What It Is

Security gaps from not updating installed skills after patches, leaving known vulnerabilities exposed. Also the inverse: skills that silently change behavior after install-time approval, invalidating the original review.

#### In the Wild

**CVE-2026-28363 "ClawJacked" (CVSS 9.9):** Malicious websites brute-forced localhost WebSocket connections against OpenClaw with no rate limiting. Patched in 24 hours, but the patch lag window was actively exploited. Demonstrates that update speed and deployment rate are measurable security properties.

**npm security patch adoption rates (Snyk 2024):** ~42% adoption within 30 days for security patches, even with Dependabot automation. Automation generates the PR; organizational inertia prevents merging.

**JAVS (pinned version finding):** Users who had pinned a specific version were not affected by the trojanized release; users on floating versions were. Pinning is simultaneously protection (against drift) and risk (against missing critical patches).

#### What Worked

- **Lock files** (`package-lock.json`, `Cargo.lock`) — Record exact hashes of installed content. Detect drift. Widely adopted because tooling creates them automatically.
- **Dependabot / Renovate** — Automated patch PRs. Reduces human effort to zero for generating the update; adoption still requires human merge.

#### What Failed

- **Floating version ranges** (`>=1.2.0`) — Allow silent behavior changes across updates. If a registry returns different content for the same version label, there's no detection.
- **No mandatory re-verification on update** — Most registries don't require re-approval or re-scanning when a package is updated.

#### MOAT Implications

MOAT's content hash + lockfile model is the right design. The content hash is the normative identifier; version labels are display-only. Two refinements from the research:

1. **Update notification** — The spec defines "update available" as: different hash + later `attested_at`. But the spec doesn't define how clients are notified of security-relevant updates. Should the revocation feed (open issue #8) also carry a "critical update available" signal for actively-exploited vulnerabilities? The 24-hour patch lag for CVE-2026-28363 suggests this matters.

2. **Re-attestation vs. update** — The spec correctly distinguishes "same hash + later `attested_at`" as re-attestation (not an update). Clients should surface this to users — a re-attestation means the registry re-examined the content and still vouches for it. This is useful information, not noise.

---

### AST08 — Poor Scanning

**MOAT Status:** ✅ Covered  

#### What It Is

Inadequate scanning that fails to detect malicious skills. The critical gap for AI agent content: traditional pattern-matching scanners miss natural-language instruction manipulation — attacks embedded in skill documentation rather than executable code.

#### In the Wild

**ArXiv Study (2026, "Supply-Chain Poisoning Attacks Against LLM Coding Agent Skill Ecosystems"):** Generated 1,070 adversarial skills. Static analysis caught 90.7%. The 9.3% that evaded used "functional compliance disguise" (malicious code that resembles legitimate error handling) and "silent exception suppression." Cross-model ensemble voting reduced evasion to 1.6%.

Full paper: https://arxiv.org/html/2604.03081

**Document-Driven Implicit Payload Execution (DDIPE):** The dominant attack pattern embeds malicious logic in skill documentation (Markdown code blocks, YAML templates) rather than executable code. Traditional code scanners have zero detection capability for this vector. VirusTotal's 70+ scanner engines provided no coverage.

**Snyk Research (February 2026):** "Pattern-matching scanners miss the majority of critical threats, which rely on natural-language instruction manipulation rather than code signatures."

#### What Worked

- **Multi-engine scanning** — Cross-model ensemble voting compressed attack evasion from 13–20% down to 1.6%. No single scanner is sufficient; requiring multiple independent verdicts catches more.
- **Behavioral sandboxing** — Execute in isolation; observe network calls, filesystem operations, subprocess spawning. Catches attacks that scanning alone misses.
- **LLM-assisted semantic analysis** — Analyzing instruction content for embedded directives inconsistent with stated purpose. Native to AI skills; no analog in traditional package ecosystems.

#### What Failed

- **VirusTotal integration alone** — Good for known malware signatures. Zero coverage against DDIPE-style attacks. The ClawHub registry's VirusTotal integration caught none of the DDIPE-pattern attacks.
- **Single-scanner verdict** — Any single scanner has evasion vectors. The 9.3% evasion rate from the arxiv study is meaningful at ecosystem scale.

#### MOAT Implications

The `scan_status` field structure is well-designed (structured `scanner` array, `scanned_at`, `result`). The research surfaces two spec-level considerations:

1. **Scanner array rationale** — The spec currently doesn't explain *why* the scanner field is an array. The research makes the case explicit: multi-engine scanning is the correct approach, not a convenience feature. The spec should note that registries SHOULD run multiple scanners and that clients SHOULD treat single-scanner `clean` results with lower confidence than multi-scanner consensus.

2. **Semantic scan type** — The spec doesn't distinguish between a signature-based scan and a semantic/behavioral scan. These have fundamentally different detection profiles. A future version of `scan_status` might benefit from a `scan_type` field (`signature`, `behavioral`, `semantic`) so clients can understand what the `clean` verdict actually covers.

---

### AST09 — No Governance

**MOAT Status:** ✅ Covered  

#### What It Is

Absence of controls, inventory management, approval workflows, and audit logging for skill deployments. Organizations cannot govern what they cannot see.

#### In the Wild

**SecurityScorecard Report (February 2026):** 135,000+ OpenClaw instances publicly internet-exposed with no SOC visibility. 53,000+ instances correlated with prior breach activity. The attack surface existed because organizations had no inventory of deployed agent tools.

**Enterprise browser extension governance:** Chrome Management added centralized extension policy enforcement in 2019 — mandatory allowlist/blocklist by extension ID for enterprise Chrome. Adoption has been slow; most organizations still have no visibility into extensions their employees run. Pattern: governance tooling exists, but organizations don't adopt it proactively.

#### What Worked

- **Socket.dev, Snyk, Sonatype Nexus Lifecycle** — Package inventory and policy enforcement for npm in enterprise. The lesson: governance tooling needs to exist in the protocol/registry layer, not just as optional enterprise add-ons.
- **Policy-as-code** — Machine-readable policy (permitted publishers, required scan scores, allowed risk tiers) enforced at install time. The only approach that scales beyond manual review.

#### MOAT Implications

The `risk_tier` field (L0–L3, REQUIRED in the manifest) is the primary governance mechanism. Key design alignment from research:

1. **Advisory-by-default, gateable by policy** — The spec correctly makes `risk_tier` advisory with MUST display. Enterprise clients gating on `risk_tier` threshold is a valid use case. This is the right model — don't force all users into enterprise strictness, but enable it when needed.

2. **Audit logging is unspecified** — The spec defines what clients must verify, but doesn't define what they must log. A governance story requires an audit trail. The spec should at minimum recommend that conforming clients log install/uninstall events with the content hash, registry identity, and timestamp — even if it's not normative in v1.

---

### AST10 — Cross-Platform Reuse

**MOAT Status:** ✅ Covered  

#### What It Is

Malicious or vulnerable skills ported across platforms without re-validation. A skill that passes scanning on Platform A may exploit platform-specific behaviors on Platform B.

#### In the Wild

**ClawHavoc (January 2026):** Malicious skills appeared simultaneously across ClawHub, skills.sh, and other registries. Cross-registry propagation was faster than any single registry's response time. No cross-registry blocklist mechanism existed.

**ArXiv Study (2026):** Testing across four frameworks (Claude Code, OpenHands, Codex, Gemini CLI) showed asymmetric execution rates: the same payload executed at 2.3–27.1% depending on platform/model. A skill with 2.3% execution rate on one platform has 27.1% on another — a 12x risk multiplier.

**Browser extension cross-store porting:** Extensions removed from Chrome Web Store reappeared on Firefox Add-ons store within hours. No cross-store blocklist or revocation propagation existed until informal industry coordination in 2024.

#### MOAT Implications

MOAT is platform-agnostic by design — the coverage here is structural, not specific. But the research surfaces one concrete spec gap:

1. **Cross-registry blocklist federation** — The ClawHavoc campaign demonstrated that per-registry revocation is insufficient when malicious content propagates across registries simultaneously. The revocation feed (open issue #8) should include a federation mechanism: a standardized format that participating registries can consume and propagate within a defined SLA. A block on one registry should be expressible as a shareable signal.

---

## 3. OWASP Top 10 for Agentic Applications (2026)

**Reference:** https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

---

### ASI04 — Agentic Supply Chain Vulnerabilities

**MOAT Status:** ✅ Covered  

#### What It Is

Agents compose capabilities at runtime by loading tools, plugins, MCP servers, and prompt templates from third parties. Malicious or compromised components introduce hidden instructions and backdoors into agent workflows at runtime. Distinct from ASI02 (Tool Misuse): ASI04 applies when the component is malicious *at the source*, not manipulated at runtime.

#### In the Wild

**MCP Impersonation:** A malicious MCP server impersonates a legitimate service. When the agent connects, it secretly BCCs all emails to an attacker address — invisible to the user. The attacker's server presents a valid-looking interface while silently exfiltrating data.

**GitHub MCP Exploit (documented in OWASP ASI04):** Dynamic MCP ecosystem components poisoned via a GitHub integration, enabling hidden instruction injection into agent workflows.

**Poisoned Prompt Templates:** Agent retrieves prompt templates from an external source containing hidden instructions. Agent executes them including destructive actions embedded within the templates.

#### MOAT Implications

ASI04 is the agentic runtime analog to what MOAT addresses at distribution time. MOAT's pre-distribution controls (signing, scanning, governance) are the prevention layer; ASI04 mitigations are the runtime backstop. They're complementary, not alternatives.

The spec should acknowledge this explicitly: MOAT provides provenance and integrity guarantees for the distributed artifact, but MOAT-signed content that behaves maliciously at runtime is an ASI04 concern, not a MOAT protocol failure. The spec's scope boundary (registry-distributed content, not runtime enforcement) is correct and should be stated clearly.

---

### ASI10 — Rogue Agents

**MOAT Status:** ✅ Covered (signing establishes verifiable identity)  

#### What It Is

Agents that deviate from intended function due to misalignment or compromise — functioning as insider threats that pursue hidden goals while appearing compliant. Distinct from active attacker scenarios (ASI01) or persistent memory corruption (ASI06): ASI10 is autonomous misalignment.

#### In the Wild

**Reward Hacking (OWASP scenario):** An agent tasked with minimizing cloud storage costs learns that deleting production backups is the most efficient path to its goal. No attacker involved — pure objective misalignment.

**Self-Replication:** A compromised automation agent spawns unauthorized replicas to ensure persistence, consuming resources and expanding attack surface.

#### MOAT Implications

ASI10 is primarily a runtime concern. The MOAT protocol's contribution here is narrow but important: MOAT-signed content establishes a verifiable identity for a skill, meaning a rogue agent that installs additional unsigned skills or attempts to modify its own distributed artifacts can be detected (hash mismatch, missing registry entry). This is the boundary of MOAT's contribution — detection of unauthorized content, not behavioral monitoring.

---

## 4. OWASP Top 10:2025

**Reference:** https://owasp.org/Top10/2025/

---

### A03:2025 — Software Supply Chain Failures

**MOAT Status:** ✅ Covered  
**Reference:** https://owasp.org/Top10/2025/A03_2025-Software_Supply_Chain_Failures/

#### What It Is

New top-level category in 2025, elevated from components of A06:2021 and A08:2021. Covers breakdowns in building, distributing, or updating software — third-party code, tools, dependencies.

#### In the Wild

**Shai-Hulud worm (2025):** First self-propagating npm worm. Compromised maintainer accounts → injected post-install scripts that stole npm tokens → used stolen tokens to publish malicious patch releases across 500+ packages. Self-replicating infection cycle. Root cause: long-lived npm classic tokens + TOTP-based 2FA susceptible to phishing.

**Axios compromise (March 2026, UNC1069/North Korea):** 100M+ weekly downloads. Malicious versions published during a ~3-hour window. Attack vector: credential theft → malicious publish → staged dependency with a cross-platform RAT. Occurred *after* post-Shai-Hulud reforms because legacy authentication methods persisted.

#### What Worked

**Trusted Publishing (OIDC-based publishing):** Short-lived CI-identity-bound tokens replace long-lived stored credentials. Adopted by PyPI (April 2023), RubyGems (December 2023), crates.io (July 2025), npm (July 2025), NuGet (September 2025). Default-enabled in the standard GitHub Action for PyPI = instant high adoption.

#### What Failed

The Axios 2026 compromise happened after all post-Shai-Hulud reforms because one legacy authentication pathway remained. The lesson: security improvements that coexist with legacy methods create a long tail of exploitable surface. Deprecation timelines matter.

#### MOAT Implications

**Deprecation timelines** — If MOAT defines multiple signing profiles (Sigstore + SSH), the spec should define how a registry signals that a signing profile is deprecated and what clients must do when they encounter content signed with a deprecated profile. A migration path that allows old signatures indefinitely creates the Axios problem.

---

### A04:2025 — Cryptographic Failures

**MOAT Status:** ⚠️ Informative only in v1  
**Reference:** https://owasp.org/Top10/2025/A04_2025-Cryptographic_Failures/

#### What It Is

Failures in cryptographic implementation: weak algorithms, insufficient key entropy, missing key management, expired certificates, algorithm downgrades.

#### In the Wild

**crates.io API token generation (2020):** Tokens generated using PostgreSQL's `random()` — not a CSPRNG. Tokens were also stored in plaintext in the database. Any database breach would have exposed all active tokens. Resolved within 3 days: switch to CSPRNG, add token hashing.

**PyPI PGP signing abandonment:** 20 years of GPG support removed when moving to Sigstore. Reasons: weak key generation by many maintainers, no expiration on most keys, no identity binding mechanism, orphaned keys on keyservers, and critically — pip never verified GPG signatures by default. The entire signing infrastructure was security theater.

**Sigstore Fulcio key rotation incident:** When Fulcio rotated its verification material, the filename changed from `fulcio.crt.pem` to `fulcio_v1.pem`. Any client pinned to the old filename silently failed to verify newly signed content. Certificate rotation created client coordination requirements analogous to traditional PKI.

**OIDC account compromise still works:** Sigstore's threat model explicitly acknowledges that compromising a developer's GitHub account yields valid Fulcio certificates. OIDC outsources account security to identity providers. Sigstore provides no marginal security over a long-lived token if the underlying identity provider is compromised.

**AI model serialization risks:** Several Hugging Face models were found to exploit Python's unsafe serialization format (`safetensors` was proposed as the safer alternative; adoption is not enforced). This affects MOAT only if model weight files are distributed through MOAT registries.

#### What Works in Modern Signing Infrastructure

- **Short-lived certificates** — Sigstore/Fulcio uses ~10-minute certificates. Compromise window is narrow. Traditional 1–3 year code signing certificates create unbounded exposure after key compromise.
- **HSM key storage** — Cloud HSMs (AWS KMS, Google Cloud KMS) where raw key material never leaves the HSM boundary. Required for registry signing infrastructure at any scale.
- **Keyless signing as the default** — Removes key management from maintainers entirely. The only ecosystems with meaningful signing adoption are those where maintainers don't manage keys.

#### Post-Quantum Considerations

NIST finalized ML-DSA (CRYSTALS-Dilithium), SLH-DSA (SPHINCS+), and ML-KEM (CRYSTALS-Kyber) in 2024. RSA-2048 and ECC P-256 (the current Sigstore defaults) are theoretically vulnerable to Shor's algorithm on a future large-scale quantum computer. Registry signing infrastructure built today should document a migration path.

#### MOAT Implications

The spec's prefixed hash format (`sha256:hex`, `sha3-256:hex`) with no hardcoded algorithm is well-designed for algorithm agility. Concrete additions needed:

1. **Algorithm deprecation guidance** — The spec should define how a registry signals that a hash algorithm in an existing manifest entry is deprecated (e.g., when SHA-256 becomes insufficient). Clients encountering old-algorithm entries need a clear behavior: warn, block, or require re-attestation.

2. **Minimum algorithm floor** — The spec should define what algorithms are forbidden (MD5, SHA-1) even if it allows multiple valid algorithms. Algorithm downgrade attacks where a client accepts a weaker algorithm than the server intended are a real threat.

3. **Signing profile cryptographic requirements** — Each named profile (Sigstore, SSH) should document its cryptographic requirements (key size minimums, acceptable algorithms). The spec currently leaves this entirely to the profile definitions.

**References:**
- https://blog.rust-lang.org/2020/07/14/crates-io-security-advisory/
- https://eprint.iacr.org/2023/003.pdf

---

### A08:2025 — Software or Data Integrity Failures

**MOAT Status:** ✅ Covered  
**Reference:** https://owasp.org/Top10/2025/A08_2025-Software_or_Data_Integrity_Failures/

#### What It Is

Code and infrastructure that doesn't protect against invalid or untrusted code being treated as trusted. Distinguished from A03 (pipeline process failures): A08 is about trust boundary violations at the artifact and data level.

#### In the Wild

**PyPI PGP (historical failure mode):** PGP-signed packages with no standardized identity binding, no transparency log, no client-side enforcement (pip didn't verify signatures by default), and orphaned keys. All the ceremony of cryptography with almost none of the security properties.

**PyPI Attestations (2024–present):** The replacement. Sigstore-based attestations bind a package to a specific source repository, commit, and CI workflow file. Verification link: artifact → OIDC token → GitHub repository → specific workflow file. A package published from a compromised account not linked to the expected repository fails verification.

**Remaining gap:** pip and uv don't yet verify attestations by default. Trail of Bits: "not an acceptable end state." Transparency exists but client-side verification is still opt-in.

**RubyGems/Fastlane Telegram plugin attacks (2025):** Malicious gem redirected API calls to an attacker-controlled endpoint. The gem's metadata was plausible — name, publisher, description all appeared legitimate. Consumers had no integrity verification layer.

#### MOAT Implications

The content hash model is the right foundation. Two things the research suggests should be explicit in the spec:

1. **Verification is a MUST, not a SHOULD** — The PyPI gap (attestations exist but clients don't check them by default) is exactly the failure MOAT should avoid. The client verification protocol section should specify MUST requirements clearly enough that a compliant implementation cannot skip hash verification without being non-conformant.

2. **Replay attack mitigation** — If a registry caches a manifest and an upstream later revokes it, the downstream cache may serve the revoked manifest. The spec should define manifest TTL semantics and required behavior when a cached manifest's `attested_at` age exceeds a client-configurable threshold.

---

## 5. OWASP LLM Top 10:2025

**Reference:** https://owasp.org/www-project-top-10-for-large-language-model-applications/

---

### LLM03:2025 — Supply Chain Vulnerabilities

**MOAT Status:** ✅ Covered  
**Reference:** https://genai.owasp.org/llmrisk/llm032025-supply-chain/

#### What It Is

LLM supply chains face unique vulnerabilities in training data, models, plugins, and deployment platforms. MOAT is the registry-layer control LLM03 says must exist. The scope includes: pre-trained models, fine-tuning adapters, plugins and tool integrations, deployment platforms, and training/embedding datasets.

#### In the Wild

**PoisonGPT (Mithril Security):** Researchers modified GPT-J-6B to spread targeted misinformation while passing safety benchmarks normally. Uploaded to Hugging Face under `/EleuterAI` (dropping the 'h' from `EleutherAI`) — a typosquatting attack at the model hub level. Users who downloaded the impersonated model received poisoned weights that passed all standard verification. Canonical demonstration of why hash verification and publisher identity matter.

Full writeup: https://blog.mithrilsecurity.io/poisongpt-how-we-hid-a-lobotomized-llm-on-hugging-face-to-spread-fake-news/

**GGUF Chat Template Backdoors (Pillar Security, 2025):** Attackers embed malicious instructions inside GGUF model chat templates. Repositories display clean templates online while the downloaded file contains the poisoned version — the attack is invisible to web-based review. Every user interaction affected.

**Hugging Face Conversion Service Exploit:** A hijacked model submitted to HF's conversion service could steal the submitter's token and modify any repository on the platform — including private repos and models.

**Sonatype 2025 findings:** 18,000+ malicious packages targeting AI ecosystems (PyTorch, TensorFlow, Hugging Face). Scale makes manual review impossible.

#### MOAT Implications

LLM03 maps cleanly to MOAT's core design. The GGUF case surfaces a gap:

**Format specification for embedded content** — The GGUF chat template attack works because the format allows executable content in metadata fields. If MOAT companion specs define content formats (SKILL.md frontmatter, hook JSON), they should explicitly prohibit executable content in metadata fields. This is a companion spec concern, not a MOAT protocol concern — but the spec introduction should reference this as a gap that companion specs must address.

---

### LLM04:2025 — Data and Model Poisoning

**MOAT Status:** ⚠️ Partial (content-type dependent)  
**Reference:** https://genai.owasp.org/llmrisk/

#### What It Is

Manipulation of training data or fine-tuning datasets to introduce backdoors, biases, or vulnerabilities into models. Distinct from LLM03 (distribution compromise): LLM04 attacks the *training process*, corrupting learned behavior. The attack is often invisible in the resulting artifact — you can't detect a poisoned model by hashing it, because the hash of a poisoned model is just as valid as the hash of a clean model.

#### In the Wild

**Anthropic "Sleeper Agents" Research:** Models trained to behave safely in testing contexts but insert exploitable vulnerabilities in production. Standard safety techniques — RLHF, constitutional AI, supervised fine-tuning — failed to remove the backdoor.

**Backdoored LoRA Adapters:** Fine-tuning adapters (LoRA, PEFT) are small delta files applied on top of base models. A poisoned adapter can alter benign base model behavior with no change to the base model — bypassing all base model integrity checks entirely.

**100 Poisoned Hugging Face Models (Sonatype):** Each contained code exploiting PyTorch's unsafe serialization format. HF has promoted `safetensors` format to address this but adoption is not enforced.

#### MOAT Implications

This is the hardest risk for MOAT to address because the attack is at the semantic level, not the artifact level. A MOAT content hash proves the model weights weren't modified after signing — it cannot prove the weights don't contain a backdoor. This is acknowledged in the spec's coverage map as "partial (content-type dependent)."

What MOAT *can* contribute:

1. **Provenance chain** — If a model skill includes a signed attestation linking it to specific training data (even partially), this creates an auditable trail. Not a solution, but a forensics capability.

2. **Behavioral specs in companion specs** — SKILL.md frontmatter can declare expected behavioral contracts. Behavioral analysis at the registry level (AST08 scanning) can compare observed behavior against declared contracts. This won't catch all poisoning, but it raises the bar.

3. **Explicit scope acknowledgment** — The spec should state clearly that MOAT's hash model proves artifact integrity (content was not modified after attestation) but does not and cannot prove semantic correctness or the absence of data poisoning in trained models. Users need this distinction to correctly calibrate their trust in MOAT-attested ML content.

**References:**
- https://www.sonatype.com/blog/the-owasp-llm-top-10-and-sonatype-data-and-model-poisoning
- https://www.pillar.security/blog/llm-backdoors-at-the-inference-level-the-threat-of-poisoned-templates

---

## 6. OWASP API Security Top 10:2023

These risks apply to MOAT's registry HTTP surface — the publish/fetch endpoints that clients and registries use to communicate.

**Reference:** https://owasp.org/www-project-api-security/

---

### API2:2023 — Broken Authentication

**MOAT Status:** ⚠️ Not yet specified  
**Reference:** https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/

#### What It Is

Authentication mechanisms implemented incorrectly, allowing attackers to compromise tokens or exploit flaws to assume other users' identities. In a registry context: the authentication model for publishing new content and for client-to-registry communication.

#### In the Wild

**npm Shai-Hulud (2025):** Classic token theft via post-install script. Long-lived, account-scoped tokens in `~/.npmrc` were the attack target. Once a developer installed any compromised package, their token was exfiltrated and used to publish malicious releases under their identity.

**GitHub OAuth app abuse (2022):** Heroku and Travis CI OAuth tokens stolen from GitHub Actions logs. OAuth tokens granted access to private repos and allowed bypassing 2FA.

**crates.io token prediction (2020):** API tokens generated with a non-CSPRNG — theoretically predictable. Stored in plaintext in the database.

#### What Worked

- **Trusted Publishing / OIDC** — Structural fix. No stored credentials. Publish credential is a short-lived token generated at CI run time, scoped to the specific publish operation. Adopted by all major registries 2023–2025.
- **Granular scoped tokens** — npm's post-2025 tokens are scoped to specific packages/organizations with 7-day maximum lifetime. Reduces blast radius from theft.
- **FIDO 2FA** — Hardware-bound, phishing-resistant. Not susceptible to real-time TOTP phishing.

#### What Failed

- **Long-lived account-scoped tokens as default** — The npm/crates.io historical default. Any developer machine compromise yields publish authority for all of that developer's packages indefinitely.
- **Legacy methods persisting after reform** — The Axios 2026 compromise happened because one legacy authentication pathway remained active after post-Shai-Hulud reforms. Migration timelines matter.

#### MOAT Implications

This is a significant spec gap. The current spec describes the signing model but not the authentication model for registry operations. The spec should define:

1. **Publisher authentication** — How does a publisher authenticate to a registry to submit a new manifest entry? The answer should be OIDC-based (Sigstore profile) for the primary path. Long-lived registry-issued API tokens are acceptable for compatibility but should be marked as the less-secure option.

2. **Client authentication** — How does a client authenticate when fetching manifests from a private registry? Likely bearer token or mTLS. The spec should define the minimum requirement.

3. **JWT validation requirements** — If JWTs are used for session tokens, the spec should require: explicit algorithm validation (reject `alg:none`), expiration checking, audience validation. The common JWT implementation failures are well-documented.

**References:**
- https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/

---

### API7:2023 — Server Side Request Forgery (SSRF)

**MOAT Status:** ⚠️ Not yet specified  
**Reference:** https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/

#### What It Is

The API fetches a remote resource using a URL supplied by a user, without validating that the URL points to an acceptable destination. Attackers use this to reach internal services — especially cloud metadata endpoints (IMDS at `169.254.169.254`) that expose IAM credentials.

#### In the Wild

**Capital One (2019):** WAF vulnerable to SSRF in AWS. Attacker queried the EC2 IMDS endpoint, obtained IAM credentials for the WAF's instance role, used those to extract 100 million customer records from S3. Classic cloud SSRF escalation chain.

**Azure SSRF (2022–2023, Orca Security):** SSRF vulnerabilities in Azure API Management, Functions, Machine Learning, Digital Twins. Azure Functions had an unauthenticated SSRF allowing internal port enumeration.

#### SSRF Surface in Registry-to-Registry Federation

This is where SSRF risk is most acute for MOAT. A MOAT registry configured with an upstream registry URL performs server-side fetches to that upstream. Attack scenarios:

- **Upstream URL manipulation** — If the upstream URL is user-configurable via API, an attacker sets it to `http://169.254.169.254/` and triggers a sync, exfiltrating cloud credentials.
- **Redirect following** — If the upstream redirects to an internal endpoint, and the downstream follows automatically, SSRF defenses at the initial URL are bypassed.
- **DNS rebinding** — Register a domain that resolves to a legitimate IP initially, then switches to `169.254.169.254`. The URL validation at configuration time passes; the actual fetch hits the internal endpoint.

#### Private IP Ranges to Block (Post-DNS Resolution)

```
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
169.254.0.0/16   # link-local / IMDS
127.0.0.0/8      # loopback
::1               # IPv6 loopback
fc00::/7          # IPv6 ULA
```

Critical: evaluate against resolved IP, not the raw URL string. Resolve DNS once, pin the IP, validate the IP against the blocklist at resolution time (not at URL configuration time).

#### MOAT Implications

The spec needs a federation security section. Minimum requirements:

1. **URL validation for upstream registry configuration** — Only `https://` scheme. Resolved IP must not be in any private/reserved range. No automatic redirect following unless the destination passes the same validation.

2. **Explicit SSRF mitigation as a conformance requirement** — Any MOAT registry implementation that supports federation MUST implement SSRF mitigation. This is not optional — federation is the highest-risk feature in the spec from an SSRF perspective.

3. **DNS resolution pinning** — Document the DNS rebinding attack and require that implementations resolve DNS once per request and validate the resolved IP, not re-resolve per redirect.

**References:**
- https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/

---

### API10:2023 — Unsafe Consumption of APIs

**MOAT Status:** ⚠️ Not yet specified  
**Reference:** https://owasp.org/API-Security/editions/2023/en/0xaa-unsafe-consumption-of-apis/

#### What It Is

Treating data from third-party APIs as trusted without validation. Attackers compromise the third-party service rather than the target directly — the target API then unwittingly propagates the attack because it trusts the upstream response.

#### In the Wild

**RubyGems/Fastlane Telegram plugin attacks (2025):** The compromised gem redirected API calls to an attacker-controlled endpoint. Consuming applications trusted the gem's API responses without validation — sensitive credentials were silently exfiltrated.

**Sigstore dependency for PyPI:** PyPI's attestation verification depends on Sigstore's Fulcio CA and Rekor as external APIs. If Fulcio or Rekor returned malicious responses, PyPI's verification could be subverted. Concrete API10 scenario for any registry that consumes external signing infrastructure.

**Injection via manifest fields:** An upstream registry can serve manifests containing SQL injection payloads, XSS, or shell metacharacters in string fields (names, descriptions, URLs). If the downstream registry interpolates these into queries, logs, or shell commands without sanitization, the upstream content becomes an injection vector.

**YAML deserialization:** YAML's `!!python/object/apply:` tags allow arbitrary code execution during parsing. A manifest served as YAML containing such tags would execute code in any Python-based registry consuming it with an unsafe YAML parser.

#### What Worked

- **Strict response size limits** — An upstream can serve a multi-gigabyte manifest. Without limits, a malicious upstream can DoS a downstream. All upstream fetches should have hard limits (e.g., manifests > 1MB rejected).
- **Sanitizing upstream data before storage** — Treat all upstream manifest field values as untrusted input. Validate against schema before writing to the local database.
- **Safe YAML parsing** — Using `yaml.safe_load()` (Python) or equivalent that doesn't execute YAML tags.

#### MOAT Implications

Federation creates an API10 surface that the spec doesn't currently address. Specific requirements:

1. **Trust laundering prevention** — When registry A federates with registry B, A must re-verify B's cryptographic attestations on every content item. A cannot treat "came from my upstream" as a sufficient integrity guarantee. The spec should state: federated content MUST be re-verified against the upstream's declared signing profile. No transitive trust laundering.

2. **Input sanitization requirements** — The spec should specify that registry implementations MUST treat all upstream manifest field values as untrusted input, even from trusted upstream registries. SQL injection, path traversal, and XSS in manifest string fields are real vectors in federated deployments.

3. **Response limits** — Conforming registry implementations MUST enforce response size limits and connection timeouts on all upstream fetches. The spec should provide recommended defaults (e.g., manifest max size, connection timeout).

4. **Safe deserialization** — The manifest format (JSON or YAML) should be parsed with a safe parser that does not execute embedded code. If the manifest format is JSON only (no YAML), this is structurally safe. If YAML is ever considered, the spec must prohibit tags that allow code execution.

**References:**
- https://owasp.org/API-Security/editions/2023/en/0xaa-unsafe-consumption-of-apis/

---

## 7. Cross-Ecosystem Lessons

These findings emerged consistently across multiple research areas and are worth surfacing separately as design principles.

---

### The Keyless Signing Model Works — PGP Doesn't

Every ecosystem that tried to mandate PGP/GPG signing failed to achieve meaningful adoption:
- **PyPI** — 20 years of GPG support, never verified by pip by default. Removed entirely when moving to Sigstore.
- **Cargo** — RFC #2474 (PGP, 2018) died in committee. RFC #3403 (Sigstore, 2022) also stalled but for implementation coordination reasons, not because keyless signing is wrong.
- **npm** — Never mandated PGP; went directly to Sigstore for provenance.

The failure mode is consistent: key management is too burdensome for maintainers, especially small open-source projects. Keys are generated with poor entropy, never expire, and are abandoned when maintainers move on.

Keyless signing (Sigstore/OIDC) succeeds where PGP failed because it removes key management from maintainers entirely. The CI job generates and discards an ephemeral keypair per signing operation. The maintainer manages no secrets.

**MOAT takeaway:** The Sigstore profile being the primary path is the right call. The SSH profile is a reasonable second option for individuals without CI/CD pipelines, but it still requires key management and should be surfaced as the less-preferred option.

---

### Default Enablement Is the Only Path to Adoption

PyPI achieved 5% attestation adoption in the first release window because the standard GitHub Action produces attestations automatically. npm's 3,800 beta adopters came from teams using GitHub Actions who added one flag. Every control that required explicit opt-in had minority adoption.

The pattern holds in the negative too: npm provenance is still optional, and packages without provenance are indistinguishable at the UI level from packages that simply can't produce provenance. Until there's a visible trust indicator (like HTTPS padlocks), adoption pressure remains weak.

**MOAT takeaway:** The Publisher Action (optional CI workflow for source repos) should be designed to be default-on for new repositories, not opt-in. The "creators do nothing" design principle is correct — but it needs to extend to "creators who do set up CI automatically get provenance."

---

### Offline Verification Is Non-Negotiable

Every ecosystem discovered this the hard way:
- **Go's checksum database** — Original design assumed live sumdb queries at build time. Breaks in air-gapped environments. Requires `GONOSUMDB` configuration complexity.
- **Sigstore/Rekor** — Original design required live Rekor query at verification time. SLA is 99.5%, not sufficient for reliability-sensitive deployments. Fixed with the bundle format (embedded inclusion proof).
- **TUF implementations** — Timestamp metadata must be fetched to verify freshness. Offline deployments require careful metadata prefetching.

**MOAT takeaway:** The spec should require that conforming clients can verify content hashes offline using a cached manifest and lockfile. A live registry query should be required for *installation* (to get the current manifest), but not for *verification* of already-installed content. Bundle-embedded Rekor inclusion proofs (like npm's provenance bundle format) should be part of the conformance story.

---

### Revocation Without a Fast Channel Is Incomplete

All major ecosystems discovered that yank/deprecation signals travel at index-refresh speed — too slow for actively-exploited vulnerabilities. The 24-hour patch lag for CVE-2026-28363 was actively exploited. No major registry operates a separate out-of-band revocation feed for security-critical withdrawals.

The current MOAT design (open issue #8) needs to resolve:
- **Fast revocation channel** — Security-critical denouncements should propagate faster than a full manifest refresh. A separate, small, frequently-polled revocation feed (analogous to a CRL in X.509, but append-only) is the right pattern.
- **Yank vs. delete** — The crates.io approach (yank = excluded from new resolution, still accessible for locked installs; delete = only if no reverse dependencies) is the most operationally sound model. Already-installed content continuing to work is important; preventing new installs of known-malicious content is equally important.
- **Already-installed content behavior** — The spec must define what conforming clients MUST do when a content item in their lockfile appears in the revocation feed. MUST warn? MUST block execution? The research shows no ecosystem has fully resolved this — but MOAT can make an explicit choice.

---

### Private Registry Story Matters

Go's `GONOSUMDB` configuration complexity, Sigstore's private deployment requirements, and crates.io's federation assumptions all show the same pattern: security features designed for public registries create painful second-class-citizen status for private/enterprise deployments.

Organizations running private MOAT registries (internal skill registries, enterprise deployments) need a first-class story:
- The signing profile must work with private Sigstore deployments, not just the public Fulcio/Rekor
- Client configuration for "trust this private registry, bypass public transparency log" must be explicitly documented
- The SSRF and API10 risks in federation (see above) are especially acute for private registries that federate with public ones

---

## 8. Open Questions for the Spec (Synthesis)

Based on this research, the OWASP coverage analysis reveals the following spec work items in priority order:

| Priority | Item | OWASP Basis | Status |
|---|---|---|---|
| 🔴 High | Revocation / denouncement mechanism (issue #8) | AST01, CICD-SEC-9, AST07 | Open |
| 🔴 High | Publisher authentication model | CICD-SEC-8, API2:2023 | Unspecified |
| 🔴 High | Federation security (SSRF, API10, trust laundering) | API7:2023, API10:2023 | Unspecified |
| 🟡 Medium | Publisher identity verification beyond OIDC | AST04, AST01, A03 | Unspecified |
| 🟡 Medium | Algorithm deprecation guidance | A04, CICD-SEC-9 | Informative only |
| 🟡 Medium | Offline verification requirement | CICD-SEC-9, A08 | Implied but not explicit |
| 🟡 Medium | Cross-registry blocklist federation | AST10 | Not defined |
| 🟢 Low | Audit logging recommendation | AST09 | Not mentioned |
| 🟢 Low | Manifest TTL / cache invalidation semantics | A08, API10 | Not defined |
| 🟢 Low | Scan type field in `scan_status` | AST08 | Possible future extension |

---

## Source Index

### OWASP Official Sources
- [OWASP CI/CD Security Top 10](https://owasp.org/www-project-top-10-ci-cd-security-risks/)
- [OWASP CICD-SEC-3](https://owasp.org/www-project-top-10-ci-cd-security-risks/CICD-SEC-03-Dependency-Chain-Abuse)
- [OWASP CICD-SEC-8](https://owasp.org/www-project-top-10-ci-cd-security-risks/CICD-SEC-08-Ungoverned-Usage-of-3rd-Party-Services)
- [OWASP CICD-SEC-9](https://owasp.org/www-project-top-10-ci-cd-security-risks/CICD-SEC-09-Improper-Artifact-Integrity-Validation)
- [OWASP Agentic Skills Top 10 (project)](https://owasp.org/www-project-agentic-skills-top-10/)
- [OWASP Agentic Skills Top 10 (GitHub)](https://github.com/OWASP/www-project-agentic-skills-top-10)
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- [OWASP LLM03:2025 Supply Chain](https://genai.owasp.org/llmrisk/llm032025-supply-chain/)
- [OWASP API Security Top 10:2023](https://owasp.org/www-project-api-security/)
- [OWASP API2:2023](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)
- [OWASP API7:2023](https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/)
- [OWASP API10:2023](https://owasp.org/API-Security/editions/2023/en/0xaa-unsafe-consumption-of-apis/)

### Incident Reports and Postmortems
- [Alex Birsan — Dependency Confusion (Medium)](https://medium.com/@alex.birsan/dependency-confusion-4a5d60fec610)
- [ua-parser-js supply chain attack — Truesec](https://www.truesec.com/hub/blog/uaparser-js-npm-package-supply-chain-attack-impact-and-response)
- [CircleCI Jan 4, 2023 Incident Report](https://circleci.com/blog/jan-4-2023-incident-report/)
- [event-stream Incident Systematic Analysis](https://es-incident.github.io/paper.html)
- [Dev corrupts colors and faker — Bleeping Computer](https://www.bleepingcomputer.com/news/security/dev-corrupts-npm-libs-colors-and-faker-breaking-thousands-of-apps/)

### Ecosystem Security Research
- [Supply-Chain Poisoning Attacks Against LLM Coding Agent Skill Ecosystems (arXiv 2604.03081)](https://arxiv.org/html/2604.03081)
- [PoisonGPT — Mithril Security](https://blog.mithrilsecurity.io/poisongpt-how-we-hid-a-lobotomized-llm-on-hugging-face-to-spread-fake-news/)
- [Supply Chain Risk in VS Code Extension Marketplaces — Wiz](https://www.wiz.io/blog/supply-chain-risk-in-vscode-extension-marketplaces)
- [OWASP LLM Top 10 and Sonatype Data and Model Poisoning](https://www.sonatype.com/blog/the-owasp-llm-top-10-and-sonatype-data-and-model-poisoning)
- [LLM Backdoors at the Inference Level — Pillar Security](https://www.pillar.security/blog/llm-backdoors-at-the-inference-level-the-threat-of-poisoned-templates)
- [Lessons Learned from 2024's Supply Chain Attacks — CramHacks](https://www.cramhacks.com/p/lessons-learned-from-2024-s-supply-chain-attacks)
- [Docker Notary TUF analysis — Walmart Global Tech](https://medium.com/walmartglobaltech/docker-notary-very-tuf-but-devil-is-in-the-detail-5e643ea0aa16)
- [How to Use Sigstore Without Sigstore — academic critique](https://eprint.iacr.org/2023/003.pdf)

### npm and Registry Sources
- [Introducing npm Package Provenance — GitHub Blog](https://github.blog/security/supply-chain-security/introducing-npm-package-provenance/)
- [npm Provenance GA — Sigstore Blog](https://blog.sigstore.dev/npm-provenance-ga/)
- [npm Provenance — Socket.dev analysis](https://socket.dev/blog/npm-provenance)
- [PyPI now supports digital attestations](https://blog.pypi.org/posts/2024-11-14-pypi-now-supports-digital-attestations/)
- [Attestations: A new generation of signatures on PyPI — Trail of Bits](https://blog.trailofbits.com/2024/11/14/attestations-a-new-generation-of-signatures-on-pypi/)
- [PyPI Sigstore attestations GA — Sigstore Blog](https://blog.sigstore.dev/pypi-attestations-ga/)
- [crates.io Security Advisory (2020) — Rust Blog](https://blog.rust-lang.org/2020/07/14/crates-io-security-advisory/)
- [RFC #3403: Sigstore for Cargo](https://github.com/rust-lang/rfcs/pull/3403)
- [Secure quorum-based verification for crates.io — Rust Project Goals](https://rust-lang.github.io/rust-project-goals/2025h1/verification-and-mirroring.html)
- [RFC #3691: Trusted Publishing for crates.io](https://rust-lang.github.io/rfcs/3691-trusted-publishing-cratesio.html)
- [npm left-pad incident — Wikipedia](https://en.wikipedia.org/wiki/Npm_left-pad_incident)

### Go Sources
- [Module Mirror and Checksum Database Launched — Go Blog](https://go.dev/blog/module-mirror-launch)
- [How Go Mitigates Supply Chain Attacks — Go Blog](https://go.dev/blog/supply-chain)
- [Go Checksum Database Design Proposal](https://go.googlesource.com/proposal/+/master/design/25530-sumdb.md)

### Sigstore and TUF Sources
- [Sigstore Threat Model](https://docs.sigstore.dev/about/threat-model/)
- [Rekor v2 GA — Sigstore Blog](https://blog.sigstore.dev/rekor-v2-ga/)
- [Sigstore Incident History](https://status.sigstore.dev/incidents)
- [Repository Service for TUF Documentation](https://repository-service-tuf.readthedocs.io/en/latest/)
