# AI Agent Content Scanning Tools — Research Findings

**Date:** 2026-04-07
**Context:** Research to evaluate whether tooling exists for scanning natural language AI agent content (SKILL.md, AGENTS.md, .cursorrules, etc.) — specifically as it relates to the feasibility of MOAT's `scan_status` and `risk_tier` manifest fields.

**Prompted by:** Remy review of MOAT v0.4.0 claiming "no scanning tooling exists at scale for natural language AI agent content." This claim is materially overstated as of early 2026.

---

## Direct Answer

Remy's claim was accurate in 2024 and through early 2025. As of early 2026, it is **overstated**. Two tools specifically target natural language skill file content and have active development and/or at-scale evidence. However, no tool offers a clean registry-callable API for the specific MOAT use case (submit a SKILL.md, receive a structured `scan_status`/`risk_tier` verdict). That integration plumbing doesn't exist yet — but the analytical building blocks do.

---

## Tool-by-Tool Findings

### 1. Snyk mcp-scan (formerly Invariant mcp-scan)

**Vendor:** Snyk (acquired Invariant Labs, June 2025)
**CLI:** `uvx mcp-scan@latest` (free, open source)
**Commercial:** Snyk AI Security Foundation (launched February 2026)

**What it scans:**
- MCP server tool descriptions — natural language text describing what each tool does
- SKILL.md files — confirmed by the ToxicSkills study (February 2026), which scanned 3,984 skills from ClawHub and skills.sh
- Detects: hidden/deceptive instructions, base64 obfuscation, Unicode smuggling, "ignore previous instructions" patterns, system message impersonation

**Detection methodology:** Hybrid — multiple specialized ML models + deterministic rules. Trained on real-world threat data. Claims 90–100% recall on confirmed malicious skills with 0% false positives on top-100 legitimate skills (per ToxicSkills paper).

**Scans natural language instruction files (SKILL.md, etc.)?** Yes — confirmed at ecosystem scale.

**Primary mode:** Scanning live MCP servers (connecting and pulling tool descriptions at runtime). Static file scanning of a SKILL.md from a registry submission pipeline would require adaptation.

**At-scale evidence:** Yes. ToxicSkills study scanned ~4,000 skills in one run. Snyk runs ecosystem-scale research using this tooling.

**Registry-callable API?** Not publicly documented. Commercial partner API surface exists in Snyk platform.

**Can it scan a SKILL.md and return a risk verdict?** Partially yes — demonstrated for ecosystem research. No public API for programmatic registry integration.

**Sources:**
- ToxicSkills study: https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/
- Snyk AI Trust Platform: https://snyk.io/blog/introducing-the-snyk-ai-trust-platform/
- Acquisition announcement: https://snyk.io/news/snyk-acquires-invariant-labs-to-accelerate-agentic-ai-security-innovation/

---

### 2. Cisco AI Defense Skill Scanner

**Vendor:** Cisco (AI Defense division)
**GitHub:** `cisco-ai-defense/skill-scanner`
**Package:** Available on PyPI

**What it scans:**
- Skill directories containing SKILL.md + supporting files (YAML, Python scripts, shell scripts, binaries)
- Explicitly supports Claude Code `.claude/commands/*.md` files with `--lenient` flag
- Four-layer analysis: YARA + YAML static analysis → Python AST behavioral analysis → LLM semantic analysis of natural language → meta-analyzer for false positive filtering
- Optional cloud integration: VirusTotal (binaries), Cisco AI Defense cloud, external LLM

**Scans natural language instruction files?** **Yes, explicitly.** SKILL.md and markdown descriptions receive LLM semantic analysis. This is the most directly applicable tool for the MOAT registry use case.

**Output format:** SARIF — parseable by automated pipelines. A registry could invoke this via subprocess or import the Python package.

**At-scale evidence:** No public evidence of ecosystem-scale deployment. Individual developer/team use appears to be the target audience.

**Maturity:** 1.7k GitHub stars, actively maintained, CI/CD integration (GitHub Actions, pre-commit). Cisco backing. Self-described as "best-effort detection, not comprehensive or complete coverage."

**Can it scan a SKILL.md and return a risk verdict?** **Yes.** This is its primary design goal. Accepts a skill directory, outputs SARIF findings.

**Sources:**
- GitHub: https://github.com/cisco-ai-defense/skill-scanner
- Repello analysis of skill security: https://repello.ai/blog/claude-code-skill-security

---

### 3. Invariant Guardrails (pre-acquisition / now Snyk Labs)

**What it scans:** Agent traces — structured sequences of tool calls, messages, and outputs at runtime. Not static files.

**Scans natural language instruction files?** No. Operates on runtime traces. A SKILL.md on disk is out of scope.

**Relevance to MOAT:** None for the `scan_status` use case. Useful as a runtime enforcement layer after distribution, not as a registry-side scanner.

**Source:** https://github.com/invariantlabs-ai/invariant

---

### 4. agent-audit (HeadyZhang)

**What it scans:** Python source files, JSON/YAML MCP configs, `.env` files. 49–53 rules mapped to OWASP Agentic Top 10 (2026). AST-based taint tracking for code.

**Scans natural language instruction files?** No. Code and config files only. No markdown, SKILL.md, AGENTS.md, or cursorrules in scope.

**Relevance to MOAT:** Useful for registries that include Python hook scripts or agent code. Not applicable for the primary MOAT content types (markdown-based skills, rules, commands).

**Source:** https://github.com/HeadyZhang/agent-audit

---

### 5. Semgrep ai-best-practices

**What it scans:** Application code in supported languages (Python, JS/TS, etc.). Tracks taint flow from LLM API call responses into dangerous sinks.

**Scans natural language instruction files?** No. Code syntax analysis only. Running semgrep on a SKILL.md will produce zero findings — not because the skill is clean, but because semgrep has no rules for natural language.

**Relevance to MOAT:** Useful for scanning Python/JS code in hook scripts or registry tooling itself. Not applicable for markdown-based content.

**Note:** The original `semgrep/ai-best-practices` repo is deprecated; migrated to the official Semgrep registry (`semgrep.dev/p/ai-best-practices`).

---

### 6. Garak

**What it scans:** Live LLM deployments — sends adversarial probes to a running model and analyzes responses.

**Scans natural language instruction files?** No. Requires a live inference endpoint. Static file analysis is not in scope.

**Relevance to MOAT:** None for registry-side scanning.

---

### 7. Promptfoo + ModelAudit

**What it scans:** Promptfoo: live LLM application red-teaming. ModelAudit: ML model binary files (Pickle, H5, SavedModel) for embedded malicious code.

**Scans natural language instruction files?** No. Different threat model.

**Relevance to MOAT:** None for `scan_status` on SKILL.md content.

---

### 8. SkillRisk (skillrisk.org)

**Claims:** Browser-based scanner for SKILL.md, settings.json, .mcp.json, hook scripts. 646+ pattern rules. Client-side JavaScript.

**Status:** Unverified. No independent evidence of at-scale deployment or production use. Exercise caution — site shows future-dated CVE numbers. Do not rely on this for security decisions without independent validation.

---

### 9. Lakera Guard (now Check Point)

**What it scans:** Runtime LLM interactions — input/output guardrail at inference time.

**Scans natural language instruction files?** No. Runtime only.

**Relevance to MOAT:** None for registry-side scanning.

---

### 10. GitHub Copilot Autofix / CodeQL

**What it scans:** Application code in supported languages. AI-powered expansion targeting code logic flaws (public testing Q2 2026).

**Scans natural language instruction files?** No. Code analysis only.

**Relevance to MOAT:** None for content scanning, but relevant for scanning registry tooling source code.

---

### 11. MCP-Guard / MCP-Shield / SafeMCP (Research)

**What they scan:** MCP server tool descriptions — JSON configs and live MCP server responses. Rule-based static analysis + optional LLM semantic pass.

**Scans natural language instruction files?** Partial — they target MCP tool description content specifically. Overlaps with skill files if the skill exposes MCP tools.

**Maturity:** Research prototypes. No evidence of production deployment.

---

## Summary Matrix

| Tool | Scans NL instruction files? | Scans code/configs | Runtime vs Static | Maturity | At-scale evidence | Registry-callable? |
|---|---|---|---|---|---|---|
| **Snyk mcp-scan** | **Yes (SKILL.md confirmed)** | Partial | Both | Beta/early GA | Yes (4K skills) | Not public |
| **Cisco Skill Scanner** | **Yes (explicit design goal)** | Yes | Static | Active dev, not GA | No public evidence | Via subprocess/pkg |
| Invariant Guardrails | No | No | Runtime only | GA (pre-acq) | Yes | Yes (Python API) |
| agent-audit | No | Yes | Static | v0.16, active | No | CLI only |
| Semgrep ai-best-practices | No | Yes (code) | Static | GA | Yes (enterprise) | Via Semgrep API |
| Garak | No | No | Runtime (live model) | GA | Yes | CLI/Python |
| Promptfoo | No | No (model binaries) | Runtime + binary | GA | Yes | CLI |
| SkillRisk | Claimed | Claimed | Static (browser) | Unverified | None | No |
| Lakera Guard | No | No | Runtime | GA | Yes | Commercial |
| GitHub Copilot/CodeQL | No | Yes (code) | Static | GA | Very large | GitHub API |
| MCP-Guard/Shield/SafeMCP | Partial (MCP JSON) | Partial | Static | Research | None | No |

---

## Implications for the MOAT Spec

### `scan_status` field

The field structure is sound. The critical gap is not "no tools exist" but "no tool offers a clean registry submission API." A registry implementing `scan_status` today would:

1. Use **Cisco's skill-scanner** as the most directly applicable tool (Python package, accepts skill directory, outputs SARIF, supports SKILL.md semantic analysis)
2. Integrate with **Snyk's platform** via partner API for higher confidence (not public, requires commercial relationship)
3. Fall back to `result: "not_scanned"` for content types the tools don't cover (non-SKILL.md formats)

A registry that runs Cisco's skill-scanner on every submitted skill and reports honest `scan_status` with `scanner: [{"name": "cisco-skill-scanner", "version": "x.y.z"}]` is technically conforming and substantively meaningful today.

### `risk_tier` field (L0–L3)

This is harder. No tool today maps scan findings directly to MOAT's L0–L3 rubric. A registry would need to interpret SARIF findings and assign tiers using their own mapping logic. For the v1 rollout, a conservative mapping is reasonable: any SARIF findings → L2/L3 depending on severity; no findings → L1 (conservative baseline for NL content that can't be proven read-only); explicit shell execution instructions → L3.

Remy's v1 scope-down suggestion (ternary: `safe_static` / `uses_tools` / `not_analyzed`) remains worth considering given that the L0–L3 analysis requires interpretation that tools don't automate today.

### Companion tooling guidance

The normative spec should not name specific scanners — tools change quickly. A companion document (e.g., `docs/registry-operator-guide.md`) should list recommended scanners, integration patterns, and the recommended SARIF-to-risk-tier mapping, updated as the ecosystem evolves.

---

## Key Correction to Remy's Review

Remy stated: "The spec defines a rubric that makes sense conceptually. What it does not address is how a registry operator actually implements this analysis."

**Accurate revision (2026):** The tooling is emerging fast. Three distinct vendors (Snyk, Cisco, Repello) launched skill-specific scanning within a 12-month window (early 2025 to early 2026). The ToxicSkills study (February 2026) finding that 36.8% of ecosystem skills have security flaws has created urgency. The field is being built now, not 3 years from now.

Remy's recommendation to scope `risk_tier` to a ternary for v1 may still be right — but for a different reason: not because analysis is impossible, but because no tool yet automates the L0–L3 classification. The rubric is correct; the gap is the automated mapping layer between scanner output and tier assignment.
