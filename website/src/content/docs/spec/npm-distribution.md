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

**Default (normative — MUST):** When `moat.tarballContentRoot` is absent from the published `package.json`, the canonical Content Directory is the unpacked tarball root with `package.json` excluded from the hash domain. The exclusion is path-anchored to the tarball root: only the `package.json` at the root of the unpacked tarball is excluded; nested `package.json` files at deeper paths (for example, `pkg/package.json`) MUST NOT be excluded and MUST be included in the hash domain. The default rule lets a Registry compute the canonical Content Hash for any published version by fetching the Distribution Tarball and applying this rule, with no Publisher cooperation required (see [Backfill Attestation by Registry](#backfill-attestation-by-registry-normative)).

**Subdirectory mode (normative — MUST):** When `moat.tarballContentRoot` is set to a subdirectory path, the canonical Content Directory is that subdirectory's contents inside the unpacked tarball. Subdirectory mode applies no exclusions: every file under the named subdirectory — including any `package.json` at any depth under it — MUST be included in the hash domain. The default-mode `package.json` exclusion does not transfer into subdirectory mode.

**Fixed exclusion list (normative — MUST):** The default-mode exclusion list is fixed at exactly one file: `package.json` at the tarball root. A Publisher MUST NOT extend, widen, or add to the exclusion list via `package.json` metadata or any other mechanism, and a Conforming Client MUST NOT honor any field that purports to do so. Future amendments to this list (for example, additional npm-injected metadata files) require a sub-spec amendment, not Publisher-side configuration.

**Rationale (informative):** The default lets backfill work — a Registry can produce the canonical Content Hash for any published tarball without the Publisher having added a `moat` block. The `package.json` exclusion lets a Publisher write the Rekor log index back into `package.json` after signing without disturbing the canonical hash, breaking the chicken-and-egg between log-index population and signature stability. The path-anchored rule mirrors the root-only exclusion discipline used by [`reference/moat_hash.py`](../reference/moat_hash.py)'s `EXCLUDED_FILES` set: nested files of the same name have no protocol meaning at depth and MUST stay inside the hash domain so malicious content cannot hide there.

---

## Revocation at the Materialization Boundary (normative)

The materialization boundary is anchored at a single, precise point: **before any byte of the tarball is written outside the package manager's content cache**. This sub-spec names three operations that a Conforming Client MAY refuse at — `resolve`, `fetch`, and `unpack` — and the choice of which sub-operation to refuse at is a Conforming Client implementation matter. Whichever sub-operation the Client refuses at, no extracted bytes may land outside the package manager's content cache. MOAT's revocation MUSTs apply at this boundary; runtime gating of already-materialized content is outside MOAT's protocol scope.

**Mapping to common npm-client architectures (informative):** The cache-boundary anchor maps cleanly onto the architectures of widely-deployed npm clients without requiring any of them to change shape. `pacote` (npm's tarball-fetch and extract library) refuses at `fetch` or `unpack` and discards the partial cache entry on refusal — the streaming-extract path complies because the cache is the staging area, not the install target. Yarn Plug'n'Play stores fetched tarballs in its content-addressable `.yarn/cache` and only resolves modules from the cache at runtime; refusing before any byte enters that cache satisfies the anchor. The pnpm content-addressable store hard-links from `node_modules` into a global content-addressed cache; refusing before the global-store write satisfies the anchor by the same reasoning. The anchor exists to align the rule with these architectures, not to constrain them.

**Pre-materialization hard block (normative — MUST):** Before a Conforming Client fetches or unpacks a Distribution Tarball, it MUST consult the lockfile's `revoked_hashes` list as defined in [`moat-spec.md` §Lockfile](../moat-spec.md#lockfile). If the Content Hash for the requested package version appears in `revoked_hashes`, the Conforming Client MUST refuse to materialize the Content Item and MUST surface the revocation reason code (inherited unchanged from the core protocol enum) in its error output. The lockfile is authoritative; the Conforming Client MUST NOT proceed to fetch on the assumption that a remote source overrides a locally-recorded revocation.

**Persistence (normative):** Once a Content Hash is recorded in `revoked_hashes`, the persistence and lockfile-authoritative semantics from [`moat-spec.md` §Lockfile](../moat-spec.md#lockfile) apply unchanged. This sub-spec does not redefine the lockfile schema or the persistence rule.

**Resolve-time logging (normative — MUST):** A Conforming Client that refuses to materialize a Content Item due to revocation MUST emit a structured log entry at resolve time identifying the package name, version, Content Hash, revocation reason code, and the source of the revocation (lockfile vs Registry Manifest). The log entry is the audit anchor; without it, an operator cannot distinguish a genuine block from a silent skip.

**Operator-acknowledged proceed (normative — MAY):** A Conforming Client MAY honor a per-hash, per-entry escape hatch via the `MOAT_ALLOW_REVOKED` environment variable. The full normative surface — process scope, REQUIRED reason co-variable, per-entry expiry encoding, structured override-applied event — lives in the [MOAT_ALLOW_REVOKED Operator Override](#moat_allow_revoked-operator-override-normative) section below. A Conforming Client that elects not to implement the override MUST treat `MOAT_ALLOW_REVOKED` as if absent.

**Post-materialization revocation (informative):** A revocation that arrives after a Distribution Tarball has been materialized has no normative effect at the materialization boundary; the Content Item is already on disk. Runtime gating of execution by an AI agent runtime is outside MOAT's protocol scope (see [`moat-spec.md` §Conforming Client](../moat-spec.md#conforming-client) for the protocol-boundary definition). A Conforming Client SHOULD surface a post-materialization revocation in its operational logs when the lockfile is updated, so that operators can audit which already-installed Content Items have been revoked, but this sub-spec defines no post-materialization MUST.

---

## MOAT_ALLOW_REVOKED Operator Override (normative)

The `MOAT_ALLOW_REVOKED` environment variable is the operator-acknowledged escape hatch for the pre-materialization hard block defined in [Revocation at the Materialization Boundary](#revocation-at-the-materialization-boundary-normative). Its purpose is to let an operator who has done out-of-band investigation re-enable a single, expiring, named exception without disabling the revocation machinery wholesale. This section fixes the normative surface a Conforming Client MUST implement when it elects to honor `MOAT_ALLOW_REVOKED`.

**Process-scope, read-once (normative — MUST):** A Conforming Client MUST read `MOAT_ALLOW_REVOKED` (and its co-variable `MOAT_ALLOW_REVOKED_REASON`) exactly once at process start. The Conforming Client MUST NOT re-read either variable mid-process; mid-process re-reads, hot-reloads, or re-evaluations are non-conformant. The override is process-scope only: a value visible to one Conforming Client process MUST NOT influence any other process. This rule prevents a long-running daemon from picking up an environment change made for an unrelated invocation.

**REQUIRED `MOAT_ALLOW_REVOKED_REASON` co-variable (normative — MUST):** Whenever `MOAT_ALLOW_REVOKED` is non-empty, the operator MUST also set the co-variable `MOAT_ALLOW_REVOKED_REASON` to a non-empty reason string. A Conforming Client MUST refuse to honor any `MOAT_ALLOW_REVOKED` entry and MUST fail with a structured error if `MOAT_ALLOW_REVOKED` is set without a non-empty `MOAT_ALLOW_REVOKED_REASON` — the override is hard-failed, not silently dropped, so the missing-reason condition is itself an audit signal. A Conforming Client MUST NOT treat the absence of `MOAT_ALLOW_REVOKED_REASON` as permission to proceed; the REASON co-variable is a precondition for the override mechanism, not metadata.

**Per-entry encoding `<sha256-hex>:<RFC3339-timestamp>` (normative — MUST):** The value of `MOAT_ALLOW_REVOKED` is a comma-separated list of entries. Each entry MUST be encoded as `<sha256-hex>:<RFC3339-timestamp>` where `<sha256-hex>` is the lower-case hex Content Hash (no `sha256:` prefix) and `<RFC3339-timestamp>` is an RFC 3339 timestamp naming the entry's expiry. The colon delimiter is mandatory: an entry that omits the colon delimiter, or that carries no timestamp after the delimiter, is malformed and MUST be ignored as malformed (a Conforming Client MUST NOT treat such an entry as permanent and MUST NOT honor it for any package). This rule eliminates permanent overrides — every entry carries its own expiry.

**Expired entries treated as if absent (normative — MUST):** A Conforming Client MUST compare each well-formed entry's RFC 3339 timestamp against the current wall-clock time at resolve time. Entries whose timestamps are past the current time MUST be treated as if absent: no override is applied, no warning is emitted, no log entry is written for the expired entry itself. The expired-entry rule is silently ignored — the spec does not require a warning or log because operators are expected to rotate entries proactively, and a noisy expiry log would obscure the structured override-applied events that matter for audit.

**Structured override-applied event (normative — MUST):** When a Conforming Client honors a well-formed, unexpired `MOAT_ALLOW_REVOKED` entry whose `<sha256-hex>` matches a Content Hash listed in `revoked_hashes`, the Conforming Client MUST emit exactly one structured log event recording the override. The event MUST include the following fields with these names verbatim:

- `package` — the npm package coordinate being materialized (`<name>@<version>`).
- `content_hash` — the canonical MOAT Content Hash matched by the override entry, in `sha256:<hex>` form.
- `reason` — the operator-supplied reason string read from `MOAT_ALLOW_REVOKED_REASON`.
- `expires_at` — the RFC 3339 timestamp from the matched override entry.

The structured event is the audit anchor for the override: it pins which package was allowed, under whose stated reason, and until when. A Conforming Client MUST NOT suppress, redact, or coalesce these events; one applied override produces exactly one event so an external log-aggregation system can count override applications.

**Per-hash, never global (normative — MUST):** A Conforming Client MUST NOT treat any `MOAT_ALLOW_REVOKED` value as a global wildcard. The empty string and tokens such as `*`, `all`, or `true` MUST NOT be interpreted as "allow all revoked hashes"; they MUST be ignored as malformed under the per-entry encoding rule above. The override is exclusively per-`<sha256-hex>` and per-entry-expiry.

---

## package.json moat Block (normative)

A Publisher distributing a Content Item via npm declares MOAT attestation by adding a top-level `moat` block to the published `package.json`. This section fixes the schema of that block.

| Field | Required | Description |
|-------|----------|-------------|
| `moat.tarballContentRoot` | OPTIONAL | String. Names the tarball-relative subdirectory whose contents are the **Content Directory** for this Content Item — the canonical concept defined in [`lexicon.md` §Content Directory](../lexicon.md) and resolved by the [Content Directory](#content-directory-normative--must) section's default and subdirectory-mode rules. When omitted, the default rule applies (unpacked tarball root with the root `package.json` excluded). When present, the value MUST resolve inside the unpacked tarball. |
| `publisherSigning` | OPTIONAL | Object (under the top-level `moat` block). Discloses the Publisher's signing identity so a Conforming Client can locate and verify the Publisher's Sigstore signature in the Rekor transparency log. The Publisher's bundle itself is NOT embedded in `package.json`; it lives in Rekor. When `publisherSigning` is absent, the package has no Publisher-attested signing identity (a Registry attestation in `moat.attestations[]` MAY still be present). |
| `publisherSigning.issuer` | REQUIRED | String. The OIDC issuer URL of the Publisher's signing identity (typically `https://token.actions.githubusercontent.com` for GitHub Actions). REQUIRED when the `publisherSigning` block is present. Carries the same semantics as the `issuer` field of the [`signing_profile`](../moat-spec.md#signing_profile) defined in [`moat-spec.md` §signing_profile](../moat-spec.md#signing_profile). |
| `publisherSigning.subject` | REQUIRED | String. The OIDC subject (workload identity) of the Publisher's signing identity (typically the GitHub Actions workflow path, e.g. `https://github.com/<owner>/<repo>/.github/workflows/<file>@refs/heads/<branch>`). REQUIRED when the `publisherSigning` block is present. Carries the same semantics as the `subject` field of the [`signing_profile`](../moat-spec.md#signing_profile) defined in [`moat-spec.md` §signing_profile](../moat-spec.md#signing_profile). |
| `publisherSigning.rekorLogIndex` | OPTIONAL | Integer. The Rekor transparency-log index of the Publisher's bundle, when known at publish time. A hint that lets a Conforming Client fetch the entry directly by index instead of querying Rekor by Content Hash. See [Publisher Verification](#publisher-verification-normative). |
| `moat.attestations` | REQUIRED | Array of Registry attestation entries. The array MAY be empty; an empty array signals that no Registry has counter-signed this Content Item. A Conforming Client treats an empty array — together with an absent `publisherSigning` block — as the `Unsigned` Trust Tier. |
| `moat.attestations[].role` | REQUIRED | String enum. The only currently defined value is `"registry"`. The field is preserved for forward compatibility with future role types. |
| `moat.attestations[].bundle` | REQUIRED | String. Base64-encoded Sigstore protobuf bundle v0.3 (Cosign Bundle, `--new-bundle-format`) covering the Registry's Canonical Attestation Payload, pinned by [`moat-spec.md` §Signature Envelope](../moat-spec.md#signature-envelope). |
| `moat.attestations[].rekor_log_index` | REQUIRED | Integer. The Rekor transparency-log index recorded for the Registry entry's bundle (`verificationMaterial.tlogEntries[0].logIndex`). A Conforming Client uses this field to resolve the entry against the Rekor log. |

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
    "publisherSigning": {
      "issuer": "https://token.actions.githubusercontent.com",
      "subject": "https://github.com/example/skill-changelog/.github/workflows/publish.yml@refs/heads/main",
      "rekorLogIndex": 12345678
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

The four runtime states this shape represents — `publisherSigning` only, Registry attestation only, both, neither — are each legitimate and produce different Trust Tiers per [`moat-spec.md` §Trust Model](../moat-spec.md#trust-model). When both are present, a Conforming Client MUST verify both before treating the package as `Dual-Attested`; the Client MUST NOT prefer one over the other.

## Publisher Verification (normative)

The `publisherSigning` block discloses the Publisher's signing identity but does NOT embed the Publisher's Sigstore bundle in `package.json`. The Publisher's bundle lives in the Rekor transparency log; `publisherSigning` is the metadata a Conforming Client uses to locate and verify it. The verification path depends on whether `publisherSigning.rekorLogIndex` is present.

The fields `publisherSigning.issuer` and `publisherSigning.subject` carry the same semantics as the `signing_profile` concept defined in [`moat-spec.md` §signing_profile](../moat-spec.md#signing_profile): `issuer` names the OIDC identity provider and `subject` names the workload identity (typically a GitHub Actions workflow path).

**Path 1 — `rekorLogIndex` present (normative — MUST):** A Conforming Client MUST fetch the Rekor entry at the indicated log index, retrieve the embedded Sigstore bundle, and verify (a) the bundle's payload matches the Canonical Attestation Payload for this package's Content Hash, and (b) the bundle's signing-certificate identity exactly matches `{issuer, subject}` from `publisherSigning`. If either check fails, the Client MUST refuse to materialize the package.

**Path 2 — `rekorLogIndex` absent (normative — MUST):** A Conforming Client MUST query Rekor for entries whose payload's `content_hash` matches the canonical Content Hash for this package, then filter the result set by the `{issuer, subject}` pair from `publisherSigning`. The Client MUST find at least one matching entry; if zero entries match, the Client MUST refuse to materialize the package. When multiple entries match, the Client MUST treat the most recent matching entry as the Publisher's attestation.

`rekorLogIndex` is a hint, not a trust anchor. A Conforming Client MUST verify the `{issuer, subject}` identity match in both paths; the index alone is insufficient because anyone can record any payload at any Rekor index. The identity binding is what distinguishes the Publisher's attestation from an unrelated Rekor entry.

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

**Orthogonal to MOAT Trust Tier (normative — MUST):** A Conforming Client MUST NOT use the presence or absence of an npm provenance attestation to compute, raise, or lower the MOAT Trust Tier. Trust Tier is determined exclusively by the role-discriminated entries in `moat.attestations` per [`moat-spec.md` §Trust Model](../moat-spec.md#trust-model); npm provenance is a separate signal from a separate system. The two systems are orthogonal axes: each can be present or absent independently of the other.

**Four-state disagreement table (informative).** The two signals together produce four observable states. The table below names each state, the Conforming Client's recommended display rule, and the resulting Trust Tier impact.

| npm provenance | MOAT attestation | Conforming Client display | Trust Tier impact |
|---|---|---|---|
| Present | Present (both present) | Display both — surface the npm provenance row alongside the MOAT Trust Tier row. The Client MUST NOT infer one signal from the other. | Determined exclusively by MOAT attestations per [`moat-spec.md` §Trust Model](../moat-spec.md#trust-model); npm provenance neither raises nor lowers the tier. |
| Absent | Present (MOAT-only) | Display the MOAT Trust Tier; surface absent npm provenance as a distinct observation (`npm provenance: absent`), not as a Trust-Tier downgrade. | Determined exclusively by MOAT attestations; absent npm provenance has no effect. |
| Present | Absent (provenance-only) | Display npm provenance presence as a distinct observation; the package's MOAT Trust Tier is `Unsigned` and the Client MUST display it as such. | `Unsigned` (no MOAT attestation present); npm provenance presence does not raise the tier. |
| Absent | Absent (neither) | Display the standard `Unsigned` Trust Tier; no npm provenance signal to surface. | `Unsigned`. |

**Surfaced as a separate row (informative):** A Conforming Client MAY surface npm provenance presence to an End User as a separate row alongside the Trust Tier — for example, listing "Trust Tier: Signed" and "npm provenance: present" as two independent display fields. This avoids the failure mode where an End User sees "npm provenance present" and infers `Dual-Attested`, or sees "npm provenance missing" and infers `Unsigned`. The two systems answer different questions: npm provenance answers "where was this build produced?"; the MOAT Trust Tier answers "who has attested the bytes inside the Content Directory?".

---

## Reference Implementations (informative)

A canonical end-to-end Publisher workflow for npm Content Items is provided as a reusable GitHub Actions YAML at [`reference/moat-npm-publisher.yml`](../reference/moat-npm-publisher.yml). The workflow demonstrates the seven-step canonical sequence in the order required by this sub-spec:

1. `npm pack` (v1) — produce the pre-sign tarball used to compute the canonical Content Directory hash.
2. Compute the canonical MOAT Content Directory hash by extracting the v1 tarball, removing the root `package.json` per the default Content Directory rule, and running [`reference/moat_hash.py`](../reference/moat_hash.py) over the remainder.
3. Sign the canonical attestation payload `{"_version":1,"content_hash":"sha256:..."}` with `cosign sign-blob --new-bundle-format` (Sigstore keyless OIDC).
4. Capture the Rekor log index from the signed bundle (`verificationMaterial.tlogEntries[0].logIndex`).
5. Write `moat.publisherSigning.{issuer, subject, rekorLogIndex}` back into `package.json`.
6. `npm pack` (v2) — repack with the updated `package.json`. Because the default Content Directory rule excludes the root `package.json` from the canonical hash domain, the v2 tarball's canonical Content Hash is byte-identical to v1's.
7. `npm publish` the v2 tarball.

The two-pack pattern is what makes Publisher signing identity disclosable inside `package.json` without invalidating the signature: editing `package.json` between the two `npm pack` invocations does not alter the canonical hash that the Sigstore signature covers. Conformance for this property is exercised by [`.ship/npm-distribution-spec/conformance/slice-8.sh`](../.ship/npm-distribution-spec/conformance/slice-8.sh) (A8). Publishers MAY adapt this workflow but MUST preserve the Content Directory exclusion rule and the canonical attestation payload shape; both are normative.

---

## Scope

**Current version:** This sub-spec covers Content Items distributed via the public npm Registry (`registry.npmjs.org`) and via npm-protocol-compatible registries that serve the same Distribution Tarball format and the same `package.json` metadata. The `moat` block schema, the materialization-boundary revocation MUSTs, and the backfill normative section apply uniformly across these.

**Planned future version:** Other registry transports — PyPI for Python content, Cargo for Rust, container registries for OCI-packaged content — will require their own sub-specs at this same boundary level. Those transports differ enough in tarball layout, manifest format, and registry-side attestation primitives that a single combined sub-spec would obscure rather than clarify. This sub-spec reserves no normative ground over those transports; future MOAT versions will add per-transport sub-specs as the transports themselves stabilize.
