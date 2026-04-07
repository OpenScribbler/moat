# Dual Attestation & Publisher Action Design

**Date:** 2026-04-07
**Status:** Resolved
**Source:** Coworker feedback review + panel analysis

---

## The Feedback

> "In GitHub, there are 2 layers of trust — the repository is trusted, but there is also a per-release trust (hash of the commit/release) — should MOAT consider both? Note: This is similar in Golang as well as there are specific Go repositories, but when you define dependencies, the specific versions are hash locked."

---

## The Two-Layer Pattern

| System | Layer 1 (source identity) | Layer 2 (release pinning) |
|---|---|---|
| GitHub | Repo/org trust | Per-release commit hash |
| Go modules | Module path (`github.com/user/mod`) | `go.sum` checksum per version |
| MOAT (pre-decision) | Registry trust | Content hash in manifest |

MOAT's existing two layers mirror the pattern — but there's a gap: if a registry's signing key is **compromised**, there is no independent second layer to catch it. The registry could sign malicious content with a valid key, and clients would verify and install it.

Source co-signing via the Publisher Action existed but was informal — "optional and additive," not a named tier.

---

## Decision: Dual-Attested as a Named v1 Tier

### Three tiers

| Tier | What it means |
|---|---|
| **Dual-Attested** | Registry-signed (Rekor entry 1) AND source repo CI-signed via Sigstore (Rekor entry 2). Two independent Rekor entries for the same content hash. Survives registry key compromise. |
| **Signed** | Registry-signed with a Rekor transparency log entry. Fully trusted. Absence of Dual-Attested is NOT a negative signal. |
| **Unsigned** | No MOAT provenance. Works, but labeled clearly. |

**Critical constraint:** `Dual-Attested` content will be rare at launch. Clients MUST NOT treat the absence of `Dual-Attested` as a negative signal — only its presence as a positive one.

### Why v1 instead of v2

Retrofitting a third tier later is a breaking change to the trust model. Users learn "Signed = trusted." Adding a superior tier later implies "Signed was never quite enough." Shipping it in v1 — even empty at launch — lets the tier fill naturally as Publisher Action adoption grows.

---

## Publisher Action Design

### What it does

A single workflow file added to a source repo:

```yaml
# .github/workflows/moat.yml
uses: moat-spec/publisher-action@v1
```

On push, the action:
1. Detects AI content in the repo (skills, hooks, rules, MCP configs)
2. Computes content hashes using the MOAT algorithm
3. Signs via Sigstore keyless OIDC — no keys, no secrets, uses GitHub Actions identity automatically
4. Posts a Rekor entry (source CI attestation)
5. Updates `moat-attestation.json` in the repo root
6. Badge in README reflects attestation status

### `moat-attestation.json`

**Location:** Repo root. One file per repo, not per content directory.

**Format:**
```json
{
  "schema_version": "1",
  "attested_at": "2026-04-07T14:00:00Z",
  "items": [
    {
      "name": "summarizer-skill",
      "content_hash": "sha256:abc123...",
      "rekor_log_id": "24296fb24b8ad77a...",
      "rekor_log_index": 12345678
    }
  ]
}
```

**Critical:** `moat-attestation.json` MUST be excluded from content hashing. It is MOAT infrastructure, not content. Add to the explicit exclusion list alongside VCS directories (`.git`, `.svn`, etc.).

### Bootstrapping pattern

First push: action runs → computes hashes → writes `moat-attestation.json` → commits file back to repo. That commit would ordinarily re-trigger the action. Resolution: GitHub Actions with `GITHUB_TOKEN` do not trigger other workflow runs by default. Publisher Action MUST document this behavior and MUST include a guard that detects "this commit is from the MOAT action" to prevent any edge case re-runs.

### Badge

Uses Shields.io reading from the raw `moat-attestation.json` URL in the repo. Badge asserts per-hash attestation, not just per-repo CI status — it's a verifiable claim, not decoration.

```markdown
![MOAT Dual-Attested](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/alice/my-skills/main/moat-attestation.json)
```

Badge data structure includes count of attested items and last attestation timestamp.

---

## Hybrid Webhook (Passive + Optional Active)

**Default (passive):** Publisher Action signs and stops. Registry discovers attestation on its own crawl cycle. No registry coordination required. Authors never need to know which registries exist.

**Optional (active):** Publisher configures a registry webhook URL. Action notifies registry immediately after signing for fast propagation.

```yaml
uses: moat-spec/publisher-action@v1
with:
  registry-webhook: ${{ secrets.MOAT_REGISTRY_WEBHOOK }}  # optional
```

**Webhook carries both directions:**
- Attestation notification: "I just attested hash X, come get it"
- Revocation notification: "I'm revoking hash X, reason: compromised"

Same channel, two event types. Payloads MUST be signed by the publisher's OIDC identity. Unsigned webhook payloads MUST be rejected by registries.

**Recommendation for registries:** Registries serving large content volumes SHOULD implement the ingest webhook endpoint to enable low-latency revocation propagation.

---

## Reference Verification Script (`moat-verify`)

Ships alongside `moat_hash.py` as a first-class spec artifact.

Takes a content directory and checks:
1. Computes the content hash locally
2. Looks up the hash in a trusted registry's manifest
3. Verifies the registry's Rekor attestation entry
4. Optionally verifies the publisher's CI Rekor attestation entry
5. Prints a human-readable trust report

**Required behavior:**
- If Rekor is unavailable: fail with explicit message — "cannot verify Rekor attestation, transparency log unreachable." Never silently pass.
- Output must state explicitly what was NOT checked. "This script verified X. It did NOT verify that the registry is one you should trust, or that the OIDC identity in the publisher attestation is the legitimate owner of this repository."

**Purpose:** Any user can verify any MOAT-attested content without depending on a specific client implementation. Makes the trust model auditable end-to-end.

---

## Panel Notes

- **Enterprise Security:** "Option B (Dual-Attested tier) is required for high-stakes deployment. Compromised registry scenario is not theoretical."
- **Platform Vendor:** "Right long-term answer, potentially wrong v1 answer — but retrofitting a tier later is harder than launching it empty."
- **Solo Publisher:** "As long as it's Sigstore keyless and a single workflow file, I'm in. I won't manage keys."
- **Registry Operator:** "Implementable only if publisher co-signing is Sigstore-only. SSH key publisher co-signing creates runtime key-lookup dependencies I can't accept."
- **Spec Purist:** "Two independent Rekor entries for the same content hash — that's the actual second layer. Not just two signatures."
- **Remy:** "The utility exchange is real. Badge in README, zero key management, one workflow file. Publisher gets direct benefit from compliance. This is unlike most spec requirements where the author does work and only consumers benefit."
