# MOAT Ecosystem Landscape & Positioning

**Date:** 2026-04-03
**Purpose:** Research synthesis mapping the agentic AI content ecosystem, identifying where MOAT fits, and reframing the spec's positioning based on findings.

---

## Table of Contents

1. [Summary](#summary)
2. [The AAIF Ecosystem](#the-aaif-ecosystem)
3. [Content Format Standards](#content-format-standards)
4. [Packaging & Distribution Projects](#packaging--distribution-projects)
5. [The Provenance Gap](#the-provenance-gap)
6. [MOAT Comparison with APS](#moat-comparison-with-aps)
7. [Positioning & Naming](#positioning--naming)
8. [Domain Decision](#domain-decision)
9. [Publication Strategy](#publication-strategy)
10. [Open Questions](#open-questions)

---

## Summary

Research into the agentic AI standards landscape (April 2026) reveals that:

- A mature ecosystem of **content format** standards exists under the Agentic AI Foundation (AAIF / Linux Foundation): Agent Skills, AGENTS.md, MCP.
- Multiple **packaging and distribution** projects exist outside AAIF: APS, Microsoft APM, .agent format.
- **No standard addresses provenance, integrity, or trust** for agent content. This is the gap MOAT fills.
- MOAT should be positioned not as a syllago feature or standalone project, but as the **missing trust layer for the entire AAIF ecosystem**.
- The Cisco research finding critical vulnerabilities (credential theft, malware) in community skills validates the urgency.

---

## The AAIF Ecosystem

The **Agentic AI Foundation (AAIF)** was announced December 2025 under the Linux Foundation. Founding members: Anthropic, OpenAI, Block. Platinum members include AWS, Google, Microsoft, Cloudflare, Bloomberg.

Block's stated goal: AAIF should become "what the W3C is for the Web" for AI agents.

### Core AAIF Projects

| Standard | Governs | Origin | Adoption |
|----------|---------|--------|----------|
| **MCP** (Model Context Protocol) | Tool/data connections for LLMs | Anthropic, Nov 2024 | Industry standard, JSON-RPC 2.0 based |
| **Agent Skills** (SKILL.md) | Portable skill format for AI coding agents | Anthropic, Dec 2025 | 16+ tools (Claude Code, Codex, Cursor, Gemini CLI, Copilot, etc.), 1300+ community skills |
| **AGENTS.md** | Project-level rules/instructions for AI agents | OpenAI, Aug 2025 | 60,000+ open-source projects |
| **Goose** | Open-source coding agent framework | Block | Active development |

### What AAIF Does NOT Cover

| Content Type | Status |
|-------------|--------|
| **Hooks** | No cross-tool spec. Claude Code and Codex have tool-specific implementations. |
| **Agent definitions** | No formal spec beyond AGENTS.md conventions. |
| **Provenance / integrity / trust** | **Nothing.** No standard for verifying authorship, integrity, or lineage of any content type. |

### AAIF 2026 Events

- AGNTCon + MCPCon Europe: Sept 17-18, Amsterdam
- AGNTCon + MCPCon North America: Oct 22-23, San Jose

Source: https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation

---

## Content Format Standards

### Agent Skills (agentskills.io)

The closest standard to what syllago manages. Defines the SKILL.md format:

- **Directory structure:** `skill-name/` containing `SKILL.md` (required) plus optional `scripts/`, `references/`, `assets/`
- **Frontmatter fields:** `name` (required, 1-64 chars, lowercase+hyphens), `description` (required, 1-1024 chars), `license`, `compatibility`, `metadata` (arbitrary key-value), `allowed-tools` (experimental)
- **Progressive disclosure:** Only name+description loaded at startup; full body loaded on activation
- **No provenance model.** No hashing, signing, authorship verification, or lineage tracking.

Security note: Cisco researchers have found critical vulnerabilities in community skills including credential theft and malware via prompt injection. The ecosystem is growing rapidly with no integrity verification layer.

Source: https://agentskills.io/specification

### AGENTS.md

Project-level rules file. Plain markdown, no formal schema. Adopted by 60K+ projects. Works across Claude Code, Cursor, Copilot, Codex, Gemini CLI, and others.

Tool-specific variants still exist (CLAUDE.md, .cursorrules, copilot-instructions.md, .windsurfrules) but AGENTS.md is the convergence point.

Source: https://prpm.dev/blog/agents-md-deep-dive

### MCP (Model Context Protocol)

The protocol for connecting LLMs to external tools and data. JSON-RPC 2.0 based. Defines transport, message format, and capability negotiation. The Nov 2025 spec added async execution and enterprise authorization.

2026 roadmap focuses on: Streamable HTTP transport, Tasks primitive, enterprise readiness, configuration portability.

Source: https://modelcontextprotocol.io/specification/2025-11-25

### Other Rules Efforts

- **aicodingrules.org** — Proposed unified YAML+Markdown rule format attempting to bridge the fragmentation
- **rulesync** (npm) — Tool to generate tool-specific rule files from a single source

---

## Packaging & Distribution Projects

### APS (Agent Packaging Standard) — agentpackaging.org

**Most similar to MOAT's provenance model, but operates at a different layer.**

- **Focus:** Packaging and distributing AI agents as tar.gz bundles
- **Format:** `agent.yaml` manifest + `.aps.tar.gz` package
- **Provenance:** Single SHA-256 digest, Ed25519 signing (Sigstore planned), basic build metadata (repository, commit, environment)
- **Policy levels:** Lenient (warn on unsigned), Strict (reject unverifiable), Custom (external attestation)
- **Status:** v0.1 draft, Apache 2.0
- **Governance:** "APS Working Group" (single maintainer: vedahegde60 on GitHub)
- **Registry API:** Defined (REST endpoints for publish/retrieval)

Source: https://agentpackaging.org/security/provenance/

### Microsoft APM (Agent Package Manager) — github.com/microsoft/apm

- **Focus:** Dependency management for agent configurations (npm-for-agents)
- **Format:** `apm.yml` manifest declaring instructions, skills, prompts, agents, hooks, plugins, MCP servers
- **Security:** Content scanning (`apm audit` detects hidden Unicode), policy governance (`apm-policy.yaml`). No cryptographic provenance.
- **Status:** v0.8.10, active, 950+ GitHub stars, 39 releases
- **Distribution:** Supports GitHub, GitLab, Bitbucket, Azure DevOps, custom git hosts. Transitive dependency resolution.

Source: https://github.com/microsoft/apm

### .agent Format — agenticapi/agentpk

- **Focus:** Packaging AI agents with behavioral trust scoring
- **Components:** Machine-readable manifest, SHA-256 integrity hash, behavioral trust score (0-100, including LLM semantic analysis), Ed25519 signing
- **Status:** Early, patent-pending (spec), MIT (tooling), CC BY 4.0 (spec)
- **Creator:** Chris Hood

Source: https://chrishood.com/introducing-agent-the-open-packaging-standard-for-ai-agents/

---

## The Provenance Gap

The ecosystem has format standards (how to write content) and packaging projects (how to bundle and distribute content). **None address provenance — the ability to verify who made content, whether it's been tampered with, and where it came from.**

### What Each Layer Provides

| Layer | Examples | What It Answers |
|-------|----------|----------------|
| **Format** | Agent Skills, AGENTS.md, MCP | "How do I structure this content?" |
| **Packaging** | APS, Microsoft APM, .agent | "How do I bundle and distribute this content?" |
| **Provenance** | **Nothing (this is MOAT's gap)** | "Who made this? Has it been modified? Where did it come from?" |

### Why This Gap Matters Now

1. **1,300+ community skills** with no way to verify authorship or integrity
2. **Cisco security research** finding credential theft and malware in community skills
3. **Enterprise adoption** of AAIF standards — enterprises need provenance for compliance
4. **Cross-tool content sharing** means content moves between contexts with no trust chain
5. **Supply chain attacks** are a known vector — the agent content ecosystem has no defense

---

## MOAT Comparison with APS

APS is the closest existing project to MOAT. Key differences:

### Where MOAT Goes Deeper

| Area | MOAT | APS |
|------|-----|-----|
| **Hash architecture** | Dual-hash (content_hash + meta_hash binding) prevents mix-and-match attacks | Single digest over package artifact |
| **Lineage** | `derived_from` with fork/convert/adapt relations, version reset on derivation | No lineage tracking |
| **Content hash algorithm** | Deterministic directory tree hashing with NFC normalization, symlink handling, VCS exclusion | Hashes tar.gz blob |
| **Metadata canonicalization** | JCS (RFC 8785) for reproducible JSON serialization | Not addressed |
| **Test vectors** | 17+ normative vectors | CLI output examples |
| **Security considerations** | 16 subsections (sidecar stripping, signature stripping, TOCTOU, namespace attacks, etc.) | Basic policy descriptions |
| **Granularity** | Content-level (individual skills, hooks, rules) | Package-level (bundled archives) |

### Where APS Covers Ground MOAT Doesn't

| Area | APS | MOAT |
|------|-----|-----|
| **Package format** | Defined (tar.gz bundling) | Out of scope |
| **Registry API** | REST endpoints specified | Out of scope |
| **CLI interface** | `aps sign`, `aps verify`, `aps keygen` | Out of scope (implementation concern) |
| **Runtime verification** | Pre-execution verification hooks | Out of scope |

### Relationship

These specs are **complementary, not competing.** MOAT answers "is this specific piece of content authentic and unmodified?" APS answers "how do I bundle and distribute an agent?" APS could adopt MOAT's provenance model as its integrity layer — it would be a significant upgrade over their current single-digest approach.

---

## Positioning & Naming

### Reframing

MOAT should not be positioned as:
- A syllago feature
- A standalone project
- A competitor to APS or any packaging standard

MOAT should be positioned as:
- **The missing trust/provenance layer for the AAIF ecosystem**
- A spec that secures Agent Skills, AGENTS.md rules, MCP configs, hooks, and agent definitions
- A candidate for AAIF governance alongside MCP, Agent Skills, and AGENTS.md

### Naming Decision

**Renamed from ACP (Agent Content Provenance) to MOAT (Metadata for Origin, Authorship, and Trust)** on 2026-04-03.

The original "ACP" acronym was crowded in the standards space. After evaluating alternatives (PACT, VOUCH, SIGIL, CODA, TACIT, MINT), MOAT was selected for:
- Clean acronym expansion that accurately describes the spec's scope
- Defensive metaphor (a moat protects the ecosystem) aligns with provenance/integrity purpose
- No collision with existing specs, protocols, or major projects in the agent/security space
- Strong CLI ergonomics (`moat verify`, `moat sign`)
- Validated by a 4-persona panel (standards architect, developer practitioner, security researcher, branding specialist) — unanimous approval

Note: The cryptographic domain separator was updated from `ACP-V1:` to `MOAT-V1:`, which changes the signing input test vector (TV-SI).

---

## Domain Decision

For the spec's standalone website:

- **TLD:** `.org` — carries the most weight for standards (graphql.org, opencontainers.org, json-schema.org)
- **Selected domain:** `moatspec.org` (~$10/year, confirmed available 2026-04-03)
- `.org` signals "open standard" vs `.dev` which signals "developer tool" — important distinction for AAIF positioning

---

## Publication Strategy

### Phase 1: Standalone Spec Site (Now)

- Publish the spec on its own site (Starlight, GitHub Pages)
- Independent of syllago — the spec is tool-agnostic
- Shareable URL for reviewers (Agent Ecosystem, Aembit colleagues)
- Domain: `moatspec.org`

### Phase 2: Ecosystem Integration

- Reference from syllago-docs ("syllago implements MOAT" with link to spec site)
- Engage with AAIF community — the spec fills a gap they haven't addressed
- Seek feedback from Agent Skills and MCP communities specifically

### Phase 3: Governance (Aspirational)

- Propose MOAT (or renamed spec) as an AAIF project
- The spec's tool-agnostic design and Apache 2.0 license align with AAIF's model
- Precedent: MCP (Anthropic), AGENTS.md (OpenAI), Goose (Block) were all donated by companies

---

## Open Questions

1. ~~**Rename or keep ACP?**~~ **Resolved.** Renamed to MOAT (Metadata for Origin, Authorship, and Trust). Domain: moatspec.org.

2. **Engage with APS?** Their provenance model is shallow compared to MOAT. Collaboration (APS adopts MOAT's provenance layer) could be mutually beneficial. Risk: they may not be receptive, and their governance is unclear (single maintainer).

3. **AAIF timing.** Is it too early to engage with AAIF? The spec is v0.1 draft with no independent implementations yet. Counter-argument: getting involved early in a new foundation is often easier than later.

4. **syllago's public timeline.** The spec can go public independently, but syllago as the reference implementation strengthens the story. What's the timeline for syllago going public?

5. **Hooks spec gap.** Hooks have no cross-tool standard. Is this something syllago/MOAT should address, or wait for AAIF?
