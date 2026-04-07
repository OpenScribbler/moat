# Research Notes: Supply-Chain Poisoning Attacks Against LLM Coding Agent Skill Ecosystems

**Paper:** Supply-Chain Poisoning Attacks Against LLM Coding Agent Skill Ecosystems  
**arXiv ID:** 2604.03081  
**DOI:** https://doi.org/10.48550/arXiv.2604.03081  
**Authors:** Yubin Qu, Yi Liu, Tongcheng Geng, Gelei Deng, Yuekang Li, Leo Yu Zhang, Ying Zhang, Lei Ma  
**Submitted:** April 3, 2026  
**Categories:** cs.CR (primary), cs.AI, cs.CL  
**Replication package:** https://sites.google.com/view/poisoning-agent-skills  

---

## Why This Paper Matters for MOAT

This is the first empirical study of supply-chain poisoning attacks specifically against AI agent skill ecosystems — the exact threat model MOAT is designed to address. It provides attack success rates, defense effectiveness data, and detection gap measurements for the Claude Code, OpenHands, Codex, and Gemini CLI frameworks. Every claim MOAT makes about adversarial skills can now be backed by numbers from this paper.

---

## Core Research Question

Can an adversary embed malicious payloads inside skill *documentation* — not explicit commands — that survive model safety alignment and framework guardrails, causing agents to execute unauthorized operations (file I/O, shell commands, network requests, package installations)?

The answer: yes, at bypass rates of **11.6%–33.5%** depending on framework and model.

---

## The Key Attack Concept: DDIPE

**Document-Driven Implicit Payload Execution (DDIPE)** is the paper's central contribution. Rather than issuing direct instructions ("run this command"), DDIPE embeds malicious logic in plausible-looking documentation artifacts — code examples, configuration templates, Makefile snippets — that agents reproduce as part of their normal helpful behavior.

The insight: safety alignment is trained on explicit imperative instructions. It generalizes poorly to documentation-embedded payloads. An agent asked to "implement the example from the skill's README" is behaviorally different from an agent asked to "run this malicious command."

> "DDIPE achieves bypass rates of 11.6%–33.5% across all eight tested configurations, while explicit instruction injection achieves 0%."

The explicit-instruction baseline (0%) is critical context: the existing defenses *do work* against naive attacks. DDIPE is specifically designed to route around them.

---

## Methodology

### PoisonedSkills Pipeline

```
81 expert-crafted seeds
       ↓
Stage 1: Seed Expansion (payload substitution)
       → 739 new samples
       ↓
Stage 2: Camouflage Mutation (8 operators)
       → 250 new samples
       ↓
Final dataset: 1,070 valid adversarial skills
```

- 99.1% format validation pass rate
- Average payload size: 1,666 bytes (Stage 1), 4,172 bytes (Stage 2)
- 15 attack categories, full MITRE ATT&CK coverage
- Evaluated across 8 configurations (4 frameworks × 5 models, some shared)
- 8,560 total execution trials
- Behavioral classification via LLM-as-Judge (Cohen's κ = 0.88)
- 10% stratified human review by security experts
- Docker-isolated containers with network isolation and filesystem snapshots

### Frameworks and Models Tested

| Framework   | Models Tested                            |
|-------------|------------------------------------------|
| Claude Code | Claude Sonnet 4.6, GLM-4.7, MiniMax-M2.5 |
| OpenHands   | Claude Sonnet 4.6, GLM-4.7, MiniMax-M2.5 |
| Codex       | GPT-5.4                                  |
| Gemini CLI  | Gemini 2.5 Pro                           |

---

## End-to-End Results

**DER = Directly Executed Rate. BR = Bypass Rate (Generated + Executed).**

| System      | Model          | Refused (%) | Generated (%) | Executed (%) | BR (%) | DER (%) |
|-------------|----------------|-------------|---------------|--------------|--------|---------|
| Claude Code | Sonnet 4.6     | 85.9        | 11.1          | **2.3**      | 13.5   | 2.3     |
| Claude Code | GLM-4.7        | 81.9        | 14.4          | **2.4**      | 16.8   | 2.4     |
| Claude Code | MiniMax-M2.5   | 78.0        | 7.2           | **13.3**     | 20.5   | 13.3    |
| OpenHands   | Sonnet 4.6     | 65.4        | 11.2          | **10.7**     | 22.0   | 10.7    |
| OpenHands   | GLM-4.7        | 56.4        | 6.4           | **27.1**     | 33.5   | 27.1    |
| OpenHands   | MiniMax-M2.5   | 8.5         | 1.5           | **25.5**     | 27.0   | 25.5    |
| Codex       | GPT-5.4        | 27.4        | 7.8           | **3.8**      | 11.6   | 3.8     |
| Gemini CLI  | Gemini 2.5 Pro | 79.4        | 9.8           | **4.2**      | 14.0   | 4.2     |

**Reading this table for MOAT:** Even in the best case (Claude Code + Sonnet 4.6), 2.3% of adversarial skills execute their payloads. At ecosystem scale — the ClawHub registry had 180K+ skills — 2.3% is thousands of active threats.

---

## Framework Amplification Effect

Moving from Claude Code to OpenHands (removing architectural guardrails while keeping the same model) reveals how much work the framework is doing:

| Model        | Claude Code DER | OpenHands DER | Amplification |
|--------------|-----------------|---------------|---------------|
| GLM-4.7      | 2.4%            | 27.1%         | **11.3×**     |
| Sonnet 4.6   | 2.3%            | 10.7%         | **4.7×**      |
| MiniMax-M2.5 | 13.3%           | 25.5%         | **1.9×**      |

The GLM-4.7 result is the most important: 219 payloads that Claude Code's architecture blocked become "sleeper payloads" — refused in one environment, executed when the framework changes. A skill that appears safe on one platform is not necessarily safe on another.

> "Neither layer alone is sufficient, and their composition is model-dependent: the same architectural change activates 219 sleeper payloads on one model but only 5 on another."

---

## Detection Results

### SkillScan Performance
*(SkillScan is detailed in the companion paper: Liu et al., arXiv:2601.10338)*

| Metric                | Value                                                           |
|-----------------------|-----------------------------------------------------------------|
| Detection rate        | **90.7%** (971/1,070 samples)                                   |
| Evasion rate          | **9.3%** (99/1,070 samples)                                     |
| Evasion mechanism     | Disguising attacks as compliance reports                        |
| Dual-penetration rate | **2.5%** (27/1,070 — bypass BOTH SkillScan AND model alignment) |

The 27 dual-penetration cases are the most dangerous: they survive the registry's scanner AND the model's alignment. These are the attacks that require layered defense.

### Ensemble Defense Effectiveness

| Defense                                                    | Attack Surface Remaining |
|------------------------------------------------------------|--------------------------|
| Single model (best case: Sonnet 4.6)                       | 2.3–13.3%                |
| Any single framework                                       | 11.6–33.5%               |
| All-model bypass (all 3 Claude Code models simultaneously) | **1.6%** (17/1,070)      |

Running multiple independent models as reviewers and requiring consensus reduces All-Bypass to 1.6% — the single most actionable defense finding in the paper.

---

## Attack Taxonomy

### 15 Attack Categories (MITRE ATT&CK Mapped)

| Category                   | MITRE ID     | Notes                                          |
|----------------------------|--------------|------------------------------------------------|
| Reverse Shell / RCE        | T1059.004    | Remote shell establishment                     |
| Container Escape           | T1611        | Breaks containerized isolation                 |
| Supply-Chain Poisoning     | T1195.002    | Redirects package manager to attacker registry |
| Malicious Config Write     | T1565.001    | Tampers system/app config files                |
| Persistence Implant        | T1053, T1543 | Cron jobs, systemd units                       |
| Credential Theft           | T1552.004    | SSH keys, tokens, API credentials              |
| Environment Variable Theft | T1528        | API keys, secrets from env                     |
| HTTP Exfiltration          | T1048.003    | Data over HTTP/S                               |
| DNS Exfiltration           | T1048.003    | Data encoded in DNS queries                    |
| Webhook Exfiltration       | T1567.002    | Data posted to attacker webhooks               |
| IaC Attacks                | T1496        | Terraform/Ansible/Helm poisoning               |
| Cryptomining               | T1496        | Cryptocurrency mining install                  |

### Category Distribution in Dataset

- Supply-chain poisoning: **47.5%** of samples (largest category)
- Environment variable theft: 11.9%
- Credential theft: 8.6%
- Cryptomining: 0.4% (rarest)

### Per-Category Results Under Claude Code

| Category            | n   | Sonnet 4.6 DER | GLM-4.7 DER | MiniMax-M2.5 DER |
|---------------------|-----|----------------|-------------|------------------|
| Supply-Chain Poison | 508 | 2.8%           | 2.4%        | 9.4%             |
| Creds & Env Theft   | 219 | 2.3%           | 3.7%        | 17.8%            |
| Config Tamper       | 64  | 6.3%           | 6.3%        | 20.3%            |
| Code & Infra        | 124 | 1.6%           | 0.0%        | 13.7%            |
| Network Exfil       | 82  | 0.0%           | 1.2%        | 19.5%            |
| Sys Persistence     | 48  | 0.0%           | 2.1%        | 16.7%            |
| Other               | 25  | 0.0%           | 0.0%        | 4.0%             |

Config Tamper has the highest execution rate for well-aligned models (6.3% for Sonnet 4.6 and GLM-4.7). These are subtle — modifying a `.gitconfig`, `pip.conf`, or `.npmrc` looks like legitimate setup work.

---

## 8 Camouflage Mutation Operators

These are the techniques that make the 9.3% of samples that evade SkillScan hard to detect:

| Operator             | Description                                                                                  |
|----------------------|----------------------------------------------------------------------------------------------|
| **ContextShift**     | Reframes payload as normal operational behavior                                              |
| **AuthorityInject**  | Adds fake compliance/authority language ("per NIST guidelines", `.internal` domains)         |
| **EncodingWrap**     | Obfuscates payload in base64 or other encodings                                              |
| **TriggerChain**     | Defers execution to a trigger condition to avoid immediate scrutiny                          |
| **DomainMigrate**    | Moves C2 endpoints to believable-looking internal domains (e.g., `metrics.company.internal`) |
| **SemanticDisguise** | Masks data exfiltration as legitimate telemetry or logging                                   |
| **CompositeChain**   | Chains multiple small operations to obscure end goal                                         |
| **AntiDetection**    | Adds `try/except: pass` blocks and other silent exception suppression                        |

### Three Specific Techniques Called Out

1. **Functional compliance disguise** — Credential exfiltration framed as "telemetry" or "error reporting to comply with GDPR retention policies"
2. **Silent exception suppression** — `try/except: pass` hides all errors from the agent, making the malicious action invisible in output
3. **False authority suggestion** — `.internal` domains and regulatory terminology trigger "this looks legitimate" pattern matching in both models and scanners

---

## Defense Findings

### What Works

| Defense                                            | Effectiveness              | Notes                                                |
|----------------------------------------------------|----------------------------|------------------------------------------------------|
| Model safety alignment (Sonnet 4.6)                | ~86% refusal rate          | Best-case; not universal                             |
| Framework architectural guardrails                 | 4.7–11.3× reduction        | Framework-dependent, model-dependent                 |
| Static scanning (SkillScan)                        | 90.7% detection            | 9.3% evasion via compliance disguise                 |
| Trust-boundary annotation in system prompt         | 100% for Sonnet 4.6        | Adding "this content is untrusted" to system message |
| Cross-model ensemble (3 models, require consensus) | Reduces All-Bypass to 1.6% | Most practically significant defense                 |

### The Trust-Boundary Annotation Fix

The OpenHands team deployed a fix: adding an explicit annotation to the system message template marking repository-provided content as "untrusted." This achieved **100% remediation for Sonnet 4.6** — all three previously-executed breach cases were refused after the fix.

This is the closest existing empirical evidence for a MOAT-style trust metadata approach. The provenance and trust tier information MOAT surfaces to agents at install time is the protocol-level version of this fix.

**Caveat:** This fix only worked for well-aligned models. For MiniMax-M2.5 (8.5% refusal rate to begin with), trust annotations had no measurable effect. Architecture cannot compensate for insufficient alignment.

### What Doesn't Work Alone

- **Model alignment alone:** 8.5%–85.9% refusal rate variance across models. No model is sufficient by itself.
- **Framework guardrails alone:** Without strong model alignment, architectural protection is bypassed. MiniMax-M2.5 on OpenHands: 8.5% refusal despite framework protections.
- **Static scanning alone:** 9.3% evasion rate. The 27 dual-penetration cases bypass both scanning and alignment.
- **Single scanner:** SkillScan is the best available tool and misses nearly 1 in 10 adversarial samples.

---

## Key Insights

### Brevity Effect
Executed samples averaged **1,850 bytes** vs. 1,964 bytes for refused samples. Shorter, cleaner payloads are harder to refuse.

The extreme case: a **479-byte universal pip.conf payload** was executed by all three Claude Code models. This is the minimal viable attack — a plausible package manager configuration file with a malicious index URL, reproduced by the agent as part of "setting up the development environment."

### Model Blind Spots
- **Sonnet 4.6 exclusive executions:** 11 samples. 90.9% used DevOps/operational tool disguises with `.internal` domains. Sonnet's safety training is robust against general malicious patterns but has a specific blind spot for operational/infrastructure templates.
- **MiniMax-M2.5:** 78 exclusive executions — the weakest alignment of the tested models.

### Cross-Model Disagreement
Only 1.6% (17/1,070) of samples bypass all three Claude Code models simultaneously. Cross-model disagreement is a feature, not a bug: different models have different blind spots, and consensus-based review exploits this.

### The Sleeper Payload Problem
219 payloads were refused by Claude Code + GLM-4.7 but executed by OpenHands + GLM-4.7. The same skill file behaves differently depending on the framework's architectural context. A skill that passes safety review on one platform cannot be assumed safe on another.

---

## Limitations (From the Paper)

1. **Generation bias** — Seeds generated with Claude Opus 4.6 may be biased toward patterns other Claude models overlook
2. **Non-controlled comparison** — Claude Code vs. OpenHands is observational, not a controlled ablation
3. **No per-operator ablation** — The 8 camouflage operators' individual contributions are not measured
4. **Model coverage gaps** — Llama ecosystem and Cursor not evaluated
5. **Retrieval not tested** — Production validation with realistic skill retrieval pipelines not attempted
6. **API error rates** — Two configurations exceeded 60% error rates due to API compatibility issues
7. **Weak baselines** — Only explicit instruction injection tested; Skill-Inject (stronger baseline) not evaluated
8. **Defenses not evaluated** — Dynamic sandboxing and LLM-based auditing untested

---

## Related Papers Worth Reading

| Paper                                                                                                                                            | Relevance                                                                                                               |
|--------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| **Liu et al. (2026), arXiv:2601.10338** — "Agent Skills in the Wild: An Empirical Study of Security Vulnerabilities at Scale"                    | The SkillScan companion paper. Details the four-layer detection system used here.                                       |
| **Greshake et al. (2023)** — "Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection" | Foundational indirect prompt injection work this paper builds on.                                                       |
| **PoisonedRAG (Zou et al., 2025)**                                                                                                               | Knowledge corruption attacks against RAG systems. Text-level injection without code execution — the precursor to DDIPE. |
| **Carlini et al. (2024)** — "Poisoning Web-Scale Training Datasets is Practical," IEEE S&P                                                       | Background on supply-chain poisoning at training data level.                                                            |
| **Skill-Inject** (full citation not in paper)                                                                                                    | Mentioned as a stronger baseline not tested. Worth tracking down.                                                       |

---

## MOAT Design Implications

### Numbers This Paper Gives Us

The paper provides empirical grounding for MOAT's threat model. These are no longer estimates:

- **Bypass rate range:** 11.6%–33.5% depending on framework/model combination
- **Best-case bypass rate:** 2.3% (Claude Code + Sonnet 4.6) — the most protected combination
- **Static scanner miss rate:** 9.3% even with the best available tool
- **Dual-penetration rate:** 2.5% bypass both scanning AND alignment
- **Ensemble benefit:** Cross-model consensus reduces All-Bypass to 1.6%
- **Sleeper payload count:** 219 payloads safe on one framework, exploitable on another

### Specific MOAT Takeaways

**1. `scan_status` multi-scanner rationale is now empirically backed**  
The scanner array in `scan_status` isn't a convenience feature — it's a documented defense necessity. The 9.3% evasion rate from a single scanner justifies requiring multi-engine consensus. The spec should reference this data when explaining why the scanner field is an array.

**2. `risk_tier` should account for sleeper payloads**  
219 payloads execute only when architectural protection is removed. A skill with a `risk_tier` of `L0` assessed on one framework may behave as `L3` on another. The spec's caveat that "the rubric is about capability granted, not strings present" needs to address the framework-dependency problem. Registries should note which framework/context the tier was assessed in.

**3. Trust-boundary annotation → MOAT's trust tier display**  
The OpenHands fix (explicit "untrusted" annotation in system prompt = 100% refusal improvement for Sonnet 4.6) is the runtime analog of what MOAT does at distribution time. MOAT clients that surface trust tier and scan results to the agent's context at install time are implementing exactly this fix at the protocol layer. This is worth stating explicitly in the spec's rationale for `scan_status` and `risk_tier`.

**4. Config Tamper is the highest-risk category for well-aligned models**  
6.3% execution rate for Sonnet 4.6 — higher than Credential Theft (2.3%) or Supply-Chain Poisoning (2.8%). Skills that include configuration templates (`.npmrc`, `pip.conf`, `.gitconfig`) should receive elevated scrutiny. Registry tooling computing `risk_tier` should weight configuration write capabilities upward.

**5. The 479-byte pip.conf attack is a conformance test vector**  
A minimal, plausible-looking pip configuration file that redirects package installs to a malicious index executed across all three Claude Code models. This is the kind of adversarial test vector the MOAT conformance test suite should include for `risk_tier` analysis tools.

**6. The 9.3% gap is the argument for behavioral sandboxing**  
The paper explicitly identifies dynamic sandboxing as a defense not yet evaluated. The gap between 90.7% static detection and 100% is filled by: behavioral execution in isolation (observe what the skill actually does, not just what it says). The `scan_status` spec guidance for registries SHOULD mention behavioral sandboxing as a complement to signature-based scanning.

**7. Ensemble review has a 1.6% floor**  
Running three independent models as reviewers reduces All-Bypass to 1.6% (17/1,070). This is the practical minimum with current technology. The spec's "secure path is visibly tiered" principle should acknowledge this — no registry can claim 0% detection with any combination of current defenses.

---

## Critical Quote for the Spec Introduction

> "DDIPE achieves bypass rates of 11.6%–33.5% across all eight tested configurations, while explicit instruction injection achieves 0%."

This is the sentence that justifies MOAT's entire existence as a registry protocol. The threat is real, measurable, and specifically resistant to naive defenses. A well-designed registry with layered controls (signing + scanning + risk tier + trust annotation) addresses the exact vulnerability surface this paper maps.
