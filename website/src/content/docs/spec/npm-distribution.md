---
title: "npm Distribution"
description: "MOAT npm Distribution sub-specification — how MOAT attestations travel with content distributed through the npm Registry."
---
# npm Distribution Specification

**Version:** 0.2.0 (Draft)
**Requires:** moat-spec.md ≥ 0.7.1
**Part of:** [MOAT Specification](../moat-spec.md)

> The npm Distribution sub-spec defines how MOAT attestations travel with content distributed through the npm Registry: where the Content Hash is computed, what `package.json` metadata a Publisher embeds, when a Conforming Client refuses to materialize a Content Item, and how a Registry can attest a pre-existing npm package without Publisher cooperation.

---

## Content Hash Domain (normative)

A Content Item distributed via npm is published as an npm package. Each published version is delivered as a Distribution Tarball — a gzipped tar archive identified by an npm-assigned tarball URL.

**Hash input domain (normative — MUST):** The MOAT Content Hash for a Content Item distributed via npm is computed over the **Content Directory** (see [`lexicon.md` §Content Directory](../lexicon.md)) inside the unpacked Distribution Tarball. A Conforming Client MUST resolve the Content Directory using the [Content Directory](#content-directory-normative--must) section's default and subdirectory-mode rules — reading the `moat.tarballContentRoot` field in the published `package.json` when present, applying the default rule when absent — and MUST compute the Content Hash over its contents.

**Algorithm (normative — MUST):** The hash algorithm is unchanged from the core protocol; the Conforming Client computes the Content Hash using the algorithm specified in [`moat-spec.md` §Content Hash](../moat-spec.md#content-hash) and implemented by [`reference/moat_hash.py`](../reference/moat_hash.py). Only the input directory differs from the GitHub-Distribution Channel: where a GitHub-distributed Content Item hashes a directory in the source repository, an npm-distributed Content Item hashes the Content Directory inside the unpacked tarball. The algorithm itself — file ordering, normalization, exclusion list — is identical and MUST NOT be re-implemented in the Conforming Client.

**Copy-survival (normative):** Because the hash input is the bytes inside the tarball's Content Directory and the algorithm is canonical, two Distribution Tarballs that contain byte-identical Content Directory contents produce the same Content Hash. A Conforming Client that has revoked a Content Hash MUST treat any tarball whose Content Directory hashes to the revoked value as revoked, regardless of which package name, version, or Registry the tarball was retrieved from.

**Relationship to the npm tarball SHA-512:** npm's own integrity primitive — the `dist.integrity` SHA-512 recorded by the npm Registry for each published version — covers the entire Distribution Tarball, including `package.json`, `README`, license files, and any other ancillary content. The MOAT Content Hash covers only the Content Directory. The two values are computed over different inputs and serve different purposes: the npm tarball SHA-512 protects against tarball-level corruption or substitution at the Registry boundary; the MOAT Content Hash binds attestations to the bytes of the Content Item itself. A Conforming Client MUST NOT substitute one for the other and MUST NOT use the npm tarball SHA-512 in place of the MOAT Content Hash for any normative check defined by this sub-spec or by `moat-spec.md`.

**Relationship to npm provenance:** npm provenance, when present, is observed-when-present and orthogonal to the MOAT Content Hash; the [npm Provenance](#npm-provenance-informative) section below states the full normative position.

---

## Content Directory (normative — MUST)

The Content Directory is the input domain to the MOAT Content Hash for a Content Item distributed via npm. This section fixes the rule a Conforming Client uses to resolve the Content Directory inside the unpacked Distribution Tarball.

**Default rule for Registry-backfilled items (normative — MUST):** The default rule applies when a Registry backfills attestation for a publisher-uncooperative npm package — i.e., for Registry-backfilled items only. In that case, the canonical Content Directory is the unpacked tarball root with `package.json` excluded from the hash domain. The exclusion is path-anchored to the tarball root: only the `package.json` at the root of the unpacked tarball is excluded; nested `package.json` files at deeper paths (for example, `pkg/package.json`) MUST NOT be excluded and MUST be included in the hash domain. The default rule lets a Registry compute the canonical Content Hash for any published version by fetching the Distribution Tarball and applying this rule, with no Publisher cooperation required (see [Backfill Attestation by Registry](#backfill-attestation-by-registry-normative)).

**Cooperative-Publisher `moat.tarballContentRoot` declaration (normative — MUST):** A cooperative Publisher MUST declare `moat.tarballContentRoot` explicitly in the published `package.json` `moat` block; the default rule is not available as a way for a cooperative Publisher to omit the field. The default rule is reserved for Registry-backfilled items where no cooperative Publisher declaration exists.

**Subdirectory mode (normative — MUST):** When `moat.tarballContentRoot` is set to a subdirectory path, the canonical Content Directory is that subdirectory's contents inside the unpacked tarball. Subdirectory mode applies no exclusions: every file under the named subdirectory — including any `package.json` at any depth under it — MUST be included in the hash domain. The default-mode `package.json` exclusion does not transfer into subdirectory mode.

**Fixed exclusion list — layering (informative):** The default-mode exclusion list is composed as two layers: a global layer (protocol-internal, defined in [`moat-spec.md` §Content Hashing](../moat-spec.md#content-hashing) and shared across every Distribution Channel) and a per-channel additive layer (declared in the relevant channel sub-spec). The two-layer composition is additive: the per-channel layer extends the global layer; it does not replace, narrow, or override it. For the npm Distribution Channel, the per-channel additive layer is fixed at exactly one file: `package.json` at the tarball root. Future amendments to either layer (for example, additional npm-injected metadata files) require a sub-spec amendment, not Publisher-side configuration.

**No Publisher extension of the exclusion list (normative — MUST NOT):** A Publisher MUST NOT extend either layer (the global layer or the npm per-channel additive layer) via `package.json` metadata or any other mechanism. The fixed-list rule is what makes Registry backfill deterministic; a Publisher who could extend the list could put arbitrary content outside the hash domain.

**No Conforming-Client honoring of Publisher-declared exclusions (normative — MUST NOT):** A Conforming Client MUST NOT honor any `package.json` field that purports to extend the default-mode exclusion list. The Conforming Client's hashing-domain decisions are bound by the protocol-level fixed list, not by Publisher-side configuration.

**Rationale (informative):** The default lets backfill work — a Registry can produce the canonical Content Hash for any published tarball without the Publisher having added a `moat` block. The `package.json` exclusion lets a Publisher write the Rekor log index back into `package.json` after signing without disturbing the canonical hash, breaking the chicken-and-egg between log-index population and signature stability. The path-anchored rule mirrors the root-only exclusion discipline used by [`reference/moat_hash.py`](../reference/moat_hash.py)'s `EXCLUDED_FILES` set: nested files of the same name have no protocol meaning at depth and MUST stay inside the hash domain so malicious content cannot hide there.

---

## Revocation at the Materialization Boundary (normative)

The materialization boundary is anchored at a single, precise point: **before any byte of the tarball is written outside the package manager's content cache**. This sub-spec names three operations that a Conforming Client MAY refuse at — `resolve`, `fetch`, and `unpack` — and the choice of which sub-operation to refuse at is a Conforming Client implementation matter. Whichever sub-operation the Client refuses at, no extracted bytes may land outside the package manager's content cache. MOAT's revocation MUSTs apply at this boundary; runtime gating of already-materialized content is outside MOAT's protocol scope.

**Mapping to common npm-client architectures (informative):** The cache-boundary anchor maps cleanly onto the architectures of widely-deployed npm clients without requiring any of them to change shape. `pacote` (npm's tarball-fetch and extract library) refuses at `fetch` or `unpack` and discards the partial cache entry on refusal — the streaming-extract path complies because the cache is the staging area, not the install target. Yarn Plug'n'Play stores fetched tarballs in its content-addressable `.yarn/cache` and only resolves modules from the cache at runtime; refusing before any byte enters that cache satisfies the anchor. The pnpm content-addressable store hard-links from `node_modules` into a global content-addressed cache; refusing before the global-store write satisfies the anchor by the same reasoning. The anchor exists to align the rule with these architectures, not to constrain them.

**Pre-materialization lockfile consultation (normative — MUST):** Before a Conforming Client fetches or unpacks a Distribution Tarball, it MUST consult the project-scoped MOAT lockfile at `.moat/npm-lockfile.json` — the npm-channel realization of the lockfile concept defined in [`moat-spec.md` §Lockfile](../moat-spec.md#lockfile) — and check the Content Hash for the requested package version against the lockfile's `revoked_hashes` list.

**Refusal on revoked Content Hash (normative — MUST):** If the Content Hash for the requested package version appears in `.moat/npm-lockfile.json`'s `revoked_hashes`, the Conforming Client MUST refuse to materialize the Content Item.

**Revocation reason code surfaced (normative — MUST):** On refusal under the pre-materialization hard block, the Conforming Client MUST surface the revocation reason code (inherited unchanged from the core protocol enum) in its error output. The reason code is what gives the End User a routable explanation for the refusal.

**Lockfile authoritative over remote source (normative — MUST NOT):** The lockfile is authoritative; the Conforming Client MUST NOT proceed to fetch on the assumption that a remote source overrides a locally-recorded revocation.

**Persistence (normative):** Once a Content Hash is recorded in `.moat/npm-lockfile.json`'s `revoked_hashes`, the persistence and lockfile-authoritative semantics from [`moat-spec.md` §Lockfile](../moat-spec.md#lockfile) apply unchanged. This sub-spec does not redefine the lockfile schema or the persistence rule; it only pins the on-disk filename for the npm channel (`.moat/npm-lockfile.json`, one file per project root, source-tree-checked-in like npm's own `package-lock.json`). The `npm-` filename prefix reserves parallel filenames for future per-channel lockfiles (`.moat/pypi-lockfile.json`, `.moat/cargo-lockfile.json`, etc.) without cross-channel collision.

**Resolve-time logging (normative — MUST):** A Conforming Client that refuses to materialize a Content Item due to revocation MUST emit a structured log entry at resolve time identifying the package name, version, Content Hash, revocation reason code, and the `source` of the revocation (the literal value `lockfile` when the block originated from the local lockfile's `revoked_hashes`, or `registry_manifest` when it originated from a Registry Manifest revocation entry). The log entry is the audit anchor; without it, an operator cannot distinguish a genuine block from a silent skip, nor reconstruct which authority's revocation triggered the refusal.

**No per-hash operator escape hatch for Registry-source revocations (normative — MUST NOT):** A Conforming Client MUST NOT honor any per-hash, per-entry operator escape hatch from the pre-materialization hard block when the revocation is Registry-source — that is, when the Content Hash is recorded in `.moat/npm-lockfile.json` `revoked_hashes` as the npm-channel realization of [`moat-spec.md` §Revocation](../moat-spec.md#revocation)'s Registry row (see `moat-spec.md:636`). Revocation refusal for Registry-source revocations is a protocol-level decision; an operator who has done out-of-band investigation may correct the authoritative source (remove the entry from the local lockfile, or refuse to sync a Registry Manifest revocation they reject) but MUST NOT instruct the Conforming Client to proceed with a Content Hash whose presence in `revoked_hashes` is currently authoritative. Publisher-source revocations are governed by [`moat-spec.md` §Revocation](../moat-spec.md#revocation)'s Publisher row at `moat-spec.md:636`, which allows use with explicit End User confirmation; this sub-spec adds no override beyond what core defines for the Publisher source. The trade-off is recorded in [`docs/adr/0010-…`](../docs/adr/0010-hard-revocation-no-operator-override.md), which supersedes ADR-0007.

**Override env vars, CLI flags, and config entries treated as absent (normative — MUST):** Env vars, command-line flags, and configuration entries that purport to allow a Registry-source-revoked Content Hash to materialize MUST be treated as if absent by a Conforming Client. The Client MUST NOT consult them, MUST NOT emit a warning that they could have changed the outcome, and MUST NOT log them as having been overridden — they have no effect on the protocol and surface no signal to the operator that they were observed.

**Post-materialization revocation (informative):** A revocation that arrives after a Distribution Tarball has been materialized has no normative effect at the materialization boundary; the Content Item is already on disk. Runtime gating of execution by an AI agent runtime is outside MOAT's protocol scope (see [`moat-spec.md` §Conforming Client](../moat-spec.md#conforming-client) for the protocol-boundary definition). A Conforming Client SHOULD surface a post-materialization revocation in its operational logs when the lockfile is updated, so that operators can audit which already-installed Content Items have been revoked, but this sub-spec defines no post-materialization MUST.

---

## package.json moat Block (normative)

A Publisher distributing a Content Item via npm declares MOAT attestation by adding a top-level `moat` block to the published `package.json`. This section fixes the schema of that block.

Editorial note on field naming: the schema mixes camelCase (`tarballContentRoot`, `publisherSigning`) for fields that are local to this sub-spec with snake_case (`distribution_uri`, `source_uri`, `rekor_log_index`) for fields whose semantics mirror existing core-protocol or Rekor-bundle field names — the snake_case form preserves spelling parity with the upstream identifier rather than renaming it at the sub-spec boundary.

| Field | Required | Description |
|-------|----------|-------------|
| `moat.tarballContentRoot` | REQUIRED | String. Names the tarball-relative subdirectory whose contents are the **Content Directory** for this Content Item — the canonical concept defined in [`lexicon.md` §Content Directory](../lexicon.md) and resolved by the [Content Directory](#content-directory-normative--must) section's default and subdirectory-mode rules. A cooperative Publisher MUST declare this field explicitly. The field MAY be omitted only on Registry-backfilled items (for which the Registry, not the Publisher, populates the canonical Content Hash by applying the Default rule — unpacked tarball root with the root `package.json` excluded). When present, the value MUST resolve inside the unpacked tarball. |
| `moat.distribution_uri` | REQUIRED for cooperative Publishers | String. The canonical, dereferenceable URL of the published Distribution Tarball on the npm Registry (typically `https://registry.npmjs.org/<package-name>/-/<package-name>-<version>.tgz`). The field is **distinct from** `source_uri` in the Registry Manifest entry: `source_uri` names the upstream Source Repository (a git URL — where the content was authored), while `distribution_uri` names where this version's bytes can be fetched on this channel. Normative declaration, backfill, resolution, and non-conflation rules are stated in the four MUST sentences below the schema table. |
| `publisherSigning` | OPTIONAL | Object (under the top-level `moat` block). Discloses the Publisher's signing identity so a Conforming Client can locate and verify the Publisher's Sigstore signature in the Rekor transparency log. The Publisher's bundle itself is NOT embedded in `package.json`; it lives in Rekor. When `publisherSigning` is absent, the package has no Publisher-attested signing identity (a Registry attestation in `moat.attestations[]` MAY still be present). |
| `publisherSigning.issuer` | REQUIRED | String. The OIDC issuer URL of the Publisher's signing identity (typically `https://token.actions.githubusercontent.com` for GitHub Actions). REQUIRED when the `publisherSigning` block is present. Carries the same semantics as the `issuer` field of the [`signing_profile`](../moat-spec.md#signing_profile) defined in [`moat-spec.md` §signing_profile](../moat-spec.md#signing_profile). |
| `publisherSigning.subject` | REQUIRED | String. The OIDC subject (workload identity) of the Publisher's signing identity (typically the GitHub Actions workflow path, e.g. `https://github.com/<owner>/<repo>/.github/workflows/<file>@refs/heads/<branch>`). REQUIRED when the `publisherSigning` block is present. Carries the same semantics as the `subject` field of the [`signing_profile`](../moat-spec.md#signing_profile) defined in [`moat-spec.md` §signing_profile](../moat-spec.md#signing_profile). |
| `moat.attestations` | REQUIRED | Array of Registry attestation entries. The array MAY be empty; an empty array signals that no Registry has counter-signed this Content Item. A Conforming Client treats an empty array — together with an absent `publisherSigning` block — as the `Unsigned` Trust Tier. |
| `moat.attestations[].role` | REQUIRED | String enum. The only currently defined value is `"registry"`. The field is preserved for forward compatibility with future role types. |
| `moat.attestations[].bundle` | REQUIRED | String. Base64-encoded Sigstore protobuf bundle v0.3 (Cosign Bundle, `--new-bundle-format`) covering the Registry's Canonical Attestation Payload, pinned by [`moat-spec.md` §Signature Envelope](../moat-spec.md#signature-envelope). |
| `moat.attestations[].rekor_log_index` | REQUIRED | Integer. The Rekor transparency-log index recorded for the Registry entry's bundle (`verificationMaterial.tlogEntries[0].logIndex`). A Conforming Client uses this field to resolve the entry against the Rekor log. |

**Cooperative-Publisher `distribution_uri` declaration (normative — MUST):** A cooperative Publisher distributing a Content Item via npm MUST declare `moat.distribution_uri` in the published `package.json` `moat` block. The field carries the canonical, dereferenceable URL of the published Distribution Tarball on the npm Registry.

**Registry `distribution_uri` backfill (normative — MUST):** A Registry MUST populate `moat.distribution_uri` on a backfilled Registry Manifest entry. The field is the channel-specific artifact URL for the backfilled item and lets a Conforming Client fetch the canonical Distribution Tarball without re-resolving the package against the npm Registry API.

**`distribution_uri` resolution to attested tarball (normative — MUST):** The `moat.distribution_uri` value MUST resolve to the exact Distribution Tarball whose unpacked Content Directory produced the canonical Content Hash this entry attests.

**`source_uri` and `distribution_uri` separation (normative — MUST NOT):** A Publisher or Registry MUST NOT conflate `moat.distribution_uri` with `source_uri`. The `source_uri` field of the Registry Manifest entry names the upstream Source Repository (a git URL — where the content was authored); `moat.distribution_uri` names where this version's bytes can be fetched on this channel. A Conforming Client MUST NOT substitute one for the other.

The schema-shape change — Publisher identity as a single `publisherSigning` object, Registry attestations as a list — replaces the Round 1 "duplicate role is malformed" rule with structural enforcement: a Conforming Client rejects malformed shapes via JSON schema validation rather than by counting role values at parse time.

**Canonical Attestation Payload:** Each Registry entry in `moat.attestations`, and the Publisher's Rekor entry referenced via `publisherSigning`, signs the canonical payload defined by [`moat-spec.md` §Per-Item Attestation Payload](../moat-spec.md#per-item-attestation-payload):

```json
{"_version":1,"content_hash":"sha256:<hex>"}
```

This sub-spec MUST NOT introduce a second canonical payload format. Both Publisher and Registry attestations sign byte-identical payloads for the same Content Hash; the operational difference between them lives in the signing identity recorded in the bundle, not in the payload.

**Worked example.** A Publisher who has both produced their own Sigstore signature (lodged in Rekor) and obtained a Registry counter-signature publishes the Publisher identity as `publisherSigning` and the Registry's bundle as a `moat.attestations[]` entry:

```json
{
  "name": "@example/skill-changelog",
  "version": "1.4.0",
  "moat": {
    "tarballContentRoot": "skill",
    "distribution_uri": "https://registry.npmjs.org/@example/skill-changelog/-/skill-changelog-1.4.0.tgz",
    "publisherSigning": {
      "issuer": "https://token.actions.githubusercontent.com",
      "subject": "https://github.com/example/skill-changelog/.github/workflows/publish.yml@refs/heads/main"
    },
    "attestations": [
      {
        "role": "registry",
        "bundle": "CnsKdGh...REGISTRY-BASE64-BUNDLE...",
        "rekor_log_index": 12345910
      }
    ]
  }
}
```

The four runtime states this shape represents — `publisherSigning` only, Registry attestation only, both, neither — are each legitimate and produce different Trust Tiers per [`moat-spec.md` §Trust Model](../moat-spec.md#trust-model).

**`Dual-Attested` requires verifying both attestations (normative — MUST):** When both `publisherSigning` and a Registry attestation are present, a Conforming Client MUST verify BOTH the Publisher's Rekor entry AND the Registry's attestation before treating the package as `Dual-Attested`.

**No preferring one attestation over the other (normative — MUST NOT):** A Conforming Client MUST NOT prefer one attestation over the other when both `publisherSigning` and a Registry attestation are present.

## Publisher Verification (normative)

The `publisherSigning` block discloses the Publisher's signing identity but does NOT embed the Publisher's Sigstore bundle in `package.json`. The Publisher's bundle lives in the Rekor transparency log; `publisherSigning` is the metadata a Conforming Client uses to locate and verify it.

The fields `publisherSigning.issuer` and `publisherSigning.subject` carry the same semantics as the `signing_profile` concept defined in [`moat-spec.md` §signing_profile](../moat-spec.md#signing_profile): `issuer` names the OIDC identity provider and `subject` names the workload identity (typically a GitHub Actions workflow path).

**Rekor query by `content_hash` + `{issuer, subject}` filter (normative — MUST):** A Conforming Client MUST query Rekor for entries whose payload's `content_hash` matches the canonical Content Hash for this package, then filter the result set by the `{issuer, subject}` pair from `publisherSigning`.

**Zero-match refusal (normative — MUST):** The Conforming Client MUST refuse to materialize the package if zero Rekor entries match `{content_hash, issuer, subject}`.

**Certificate-identity verification (normative — MUST):** The Conforming Client MUST verify that the selected entry's signing-certificate identity exactly matches `{issuer, subject}` from `publisherSigning` — payload match alone is insufficient because anyone can record any payload at any Rekor index, so the identity binding is what distinguishes the Publisher's attestation from an unrelated entry.

**Tiebreaker rule (normative — MUST):** When multiple Rekor entries match `{content_hash, issuer, subject}`, the Conforming Client MUST sort the matches by Rekor `logIndex` descending and select the entry with the largest `logIndex` — the most recent matching entry — as the Publisher's attestation. Rekor assigns `logIndex` monotonically, so the largest value is unambiguously the most recent insertion into the transparency log; this rule produces one and only one selected attestation per `{content_hash, issuer, subject}` triple.

**Anti-rollback — refuse smaller `logIndex` (normative — MUST):** Once a Conforming Client has recorded a Publisher attestation for a given Content Item — for example, in `.moat/npm-lockfile.json` — it MUST refuse to accept a later attestation whose Rekor `logIndex` is strictly smaller than the recorded value. Because `logIndex` is monotonic, a smaller value is never legitimate evidence of a newer signature; accepting one would let an attacker substitute a stale attestation for a current one. If a smaller `logIndex` is observed for an otherwise-matching `{content_hash, issuer, subject}` triple, the Client MUST refuse to materialize the package.

**Anti-rollback — surface anomaly to End User (normative — MUST):** When a Conforming Client refuses a Publisher attestation under the anti-rollback rule, the Client MUST surface the anomaly to the End User. The anomaly is what gives the End User a routable explanation for the refusal and a starting point for incident response (the recorded `logIndex` did not advance, so either the attestation chain is broken or the lockfile is wrong).

---

## Backfill Attestation by Registry (normative)

A Registry can attest a pre-existing npm package without the Publisher's cooperation — fetch the published Distribution Tarball, compute the MOAT Content Hash over the unpacked Content Directory, sign the resulting Canonical Attestation Payload, and publish a Registry Manifest entry pointing at it. This is "backfill": MOAT trust applied retroactively to a package whose Publisher has not (or not yet) added a `moat` block.

**Same signing profile (normative — MUST):** A backfilled Registry attestation MUST be produced under the Registry's existing `registry_signing_profile` as defined in [`moat-spec.md` §Registry Manifest](../moat-spec.md#registry-manifest). This sub-spec does not define a second registry-level signing profile for backfilled entries; the same single `registry_signing_profile` covers both Publisher-cooperative and backfilled attestations. The Registry's attestation is the Registry's attestation; whether it was triggered by a Publisher's published `moat` block or by the Registry's own backfill workflow makes no signing-identity difference.

**Trust Tier is the only encoded distinction (normative):** Backfill is observable to a Conforming Client only through the Trust Tier the resulting attestation produces. A backfilled package with no Publisher attestation present yields the `Signed` Trust Tier (registry-only attestation). The same package becomes `Dual-Attested` if and when the Publisher subsequently adds their own attestation entry to the `moat.attestations` array — at which point both entries verify under their respective signing identities and the package crosses into `Dual-Attested` per [`moat-spec.md` §Trust Model](../moat-spec.md#trust-model). The backfill-vs-counter-signed distinction is therefore encoded in the role-discriminated array, not in any second signing-profile field.

**`source_uri` omitted when no upstream Source Repository is known (normative — MUST):** Every Registry Manifest entry carries a REQUIRED `source_uri` field per [`moat-spec.md` §Registry Manifest](../moat-spec.md#registry-manifest) (closest single MUST anchor: `moat-spec.md:807`, the per-item compound-key uniqueness rule that also pins `source_uri` as REQUIRED on every manifest entry). For a backfilled npm-only Content Item, `source_uri` names the upstream Source Repository (a git URL) when one is known; when no upstream Source Repository is known, the Registry MUST omit `source_uri` rather than substitute the npm tarball URL. The npm tarball URL belongs in the channel-scoped `distribution_uri` field defined in §package.json moat Block, not in `source_uri`; the two fields have distinct semantics and MUST NOT be conflated.

**`distribution_uri` populated on every backfilled entry (normative — MUST):** A Registry MUST populate `distribution_uri` on every backfilled Registry Manifest entry. It is the only stable, dereferenceable identity npm offers for a published version, and a Conforming Client uses it to fetch the canonical Distribution Tarball without re-resolving the package against the npm Registry API.

**Uniqueness invariant preserved (normative — MUST):** A backfilled Registry Manifest entry MUST satisfy the `(name, type)` uniqueness constraint defined in [`moat-spec.md` §Registry Manifest](../moat-spec.md#registry-manifest).

**No duplicate backfill/Publisher entry for the same `(name, type)` (normative — MUST NOT):** A Registry MUST NOT publish two entries — one backfilled, one Publisher-cooperative — that share the same `(name, type)` pair. When a Publisher's attestation arrives for a previously-backfilled item, the Registry updates the existing entry in place (Trust Tier rises from `Signed` to `Dual-Attested`); it MUST NOT publish a duplicate entry.

---

## npm Provenance (informative)

The npm Registry supports its own publisher-attestation mechanism — npm provenance — that records build-environment metadata in a Sigstore bundle stored alongside the published package. npm provenance is established, useful, and produced today by a substantial fraction of popular packages.

**Observed-when-present, recommended-but-not-required:** A Conforming Client SHOULD record whether a fetched Distribution Tarball has an associated npm provenance attestation, but a missing npm provenance attestation MUST NOT cause materialization to fail. npm provenance is not a MOAT attestation: it does not sign the MOAT Canonical Attestation Payload, it does not bind to the MOAT Content Hash, and it does not appear in the Registry Manifest's `content[]` entries.

**Orthogonal to MOAT Trust Tier (normative — MUST):** A Conforming Client MUST NOT use the presence or absence of an npm provenance attestation to compute, raise, or lower the MOAT Trust Tier. Trust Tier is determined exclusively by the role-discriminated entries in `moat.attestations` per [`moat-spec.md` §Trust Model](../moat-spec.md#trust-model); npm provenance is a separate signal from a separate system. The two systems are orthogonal axes: each can be present or absent independently of the other.

**Four-state Trust Tier impact table (informative).** The two signals together produce four observable states. The table below names each state and its resulting MOAT Trust Tier impact; the normative display rules sit in prose under the table so they cannot be misread as table-cell footnotes.

| State | Trust Tier impact |
|---|---|
| Both present (npm provenance present, MOAT attestation present) | Determined exclusively by MOAT attestations per [`moat-spec.md` §Trust Model](../moat-spec.md#trust-model); npm provenance neither raises nor lowers the tier. |
| MOAT-only (npm provenance absent, MOAT attestation present) | Determined exclusively by MOAT attestations; absent npm provenance has no effect. |
| Provenance-only (npm provenance present, MOAT attestation absent) | `Unsigned` (no MOAT attestation present); npm provenance presence does not raise the tier. |
| Neither (both absent) | `Unsigned`. |

**Both-present display (normative — MUST NOT):** When both an npm provenance attestation and a MOAT attestation are present for a Content Item, a Conforming Client MUST NOT infer one signal from the other — npm provenance presence MUST NOT raise the MOAT Trust Tier, and MOAT attestation presence MUST NOT be used as evidence of npm provenance. The two signals are recorded by independent systems and a Conforming Client SHOULD display them on separate rows so an End User can read each on its own terms.

**Provenance-only display (normative — MUST):** When npm provenance is present but no MOAT attestation is present, a Conforming Client MUST display the package's MOAT Trust Tier as `Unsigned`. The presence of npm provenance MUST NOT be displayed in a way that allows an End User to infer the MOAT Trust Tier from the npm-provenance signal.

**Surfaced as a separate row (informative):** A Conforming Client MAY surface npm provenance presence to an End User as a separate row alongside the Trust Tier — for example, listing "Trust Tier: Signed" and "npm provenance: present" as two independent display fields. This avoids the failure mode where an End User sees "npm provenance present" and infers `Dual-Attested`, or sees "npm provenance missing" and infers `Unsigned`. The two systems answer different questions: npm provenance answers "where was this build produced?"; the MOAT Trust Tier answers "who has attested the bytes inside the Content Directory?".

---

## Reference Implementations (informative)

A canonical end-to-end Publisher workflow for npm Content Items is provided as a reusable GitHub Actions YAML at [`reference/moat-npm-publisher.yml`](../reference/moat-npm-publisher.yml). The workflow demonstrates the six-step canonical sequence in the order required by this sub-spec:

1. `npm pack` (v1) — produce the pre-sign tarball used to compute the canonical Content Directory hash.
2. Compute the canonical MOAT Content Directory hash by extracting the v1 tarball, removing the root `package.json` per the default Content Directory rule, and running [`reference/moat_hash.py`](../reference/moat_hash.py) over the remainder.
3. Sign the canonical attestation payload `{"_version":1,"content_hash":"sha256:..."}` with `cosign sign-blob --new-bundle-format` (Sigstore keyless OIDC).
4. Write `moat.publisherSigning.{issuer, subject}` back into `package.json` so a Conforming Client can locate the Publisher's Rekor entry by querying for `{content_hash, issuer, subject}` per §Publisher Verification.
5. `npm pack` (v2) — repack with the updated `package.json`. Because the default Content Directory rule excludes the root `package.json` from the canonical hash domain, the v2 tarball's canonical Content Hash is byte-identical to v1's.
6. `npm publish` the v2 tarball.

The two-pack pattern is what makes Publisher signing identity disclosable inside `package.json` without invalidating the signature: editing `package.json` between the two `npm pack` invocations does not alter the canonical hash that the Sigstore signature covers. Conformance for this property is exercised by [`specs/conformance/npm-distribution/slice-8.sh`](conformance/npm-distribution/slice-8.sh) (A8). Publishers MAY adapt this workflow but MUST preserve the Content Directory exclusion rule and the canonical attestation payload shape; both are normative.

---

## Conformance (normative)

This section enumerates the refusal modes a Conforming Client MAY emit when an npm-distributed Content Item fails to satisfy this sub-spec's normative MUSTs. Each row pairs a stable error code (`NPM-<SECTION>-<NN>`) with the precise spec citation that the code refers to. A Conforming Client SHOULD surface the code alongside the human-readable refusal message so an operator reading logs can route from the refusal back to the rule. This surface is normative for code values (the codes are stable identifiers a Conforming Client emits on the wire); the human-readable refusal text and the rendering rules are informative. Once shipped, a code's spelling and meaning MUST NOT change. Obsolete codes MUST be retained in the table marked `Reserved (was: <description>)` rather than reused for a different obligation. Conforming Clients SHOULD surface codes verbatim.

| Code | Refusal mode | Spec citation |
|---|---|---|
| `NPM-HASH-01` | Content Hash computed over wrong domain (not the Content Directory inside the unpacked tarball). | `specs/npm-distribution.md:15` |
| `NPM-HASH-02` | Hash algorithm re-implemented in Conforming Client (not delegated to `moat_hash.py`). | `specs/npm-distribution.md:17` |
| `NPM-HASH-03` | Byte-identical Content Directory not treated as the revoked Content Hash regardless of package name or version. | `specs/npm-distribution.md:19` |
| `NPM-HASH-04` | npm tarball SHA-512 (`dist.integrity`) substituted for the MOAT Content Hash in a normative check. | `specs/npm-distribution.md:21` |
| `NPM-CDIR-01` | Default-mode exclusion not path-anchored — nested `package.json` excluded from the hash domain. | `specs/npm-distribution.md:31` |
| `NPM-CDIR-02` | Cooperative Publisher omitted `moat.tarballContentRoot` (default rule unavailable to cooperative Publishers). | `specs/npm-distribution.md:33` |
| `NPM-CDIR-03` | Subdirectory-mode hashing applied an exclusion (subdirectory mode hashes every file under the named root). | `specs/npm-distribution.md:35` |
| `NPM-CDIR-04` | Publisher purported to extend the exclusion list via `package.json` metadata. | `specs/npm-distribution.md:39` |
| `NPM-CDIR-05` | Conforming Client honored a Publisher-declared exclusion extension. | `specs/npm-distribution.md:41` |
| `NPM-REV-01` | Conforming Client materialized a Content Item without consulting `.moat/npm-lockfile.json`'s `revoked_hashes`. | `specs/npm-distribution.md:53` |
| `NPM-REV-02` | Conforming Client proceeded to materialize a Content Hash present in `revoked_hashes`. | `specs/npm-distribution.md:55` |
| `NPM-REV-03` | Refusal output omitted the revocation reason code inherited from the core protocol enum. | `specs/npm-distribution.md:57` |
| `NPM-REV-04` | Conforming Client treated a remote source as authoritative over a locally-recorded revocation. | `specs/npm-distribution.md:59` |
| `NPM-REV-05` | Resolve-time refusal log omitted the structured `source` field (`lockfile` / `registry_manifest`). | `specs/npm-distribution.md:63` |
| `NPM-REV-06` | Conforming Client honored a per-hash operator escape hatch (env var, CLI flag, config entry). | `specs/npm-distribution.md:65` |
| `NPM-REV-07` | Operator-override env var, flag, or config entry not treated as if absent. | `specs/npm-distribution.md:67` |
| `NPM-SCHEMA-01` | `moat.tarballContentRoot` value did not resolve inside the unpacked tarball. | `specs/npm-distribution.md:81` |
| `NPM-SCHEMA-02` | Cooperative Publisher omitted `moat.distribution_uri`. | `specs/npm-distribution.md:91` |
| `NPM-SCHEMA-03` | Registry omitted `moat.distribution_uri` on a backfilled entry. | `specs/npm-distribution.md:93` |
| `NPM-SCHEMA-04` | `moat.distribution_uri` did not resolve to the exact tarball whose Content Directory produced the attested Content Hash. | `specs/npm-distribution.md:95` |
| `NPM-SCHEMA-05` | `source_uri` and `distribution_uri` conflated (npm tarball URL placed in `source_uri`, or git URL placed in `distribution_uri`). | `specs/npm-distribution.md:97` |
| `NPM-PAYLOAD-01` | Sub-spec attempted to introduce a second canonical attestation payload format. | `specs/npm-distribution.md:107` |
| `NPM-DUAL-01` | `Dual-Attested` tier assigned without verifying BOTH the Publisher's Rekor entry AND the Registry's attestation. | `specs/npm-distribution.md:135` |
| `NPM-DUAL-02` | Conforming Client preferred one attestation over the other when both were present. | `specs/npm-distribution.md:137` |
| `NPM-PUB-01` | Conforming Client queried Rekor by something other than the canonical `content_hash` + `{issuer, subject}` filter. | `specs/npm-distribution.md:145` |
| `NPM-PUB-02` | Zero Rekor entries matched `{content_hash, issuer, subject}` and Conforming Client did not refuse to materialize. | `specs/npm-distribution.md:147` |
| `NPM-PUB-03` | Selected Rekor entry's signing-certificate identity did not exactly match the `{issuer, subject}` from `publisherSigning`. | `specs/npm-distribution.md:149` |
| `NPM-PUB-04` | Tiebreaker rule violated — selected entry was not the largest-`logIndex` match. | `specs/npm-distribution.md:151` |
| `NPM-PUB-05` | Anti-rollback rule violated — accepted a strictly-smaller `logIndex` than the previously-recorded value. | `specs/npm-distribution.md:153` |
| `NPM-PUB-06` | Anti-rollback anomaly not surfaced to the End User. | `specs/npm-distribution.md:155` |
| `NPM-BACKFILL-01` | Backfilled Registry attestation not produced under the Registry's `registry_signing_profile`. | `specs/npm-distribution.md:163` |
| `NPM-BACKFILL-02` | Registry placed the npm tarball URL in `source_uri` of a Registry Manifest entry. | `specs/npm-distribution.md:167` |
| `NPM-BACKFILL-03` | Backfilled entry omitted `distribution_uri`. | `specs/npm-distribution.md:169` |
| `NPM-BACKFILL-04` | Backfilled Registry Manifest entry violated the `(name, type)` uniqueness constraint. | `specs/npm-distribution.md:171` |
| `NPM-BACKFILL-05` | Registry published a duplicate entry for an already-backfilled item. | `specs/npm-distribution.md:173` |
| `NPM-PROV-01` | Missing npm provenance caused materialization to fail (it MUST NOT). | `specs/npm-distribution.md:181` |
| `NPM-PROV-02` | npm provenance signal used to compute, raise, or lower the MOAT Trust Tier. | `specs/npm-distribution.md:183` |
| `NPM-PROV-03` | Both-present display inferred one signal from the other. | `specs/npm-distribution.md:194` |
| `NPM-PROV-04` | Provenance-only Content Item not displayed as `Unsigned`. | `specs/npm-distribution.md:196` |
| `NPM-SCOPE-01` | `distribution_uri` host is not `registry.npmjs.org` and the Content Item was attested or refused on the basis of this sub-spec rather than treated as outside its coverage. | `specs/npm-distribution.md:272` |

---

## Scope

**Current version:** This sub-spec covers Content Items distributed via the public npm Registry (`registry.npmjs.org`) and via npm-protocol-compatible registries that serve the same Distribution Tarball format and the same `package.json` metadata. The `moat` block schema, the materialization-boundary revocation MUSTs, and the backfill normative section apply uniformly across these.

**Planned future version:** Other registry transports — PyPI for Python content, Cargo for Rust, container registries for OCI-packaged content — will require their own sub-specs at this same boundary level. Those transports differ enough in tarball layout, manifest format, and registry-side attestation primitives that a single combined sub-spec would obscure rather than clarify. This sub-spec reserves no normative ground over those transports; future MOAT versions will add per-transport sub-specs as the transports themselves stabilize.

**Out-of-spec host coverage (`NPM-SCOPE-01`):** A Conforming Client encountering a `distribution_uri` whose host is not `registry.npmjs.org` MUST treat the item as outside this sub-spec's normative coverage — neither attested nor refused on the basis of this sub-spec alone. Private-registry hosts and other npm-protocol-compatible registries fall under this rule until their respective sub-specs are published; the rationale is described informatively under §Out of Scope below.

### Out of Scope

**Private-registry backfill:** This sub-spec does not cover Registry backfill against a *private* npm registry (an authenticated, access-controlled npm-protocol-compatible registry — for example, an enterprise-internal mirror at `npm.internal.example.com`). The public-`registry.npmjs.org`-only scope is deliberate: a private-registry backfill flow would need to resolve at least three additional questions that are out of scope here — (1) how a Registry authenticates to fetch a private tarball without the Publisher's credentials, (2) how the Registry expresses *which* private registry a `distribution_uri` points at when the URL alone is not globally unique, and (3) how a Conforming Client distinguishes "this hash is revoked on the public registry" from "this hash is revoked on a specific private registry". Each of those three has its own ADR-shaped design question and cannot be answered by extending this sub-spec piecewise. A future sub-spec at `specs/npm-distribution-private.md` (or equivalent) will cover the private-registry case. The normative obligation that a Conforming Client treat a non-`registry.npmjs.org` `distribution_uri` as outside this sub-spec's coverage is stated in §Scope above (`NPM-SCOPE-01`), so this paragraph carries only the informative rationale. The planned future direction is recorded in [`ROADMAP.md`](../ROADMAP.md).

**Runtime gating by AI agent runtimes:** Already covered by the §Revocation §Post-materialization revocation paragraph above; restated here for completeness. Runtime execution gating sits in the AI-agent-runtime layer, outside MOAT's protocol boundary as defined in [`moat-spec.md` §Conforming Client](../moat-spec.md#conforming-client).
