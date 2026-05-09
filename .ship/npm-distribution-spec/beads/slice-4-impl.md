Slice 4 impl bead — TDD green phase.

Append three sections to `specs/npm-distribution.md`:

1. ## Backfill Attestation by Registry (normative) — asserts the same registry_signing_profile is used for backfill and normal Registry attestations; clarifies the publisher-counter-signature distinction is encoded in the Trust Tier (Signed vs Dual-Attested), not in a second profile field; fixes source_uri for npm-only items where no Source Repository is known by referencing the manifest content-entry schema at moat-spec.md:766-807; preserves the (name, type) uniqueness invariant.

2. ## npm Provenance (informative) — observed-when-present, recommended-but-not-required, orthogonal to MOAT Trust Tiers; states that a Conforming Client MAY surface npm provenance presence in its UI as a separate row from the Trust Tier; states explicitly: it MUST NOT use npm provenance to compute or override the Trust Tier.

3. ## Scope — closing section with **Current version:** and **Planned future version:** bold-label one-liners. "Planned future version" reserves room for other registry transports (PyPI, Cargo, etc.) without committing to them.

Green phase: `.ship/npm-distribution-spec/conformance/slice-4.sh` exits 0.

Checkpoint: a Registry Operator reads the Backfill section and can answer "yes, I can attest an existing npm package without the Publisher's cooperation, using my normal registry_signing_profile" without consulting any other document; a Conforming Client implementer reads the npm Provenance section and can answer "no, npm provenance does not change the Trust Tier" without ambiguity.
