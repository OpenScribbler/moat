# MOAT — Working Guidelines for AI-Assisted Sessions

This file provides context and working principles for AI-assisted sessions on this project. It is not a contributor guide — it is a brief for the AI partner.

---

## What MOAT Is

MOAT (Manifest for Open AI Tooling) gives people who install AI agent content a way to verify it hasn't been tampered with and came from who they think. Content covered includes: skills, sub-agents, rules, commands, hooks, and MCP configs.

That's the whole job. Not safety scoring. Not policy enforcement. Provenance and integrity.

---

## Design Philosophy

### Creators do as little as possible

This is the load-bearing principle. Publishers add one workflow file and are done. If adopting MOAT requires publishers to change how they write or distribute content, the spec fails. Any decision that adds friction to the publisher path must justify itself — not theoretically, but against the reality that most publishers won't read the spec or implement anything too complex.

When the spec defines requirements that conformers must implement in complex or non-obvious ways, provide a reference implementation. The goal is that people can adopt MOAT without complex implementation decisions or guesswork. If a requirement is non-trivial to implement, it must be accompanied by a reference implementation that conformers can follow to get it right.

### Requirements must be enforceable

If something is labeled MUST or SHOULD, there must be an enforcement layer backing it. A requirement with no mechanism to enforce it is not a requirement — it is a suggestion dressed up in normative language. Before using MUST or SHOULD, ask: what happens when this is ignored? If the answer is "nothing changes," rephrase it or provide tooling that enforces it automatically.

### What MOAT makes verifiable — and what it doesn't

MOAT builds auditable registries. You can verify that content you received matches what the registry attested, that the registry's signature is logged in a transparency ledger, and that nothing was tampered with in transit.

What MOAT does not answer:
- Whether registry operators are acting in good faith or curating content carefully
- Whether content is safe to use
- Whether a publisher is who they claim to be
- Whether external dependencies outside the content directory are trustworthy

Choosing which registries to trust is a user decision. MOAT provides the tools to verify what those registries claim — not the judgment about whether those claims are worth trusting.

---

## The Three People This Is For

**Publisher** — Wrote a SKILL.md or similar file. Shouldn't have to think about MOAT. Adds one workflow file, maybe runs a verify command.

**Registry operator** — Runs a content index. Adds trust signals to what they already do. Won't rebuild their pipeline for MOAT.

**Consumer** — Installs a skill or rule. Wants to know "is this the real thing, from who I think?" Not a cryptography tutorial.

When a design decision is genuinely ambiguous, run it through the panel personas in `panel/personas.md`. They represent Platform Vendor, Enterprise Security, Solo Publisher, Registry Operator, Spec Purist, and Remy (the aggregator operator who has seen real-world author behavior at ecosystem scale). Remy's agent definition is the sharpest filter: if it fails the "will humans actually do this?" test, it fails.

---

## What "Conforming Client" Means — and What It Doesn't

In MOAT protocol language, a **conforming client** is a tool that installs and manages AI agent content: a CLI install script, a package manager, or the content-management layer of a developer tool. It fetches registry manifests, verifies content hashes, maintains the lockfile, and enforces revocation blocks.

**A conforming client is NOT an AI agent runtime.**

Claude Code, Windsurf, Gemini, Cursor — these are AI agent runtimes. They are the downstream consumers of content that a MOAT-conforming install tool has already verified and placed on disk. MOAT says nothing about how AI agent runtimes behave, process, or execute installed content. The protocol boundary is the install step. Once content is installed and verified, MOAT's job is done.

This distinction matters for spec decisions:
- "Client behavior on revocation" means the install tool refuses to make the content available — not that an AI runtime detects and blocks it at execution time.
- The lockfile is an install tool artifact, not a runtime artifact.
- moat-verify is a standalone verification script any user can run — it is not a client and does not install anything.

Do not conflate "conforming client" with "AI coding assistant." They operate at different layers and MOAT only specifies the install layer.

---

## Influences

The architecture draws from systems that solved similar problems in software package distribution. When facing a design decision, look to these for precedent — they represent years of implementation experience, failure modes, and hard-won lessons we should learn from rather than repeat.

### npm

npm established the lockfile as the mechanism that makes "you should verify what you install" actually happen at scale. Verification only works when tooling does it automatically — not when specs require users to do it manually. npm also demonstrates what happens without namespace enforcement: typosquatting attacks become trivially easy when any publisher can claim any name.

**Look to npm for:** Lockfile design, namespace conflict lessons, the cost of making security optional rather than automatic.

### Go Modules / sum.golang.org

Go modules give every module a content-addressed identity — the hash *is* the identity. sum.golang.org acts as a transparency log: once a module is published at a given version, that hash is recorded and cannot change. This is the closest precedent to MOAT's Rekor usage and registry-side attestation model.

The key lesson: immutability is what makes content-addressed distribution trustworthy. If content at a given hash can change, the hash is meaningless as an identity.

**Look to Go for:** Hash-as-identity design, transparency log usage, module proxy architecture, and what immutability guarantees actually require.

### TUF (The Update Framework)

TUF directly addresses MOAT's open Issue 16 (anti-rollback / anti-freeze). TUF requires all metadata to carry an expiry timestamp — a valid-but-old manifest is not a valid manifest. It also separates roles: who can sign what, and what happens when a signing key is compromised.

The key lesson: a security protocol without freshness semantics is vulnerable to replay attacks. "Old but valid" must not mean "still trusted."

**Look to TUF for:** Anti-rollback design, freshness semantics, role separation in trust models, key rotation and compromise handling.

### Sigstore / Rekor

Already integrated into MOAT. Sigstore's keyless OIDC signing model solves the problem of verifying signatures without requiring a public key registry — tying signing identity to an existing trusted identity provider (GitHub Actions OIDC) without separate key distribution infrastructure.

**Look to Sigstore for:** Signing mechanics, identity binding, transparency log interaction, and anything touching the keyless signing path.

### SLSA (Supply Chain Levels for Software Artifacts)

SLSA's graduated levels model — not binary trusted/untrusted, but a spectrum of assurance — directly influenced MOAT's trust tier design. A binary trust model creates pressure to claim the highest level or not adopt at all. Graduated levels let the spec describe the current state honestly and improve incrementally without demanding perfection upfront.

**Look to SLSA for:** How to frame trust levels without creating alert fatigue, and how to describe what each level guarantees vs. implies.

---

## For AI-Assisted Sessions

Before landing on a recommendation or drafting spec language, apply these checks:

**The day-one test.** What does the ecosystem look like the moment this spec ships — not after ideal adoption? If thousands of existing content items don't conform on day one, the spec needs to acknowledge that, not pretend conformance will materialize.

**The copy survival test.** Content gets copied between repos constantly. Aggregators scrape and re-host without reading specs. Does this design element survive being copied to a different repo by someone who never read the spec? If it depends on a sidecar file an aggregator will strip, it is fragile by design.

**The "works fine without it" test.** If a requirement can be ignored with no observable consequence, it will be ignored. Before using MUST or SHOULD, confirm there is a way to detect or enforce non-compliance. If there isn't, it's a suggestion.

**The enforcement question.** What is the enforcement mechanism? If the answer is "trust that people will comply," either provide tooling that enforces it automatically or remove the normative language.

**The reference implementation question.** If implementing a requirement correctly requires more than one non-obvious step, is there a reference implementation? Complex algorithms without reference implementations will produce divergent implementations that cannot be trusted to agree.
