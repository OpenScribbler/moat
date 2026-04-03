# MOAT Trust Anchor Panel Consensus

**Date:** 2026-04-03
**Rounds:** 3 (of 5 max)
**Panelists:** Platform Vendor, Enterprise Security, Solo Publisher, Registry Operator, Spec Purist

---

## Q1: `source_repo` + `publisher_identity` — 5-0 accepted (1 recorded objection)

**Decision:** Keep `source_repo` unchanged as the canonical code location. Add `publisher_identity` as a new field:
- REQUIRED when the signing identity differs from the `source_repo` owner (platform-managed/delegated publishing)
- Absent for direct-publish (no new friction for solo publishers)

**Companion requirements:**
- Spec MUST define "differs" programmatically: Fulcio-extracted Source Repository URI vs `source_repo` mismatch triggers requirement
- Verifiers MUST surface the `publisher_identity` distinction to users — delegated and direct publish are not equivalent trust signals
- Define normative sentinel for direct-publish case (explicit empty vs field omission)

**SPu objection (recorded):** Field acceptable only with companion normative verifier-behavior statement. Without it, "normative theater."

---

## Q2: Sigstore Trust Root — 4-1 resolved (Round 1)

**Decision:** Define `sigstore_trust_root` field in registry manifests/content bundles.
- Public-good Sigstore instance as recommended default (non-normative guidance)
- Consumer policy governs which roots to trust
- Enterprise deployments configure own TUF root through same field

**SPu dissent:** Defaults should be tooling, not protocol. Group accepted as non-normative recommendation.

---

## Q3: Rollback Protection — 4-1 accepted (1 recorded dissent)

**Decision:** Two-part approach:

1. **Non-normative WARNING** in Security Considerations:
   - Source binding amplifies rollback risk
   - Rekor timestamps attest signing time, NOT currency
   - Source binding does not imply content is the most recent valid version

2. **Normative SHOULD** recommending registries maintain a signed latest-version manifest, delegating freshness enforcement to the registry layer

**SPu dissent (recorded):** SHOULD without testable compliance criteria is a spec quality problem. Prefers pure non-normative.

---

## Q4: Bootstrap / First-Publish Trust — 5-0 (Round 1)

**Decision:**
- Formally acknowledge TOFU in normative text: "On first publish, `source_repo` is self-asserted. Verifiers MUST treat this as an unvalidated claim until the signer has an established publish history."
- SHOULD-level recommendation that registries implement first-publish authorization policies
- `repository_owner_id` (numeric, immutable) as RECOMMENDED optional field for account resurrection protection

---

## Q5: sigstore-a2a Alignment — 5-0 (Round 1)

**Decision:**
- Reference as related work in non-normative section
- Scope differentiation: sigstore-a2a = agent cards (runtime identity); MOAT = content packages (installable artifacts)
- No format coupling at v1
- Coordinate on Fulcio OID extension usage to prevent divergence

---

## Spec Changes Implied

### New field: `publisher_identity`
- Location: `meta.yaml`
- Semantics: Who signed (when different from source_repo owner)
- Normative: REQUIRED when Fulcio identity ≠ source_repo; absent for direct-publish
- Verifier obligation: MUST surface to users; MUST NOT treat as equivalent to direct-publish

### New field: `sigstore_trust_root`
- Location: Registry manifest / content bundle
- Semantics: TUF root reference for the Sigstore instance used
- Default: Public-good instance (non-normative recommendation)

### New field: `repository_owner_id`
- Location: `meta.yaml` (optional)
- Semantics: Numeric, immutable platform ID for account resurrection protection
- Normative level: RECOMMENDED

### Spec sections to update
- Section 2 (Introduction): Platform-first framing + trust chain narrative
- Section 9.2: Source binding verification step (use OID 1.3.6.1.4.1.57264.1.12)
- Section 11 (Security Considerations): Rollback WARNING + TOFU acknowledgment
- New Appendix D: Provider OIDC formats + sigstore-a2a reference
