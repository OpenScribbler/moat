---
title: "npm Distribution"
description: "MOAT npm Distribution sub-specification — how MOAT attestations travel with content distributed through the npm Registry."
---

# npm Distribution Specification

**Version:** 0.1.0 (Draft)
**Requires:** moat-spec.md ≥ 0.7.1
**Part of:** [MOAT Specification](../moat-spec.md)

> The npm Distribution sub-spec defines how MOAT attestations travel with content distributed through the npm Registry: where the Content Hash is computed, what `package.json` metadata a Publisher embeds, when a Conforming Client refuses to materialize a Content Item, and how a Registry can attest a pre-existing npm package without Publisher cooperation.

---

## Content Hash Domain (normative)

A Content Item distributed via npm is published as an npm package. Each published version is delivered as a Distribution Tarball — a gzipped tar archive identified by an npm-assigned tarball URL.

**Hash input domain (normative — MUST):** The MOAT Content Hash for a Content Item distributed via npm is computed over the **Content Directory** inside the unpacked Distribution Tarball. The Content Directory is named by the `moat.contentDirectory` field in the published `package.json`; its path is interpreted relative to the tarball root after unpack. A Conforming Client MUST locate the Content Directory by reading `moat.contentDirectory`, MUST resolve it relative to the unpacked tarball, and MUST compute the Content Hash over its contents.

**Algorithm (normative — MUST):** The hash algorithm is unchanged from the core protocol; the Conforming Client computes the Content Hash using the algorithm specified in [`moat-spec.md` §Content Hash](../moat-spec.md#content-hash) and implemented by [`reference/moat_hash.py`](../reference/moat_hash.py). Only the input directory differs from the GitHub-Distribution Channel: where a GitHub-distributed Content Item hashes a directory in the source repository, an npm-distributed Content Item hashes the Content Directory inside the unpacked tarball. The algorithm itself — file ordering, normalization, exclusion list — is identical and MUST NOT be re-implemented in the Conforming Client.

**Copy-survival (normative):** Because the hash input is the bytes inside the tarball's Content Directory and the algorithm is canonical, two Distribution Tarballs that contain byte-identical Content Directory contents produce the same Content Hash. A Conforming Client that has revoked a Content Hash MUST treat any tarball whose Content Directory hashes to the revoked value as revoked, regardless of which package name, version, or Registry the tarball was retrieved from.

**Relationship to the npm tarball SHA-512:** npm's own integrity primitive — the `dist.integrity` SHA-512 recorded by the npm Registry for each published version — covers the entire Distribution Tarball, including `package.json`, `README`, license files, and any other ancillary content. The MOAT Content Hash covers only the Content Directory. The two values are computed over different inputs and serve different purposes: the npm tarball SHA-512 protects against tarball-level corruption or substitution at the Registry boundary; the MOAT Content Hash binds attestations to the bytes of the Content Item itself. A Conforming Client MUST NOT substitute one for the other and MUST NOT use the npm tarball SHA-512 in place of the MOAT Content Hash for any normative check defined by this sub-spec or by `moat-spec.md`.

**Relationship to npm provenance:** npm provenance, when present, is observed-when-present and orthogonal to the MOAT Content Hash; the [npm Provenance](#npm-provenance-informative) section below states the full normative position.

---

## Revocation at the Materialization Boundary (normative)

The materialization boundary is the point at which a Conforming Client resolves, fetches, or unpacks a Distribution Tarball into the install target. MOAT's revocation MUSTs apply at this boundary; runtime gating of already-materialized content is outside MOAT's protocol scope.

**Pre-materialization hard block (normative — MUST):** Before a Conforming Client fetches or unpacks a Distribution Tarball, it MUST consult the lockfile's `revoked_hashes` list as defined in [`moat-spec.md` §Lockfile](../moat-spec.md#lockfile). If the Content Hash for the requested package version appears in `revoked_hashes`, the Conforming Client MUST refuse to materialize the Content Item and MUST surface the revocation reason code (inherited unchanged from the core protocol enum) in its error output. The lockfile is authoritative; the Conforming Client MUST NOT proceed to fetch on the assumption that a remote source overrides a locally-recorded revocation.

**Persistence (normative):** Once a Content Hash is recorded in `revoked_hashes`, the persistence and lockfile-authoritative semantics from [`moat-spec.md` §Lockfile](../moat-spec.md#lockfile) apply unchanged. This sub-spec does not redefine the lockfile schema or the persistence rule.

**Resolve-time logging (normative — MUST):** A Conforming Client that refuses to materialize a Content Item due to revocation MUST emit a structured log entry at resolve time identifying the package name, version, Content Hash, revocation reason code, and the source of the revocation (lockfile vs Registry Manifest). The log entry is the audit anchor; without it, an operator cannot distinguish a genuine block from a silent skip.

**Operator-acknowledged proceed (normative — MAY / MUST):** A Conforming Client MAY honor a per-hash escape hatch via the `MOAT_ALLOW_REVOKED` environment variable. The variable's value is a comma-separated list of sha256 Content Hashes (lower-case hex, no `sha256:` prefix). When a Conforming Client is asked to materialize a Content Item whose Content Hash appears both in `revoked_hashes` and in `MOAT_ALLOW_REVOKED`, it MAY proceed with fetch and unpack, but MUST emit a structured log entry at resolve time stating that an operator-acknowledged proceed has been performed for the named hash and that the revoked entry was overridden. The override is per-hash, not global; a `MOAT_ALLOW_REVOKED` value of any token that does not exactly match a revoked hash MUST be ignored. A Conforming Client MUST NOT treat an empty `MOAT_ALLOW_REVOKED` as a wildcard.

**Post-materialization revocation (informative):** A revocation that arrives after a Distribution Tarball has been materialized has no normative effect at the materialization boundary; the Content Item is already on disk. Runtime gating of execution by an AI agent runtime is outside MOAT's protocol scope (see [`moat-spec.md` §Conforming Client](../moat-spec.md#conforming-client) for the protocol-boundary definition). A Conforming Client SHOULD surface a post-materialization revocation in its operational logs when the lockfile is updated, so that operators can audit which already-installed Content Items have been revoked, but this sub-spec defines no post-materialization MUST.

---

## package.json moat Block (normative)

A Publisher distributing a Content Item via npm declares MOAT attestation by adding a top-level `moat` block to the published `package.json`. This section fixes the schema of that block.

| Field | Required | Description |
|-------|----------|-------------|
| `moat.contentDirectory` | REQUIRED | String. Names the tarball-relative path of the Content Directory whose bytes are the input to the MOAT Content Hash (see [Content Hash Domain](#content-hash-domain-normative)). The path is interpreted relative to the unpacked tarball root and MUST resolve inside the tarball. |
| `moat.attestations` | REQUIRED | Array of attestation entries. The array MAY be empty; an empty array signals that the Publisher has reserved the `moat` block but no Publisher or Registry attestation is present yet. A Conforming Client treats an empty array as the `Unsigned` Trust Tier. |
| `moat.attestations[].role` | REQUIRED | String enum. One of `publisher` or `registry`. Identifies the actor whose signing identity backs the entry's `bundle`. A Conforming Client dispatches verification on this field. |
| `moat.attestations[].bundle` | REQUIRED | String. Base64-encoded Sigstore protobuf bundle v0.3 (Cosign Bundle, `--new-bundle-format`) covering the Canonical Attestation Payload. The bundle format and version are pinned by [`moat-spec.md` §Signature Envelope](../moat-spec.md#signature-envelope) and MUST NOT vary between roles. |
| `moat.attestations[].rekor_log_index` | REQUIRED | Integer. The Rekor transparency-log index recorded for the entry's bundle (`verificationMaterial.tlogEntries[0].logIndex`). A Conforming Client uses this field to resolve the entry against the Rekor log. |

**Role uniqueness (normative — MUST):** an attestations array MUST NOT contain two entries with the same `role` value. A Conforming Client that encounters a duplicate role MUST treat the package as having a malformed `moat` block and refuse to materialize it.

**Canonical Attestation Payload:** Each entry in `moat.attestations`, regardless of `role`, signs the canonical payload defined by [`moat-spec.md` §Per-Item Attestation Payload](../moat-spec.md#per-item-attestation-payload):

```json
{"_version":1,"content_hash":"sha256:<hex>"}
```

This sub-spec MUST NOT introduce a second canonical payload format. Both Publisher and Registry attestations sign byte-identical payloads for the same Content Hash; the operational difference between them lives in the signing identity recorded in the bundle, not in the payload.

**Worked example.** A Publisher who has both produced their own Sigstore signature and obtained a Registry counter-signature embeds both in the array:

```json
{
  "name": "@example/skill-changelog",
  "version": "1.4.0",
  "moat": {
    "contentDirectory": "skill",
    "attestations": [
      {
        "role": "publisher",
        "bundle": "CnsKdGh...PUBLISHER-BASE64-BUNDLE...",
        "rekor_log_index": 12345678
      },
      {
        "role": "registry",
        "bundle": "CnsKdGh...REGISTRY-BASE64-BUNDLE...",
        "rekor_log_index": 12345910
      }
    ]
  }
}
```

The four runtime states the role-discriminated array represents — publisher-only, registry-only, both, neither — are each legitimate and produce different Trust Tiers per [`moat-spec.md` §Trust Model](../moat-spec.md#trust-model). A Conforming Client MUST NOT prefer one role over the other when both are present; both attestations MUST verify for the package to qualify as `Dual-Attested`.

---

## Backfill Attestation by Registry (normative)

A Registry can attest a pre-existing npm package without the Publisher's cooperation — fetch the published Distribution Tarball, compute the MOAT Content Hash over the unpacked Content Directory, sign the resulting Canonical Attestation Payload, and publish a Registry Manifest entry pointing at it. This is "backfill": MOAT trust applied retroactively to a package whose Publisher has not (or not yet) added a `moat` block.

**Same signing profile (normative — MUST):** A backfilled Registry attestation MUST be produced under the Registry's existing `registry_signing_profile` as defined in [`moat-spec.md` §Registry Manifest](../moat-spec.md#registry-manifest). This sub-spec does not define a second registry-level signing profile for backfilled entries; the same single `registry_signing_profile` covers both Publisher-cooperative and backfilled attestations. The Registry's attestation is the Registry's attestation; whether it was triggered by a Publisher's published `moat` block or by the Registry's own backfill workflow makes no signing-identity difference.

**Trust Tier is the only encoded distinction (normative):** Backfill is observable to a Conforming Client only through the Trust Tier the resulting attestation produces. A backfilled package with no Publisher attestation present yields the `Signed` Trust Tier (registry-only attestation). The same package becomes `Dual-Attested` if and when the Publisher subsequently adds their own attestation entry to the `moat.attestations` array — at which point both entries verify under their respective signing identities and the package crosses into `Dual-Attested` per [`moat-spec.md` §Trust Model](../moat-spec.md#trust-model). The backfill-vs-counter-signed distinction is therefore encoded in the role-discriminated array, not in any second signing-profile field.

**source_uri for npm-only items (normative — MUST):** Every Registry Manifest entry carries a REQUIRED `source_uri` field per [`moat-spec.md` §Registry Manifest](../moat-spec.md#registry-manifest) (manifest content-entry schema, lines 766–807 of `moat-spec.md`). For a backfilled npm-only Content Item — one with no known upstream Source Repository — the Registry MUST set `source_uri` to the canonical npm tarball URL of the published version (e.g. `https://registry.npmjs.org/<package-name>/-/<package-name>-<version>.tgz`). The npm tarball URL is the only stable, dereferenceable identity npm offers for a published version; using it preserves the disambiguation semantics that `source_uri` serves at cross-registry name collisions.

**Uniqueness invariant preserved (normative):** A backfilled Registry Manifest entry MUST satisfy the `(name, type)` uniqueness constraint defined in [`moat-spec.md` §Registry Manifest](../moat-spec.md#registry-manifest). A Registry MUST NOT publish two entries — one backfilled, one Publisher-cooperative — that share the same `(name, type)` pair. When a Publisher's attestation arrives for a previously-backfilled item, the Registry updates the existing entry in place (Trust Tier rises from `Signed` to `Dual-Attested`); it MUST NOT publish a duplicate entry.

---

## npm Provenance (informative)

The npm Registry supports its own publisher-attestation mechanism — npm provenance — that records build-environment metadata in a Sigstore bundle stored alongside the published package. npm provenance is established, useful, and produced today by a substantial fraction of popular packages.

**Observed-when-present, recommended-but-not-required:** A Conforming Client SHOULD record whether a fetched Distribution Tarball has an associated npm provenance attestation, but a missing npm provenance attestation MUST NOT cause materialization to fail. npm provenance is not a MOAT attestation: it does not sign the MOAT Canonical Attestation Payload, it does not bind to the MOAT Content Hash, and it does not appear in the Registry Manifest's `content[]` entries.

**Orthogonal to MOAT Trust Tier (normative — MUST):** A Conforming Client MUST NOT use the presence or absence of an npm provenance attestation to compute, raise, or lower the MOAT Trust Tier. Trust Tier is determined exclusively by the role-discriminated entries in `moat.attestations` per [`moat-spec.md` §Trust Model](../moat-spec.md#trust-model); npm provenance is a separate signal from a separate system.

**Surfaced as a separate row (informative):** A Conforming Client MAY surface npm provenance presence to an End User as a separate row alongside the Trust Tier — for example, listing "Trust Tier: Signed" and "npm provenance: present" as two independent display fields. This avoids the failure mode where an End User sees "npm provenance present" and infers `Dual-Attested`, or sees "npm provenance missing" and infers `Unsigned`. The two systems answer different questions: npm provenance answers "where was this build produced?"; the MOAT Trust Tier answers "who has attested the bytes inside the Content Directory?".

---

## Scope

**Current version:** This sub-spec covers Content Items distributed via the public npm Registry (`registry.npmjs.org`) and via npm-protocol-compatible registries that serve the same Distribution Tarball format and the same `package.json` metadata. The `moat` block schema, the materialization-boundary revocation MUSTs, and the backfill normative section apply uniformly across these.

**Planned future version:** Other registry transports — PyPI for Python content, Cargo for Rust, container registries for OCI-packaged content — will require their own sub-specs at this same boundary level. Those transports differ enough in tarball layout, manifest format, and registry-side attestation primitives that a single combined sub-spec would obscure rather than clarify. This sub-spec reserves no normative ground over those transports; future MOAT versions will add per-transport sub-specs as the transports themselves stabilize.
