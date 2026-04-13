---
title: What is MOAT?
description: An introduction to the Model for Origin Attestation and Trust protocol.
---

MOAT (Model for Origin Attestation and Trust) is an open protocol for provenance and integrity of AI agent content — skills, rules, hooks, MCP configs, sub-agents, and more.

## The problem

AI agent content installs directly into your environment and runs with your credentials. There is currently no standard way to know whether a skill you installed came from who you think, or whether it was modified after the publisher signed off.

## What MOAT provides

MOAT makes tampering detectable. It gives publishers, registries, and consumers a shared protocol for:

- **Signing** content at distribution time (Publisher Action)
- **Attesting** signed manifests in a registry (Registry Action)
- **Verifying** content hashes against registry attestations at install time (moat-verify)

Verification happens automatically when a conforming install tool is used. The transparency log (Rekor) records every attestation, making the chain of custody auditable.

### No keys to manage

MOAT uses keyless signing — there are no private keys to generate, store, or rotate. The signing identity is the OIDC token your CI already produces. When GitHub Actions runs a workflow in your repository, that workflow gets a short-lived token that says "this ran in `owner/repo` on branch `main`." MOAT uses that token as the signing identity and logs it to a public transparency ledger. The signature is permanently auditable, but you never touch a key.

This is fundamentally different from PGP or traditional code signing, where adoption has historically failed because of key management overhead. MOAT's model is closer to how people already trust forges: if GitHub says a commit is verified, you trust that. MOAT extends that same trust signal — your CI identity — into a cryptographically verifiable, permanently logged attestation that works across registries and survives content being copied between systems.

## What MOAT does not provide

MOAT covers provenance and integrity. It does not:

- Score content for safety or behavioral risk
- Verify publisher identity beyond what the signing OIDC token provides
- Make trust decisions — those remain yours

Choosing which registries to trust is a user decision. MOAT gives you the tools to verify what those registries claim.
