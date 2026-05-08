---
title: How it works
description: How MOAT works — three roles, one auditable chain of custody.
---

MOAT makes the provenance of AI agent content verifiable. The protocol has three roles — Publisher, Registry, Consumer — each with a distinct responsibility in a chain that ends with a cryptographically confirmed answer to: "is this what I think it is, from who I think it's from?"

---

## Step 1: Publisher signs

When a publisher pushes a change to their GitHub repository, the Publisher Action runs automatically. For each content item it finds (skills, rules, sub-agents, etc.), it:

1. Computes a SHA-256 content hash of the entire content directory
2. Constructs a canonical payload: `{"_version":1,"content_hash":"sha256:<hex>"}`
3. Signs this payload using **Sigstore keyless OIDC signing** via `cosign sign-blob`

Keyless signing means there is no private key to manage or rotate. Instead, the signing identity is the GitHub Actions OIDC token for that workflow run — the certificate records the exact repository and workflow path that produced the signature. The signed entry is written to the **Rekor transparency log** and cannot be removed or modified.

The result is a `moat-attestation.json` on the repository's `moat-attestation` branch, recording the Rekor log index for each signed item. Any third party can fetch this entry and confirm the signature independently.

This step is optional. Publishers who do not run the Publisher Action still have their content indexed by registries — they just don't qualify for the `Dual-Attested` tier.

---

## Step 2: Registry attests

A registry is a GitHub repository that runs the Registry Action on a daily schedule. For each source repository it is configured to crawl, the action:

1. Discovers content items in the source repository
2. Computes the content hash for each item
3. Signs the same canonical payload format with `cosign sign-blob`, creating its own Rekor entry for each item
4. If the source repository has a `moat-attestation.json`, fetches the publisher's Rekor entry and verifies it matches the same content hash — this is what earns the `Dual-Attested` tier
5. Builds a `registry.json` manifest listing all attested items with their Rekor log indices, trust tiers, and registry signing profile
6. Signs the manifest itself as a bundle (`.sigstore`) and commits both files to the `moat-registry` branch

The resulting manifest is tamper-evident: the manifest lists what the registry attested, and the `.sigstore` bundle proves the manifest came from this registry's CI workflow. The Rekor entries for each item prove that specific content hash was attested at a specific time.

---

## Step 3: Consumer verifies

A consumer runs `moat-verify` against a content directory, pointed at a registry manifest URL. The verification steps are:

1. **Compute the content hash** of the local directory
2. **Fetch the registry manifest** and verify its `.sigstore` bundle — confirms the manifest came from the registry's CI workflow and is logged in Rekor
3. **Look up the content hash** in the manifest — confirms the registry attested this exact content
4. **Verify the per-item Rekor entry** — fetches the entry from `rekor_log_index`, reconstructs the canonical payload, confirms the Rekor entry covers the same content hash, and verifies the signing identity matches the registry's declared profile
5. **Verify publisher attestation** (optional, via `--source`) — checks the publisher's independent Rekor entry from their `moat-attestation.json`

Each step requires Rekor connectivity. Rekor unavailability is a hard failure — `moat-verify` never passes silently when the transparency log is unreachable.

After a conforming install tool runs this verification at install time, it stores the result in a **lockfile**. Future offline verification (`--lockfile` mode) checks the content hash against the lockfile and verifies the stored attestation bundle without Rekor connectivity — proving the content matches what was verified at install.

---

## Trust tiers

The trust tier recorded in the registry manifest reflects how many independent parties have attested the content:

| Tier | What happened |
|---|---|
| `Dual-Attested` | The registry signed the content hash AND the publisher independently signed the same hash in their own CI. Neither can tamper with the other's Rekor entry. |
| `Signed` | The registry signed the content hash. The publisher did not run the Publisher Action, or publisher verification failed. |
| `Unsigned` | The registry indexed the content but did not produce a Rekor entry for it. |

Higher tiers are not "more safe" — they reflect more independent attestation chains. Content safety is outside MOAT's scope.

---

## What MOAT does and does not verify

MOAT makes the following verifiable:

- The content directory matches the hash the registry attested
- The registry's attestation is logged in the Rekor transparency ledger and cannot be retroactively altered
- The attestation was signed by the OIDC identity declared in the registry manifest
- (With `Dual-Attested`) The publisher independently attested the same content hash from their CI

MOAT does not answer:

- Whether registry operators are acting in good faith or curating content carefully
- Whether content is safe to use
- Whether a publisher OIDC identity is the legitimate owner of the source repository
- Whether external dependencies outside the content directory are trustworthy

Choosing which registries to trust is a user decision. MOAT provides the tools to verify what those registries claim — not the judgment about whether those claims are worth trusting.

---

## The transparency log

Every attestation in MOAT — publisher signatures and registry item attestations — is recorded in the **Rekor** transparency log at `rekor.sigstore.dev`. Rekor is append-only: entries can be added but never removed or modified. This means:

- Any attestation MOAT produces is permanently auditable by anyone
- A content hash attested at a given Rekor index cannot be retroactively substituted
- Registry revocation works by marking content in the manifest — not by erasing the original attestation

The Rekor entries MOAT creates record content hashes, not content. The content of a skill or rule file is never uploaded to Rekor.
