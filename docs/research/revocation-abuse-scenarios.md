# Revocation System Abuse Scenarios

**Date:** 2026-04-07
**Status:** Resolved — mitigations incorporated into spec design
**Source:** Design review session

---

## Core Design Principle

**Publisher revocations are signals. Registry revocations are authoritative.**

| Revocation source | Client behavior |
|---|---|
| Publisher only (Rekor entry, not yet in registry manifest) | MUST warn prominently; MUST NOT silently ignore |
| Registry only (in manifest) | MUST block for `malicious`/`compromised`; SHOULD warn for `deprecated`/`policy_violation` |
| Both publisher and registry | MUST block; surface as high-confidence dual-revocation signal |
| Unusual volume from single source in short time window | Flag for user review; registry SHOULD apply rate limiting |

Publisher revocations do not bypass the registry for hard blocks. This prevents rage-quit and compromised-account scenarios while preserving the independent signal value for the compromised-registry scenario.

---

## Abuse Scenarios

### Scenario 1: Rage-Quit / Mass Publisher Revocation

**Attack:** Publisher gets angry, has a breakdown, or changes their mind. Uses the Publisher Action in revocation mode to flag all their content. Thousands of users can't install their skills.

**This is the npm left-pad problem with a revocation mechanism attached.**

**Mitigation:**
- Publisher revocations are warnings, not hard blocks
- Registry is the gating authority for hard blocks
- Registry reviews before updating manifest:
  - `deprecated` / `policy_violation` reasons: registry MAY auto-accept
  - `malicious` / `compromised` reasons: registry SHOULD verify before hard-blocking

---

### Scenario 2: Compromised Publisher Account Mass Revocation

**Attack:** Attacker gains access to a publisher's GitHub account. Uses the Publisher Action to create Rekor revocation entries for all the publisher's content. Legitimate author has no way to stop it in real time.

**Mitigation:**
- Same circuit breaker as Scenario 1 — publisher revocations are warnings to registries, not direct client-side blocks
- Registries SHOULD implement anomalous revocation detection: unusual volume of revocations from a single OIDC identity in a short window → rate limit processing, flag for manual review
- A wave of `compromised` revocations from a single identity is itself suspicious — may indicate a second-order compromise

---

### Scenario 3: Malicious Registry Revokes Legitimate Content

**Attack:** A registry operator decides to harm a competitor's content, or the registry is acquired by a bad actor, and starts issuing false revocations against legitimate skills. Users who have that registry trusted see content blocked.

**Mitigation:**
- Attribution is the key control. Clients MUST show the source of every revocation: *"Registry X has revoked this content."*
- Clients SHOULD surface per-registry revocation counts in their trust UI — a registry issuing anomalous revocation volumes is visible
- Cross-registry visibility: if multiple trusted registries have not revoked a skill but one newly added registry has, the pattern is obvious
- Users can remove a malicious registry

**Limitation:** Users who only have the malicious registry trusted have no cross-registry protection. The spec should recommend conforming clients ship with a default well-known community registry that maintains a public revocation list (analogous to browser certificate revocation lists).

---

### Scenario 4: Attacker Republishes Revoked Content Through a New Registry

**Attack:** Malicious content is revoked by Registry A. Attacker sets up Registry B without the revocation. Users who only trust Registry B can still install.

**Mitigation:**
- Cross-registry hash matching: conforming clients SHOULD check all trusted registries' revocation lists against all installed content hashes
- If a user trusts Registry A and Registry B, Registry A's revocation surfaces regardless of which registry distributed the content
- Limitation: single-registry users have no cross-registry protection (see Scenario 3 mitigation)

---

### Scenario 5: Webhook Flooding

**Attack:** Attacker discovers a registry's webhook endpoint and floods it with fake revocation or attestation notifications.

**Mitigation:**
- Webhook payloads MUST be signed by the publisher's OIDC identity — unsigned or unverifiable payloads are rejected before processing
- Registries SHOULD rate-limit webhook calls per source identity
- Rekor entries cost compute — mass fake notifications backed by real Rekor entries are expensive to generate

---

## Publisher-Side Revocation Design

### How it works

Publisher Action gains a revocation mode. Publisher adds a revocation entry to `moat-attestation.json` and triggers the action:

```json
{
  "revocations": [
    {
      "content_hash": "sha256:abc123...",
      "revoked_at": "2026-04-07T10:00:00Z",
      "reason": "compromised",
      "rekor_log_id": "24296fb24b8ad77b..."
    }
  ]
}
```

Action posts a signed Rekor revocation entry using the publisher's CI OIDC identity. Optionally notifies registry via webhook (same channel as attestation notifications).

### Why this helps with registry compromise

If a registry's signing key is compromised, an attacker can sign and distribute malicious content. The legitimate author can independently post a Rekor revocation entry using their GitHub Actions identity — a completely separate key. The attacker would need to compromise both the registry signing key AND the publisher's GitHub Actions identity to suppress the revocation signal.

### Out-of-band revocation

A publisher whose GitHub Actions is compromised cannot use the Publisher Action to revoke. Out-of-band registry contact MUST remain available. The spec cannot make publisher-side revocation the only mechanism.

---

## What This Changes in the Spec

The existing revocation section (Issue #8) defines registry-controlled revocation. The following additions are needed:

1. **Publisher-side revocation via Rekor** — a separate, independently verifiable signal that clients check directly. Not the same channel as `revocation_feed_url`.

2. **Client handling of publisher revocations** — MUST warn prominently; MUST NOT hard block without registry confirmation (except when registry confirmation is also present).

3. **Anomalous volume detection** — registries SHOULD rate-limit and flag unusual revocation volumes per source identity.

4. **Attribution requirement** — clients MUST show the source of every revocation signal, including publisher identity for publisher-side revocations.

5. **Dual-revocation display** — when both publisher and registry have revoked the same hash, clients SHOULD surface this as a higher-confidence signal with distinct UI treatment.

6. **Webhook security** — webhook payloads carrying revocations MUST be signed by the publisher's OIDC identity and verified before processing.
