# Version Semantics Research

**Date:** 2026-04-06
**Decision:** Option D — Content hash is identity, version is display metadata (OCI model)
**Status:** Resolved

## Research Question

Should MOAT define a normative version field, or leave versioning to registries? What format — SemVer, integer, opaque string, or none at all? Since `source_uri` can point to anything (not just git repos), we can't assume the source has a version scheme.

## Ecosystems Studied

### npm (Node.js)
- **Version is protocol-level.** Required in registry API URL paths.
- **Format:** SemVer 2.0.0, enforced at publish time.
- **Publisher controls versioning** via `package.json`.
- **Content identity:** SHA checksum of tarball (`shasum`/`integrity` in `dist` object). Version is human lookup key, hash is integrity check.

### Cargo / crates.io (Rust)
- **Version is protocol-level.** `vers` field required in every registry index entry.
- **Format:** SemVer 2.0.0, normatively enforced. Registry rejects non-conforming versions.
- **Publisher controls versioning** via `Cargo.toml`.
- **Content identity:** `cksum` field (SHA-256 of `.crate` file), computed by registry at publish time.

### Go Modules
- **Version is deeply structural.** Embedded in proxy protocol URL paths.
- **Format:** SemVer with mandatory `v` prefix. Auto-generates pseudo-versions (`v0.0.0-20191109021931-daa7c04131f5`) for untagged commits.
- **Publisher controls versioning** via Git tags; tooling synthesizes for untagged content.
- **Content identity:** `go.sum` hashes verified against transparency log (sum.golang.org). Hybrid: versions for addressing, hashes for verification.

### OCI / Container Registries
- **Tags are protocol-level but versioning is not.** Tags are mutable pointers to manifests. Format: `[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}`. No semantic structure imposed.
- **Digests are the real content identity.** Content-addressed `sha256:...` digests. Immutable. Can pull by digest or by tag.
- **Publisher controls tags.** Tags can be reassigned at any time. Registry enforces no versioning policy.
- **Key insight:** OCI cleanly separates naming (tags, opaque) from identity (digests, content-addressed). Most explicit two-layer system studied.

### Homebrew
- **Version is formula-level, not protocol-level.** Git-based formula repository, no registry protocol.
- **Format:** Freeform string, often inferred from download URL. No SemVer requirement.
- **Formula author controls versioning.** `revision` field for rebuilds; `version_scheme` integer for upstream scheme changes.
- **Content identity:** SHA-256 checksum of source tarball.

### TUF (The Update Framework)
- **Version is protocol-level for metadata, not for targets.** Monotonically increasing integer versions on metadata files (root, targets, snapshot, timestamp).
- **Format:** Positive integer. Prevents rollback and mix-and-match attacks.
- **Version serves security, not naming.** Target files have no TUF-defined version format.
- **Content identity:** Hashes on target files. Version-only identification acceptable when repository is trusted.

### Nix
- **Version is NOT a first-class concept.** Store paths: `/nix/store/<hash>-<name>`. The "name" is human-readable with no enforced structure.
- **Content is the identity.** Hash derived from build inputs (input-addressed) or output bytes (content-addressed). Different inputs = different store path, even for "same version."
- **Key insight:** Proves a fully content-addressed system can dispense with versions entirely at infrastructure level.

## Cross-Cutting Patterns

### The Version-Hash Duality

| System | Primary lookup key | Content hash role |
|--------|-------------------|-------------------|
| npm | Version | Integrity verification |
| Cargo | Version | Integrity verification |
| Go | Version | Integrity + transparency log |
| OCI | Tag OR Digest | Digest is the true identity |
| Homebrew | Version | Integrity verification |
| TUF | Version (integer) | Optional integrity check |
| Nix | Hash (store path) | Identity itself |

Spectrum: version-primary (npm, Cargo) → dual addressing (OCI, Go) → hash-primary (Nix).

### SemVer Enforcement
- **Normatively required:** Cargo, Go, npm
- **Supported but not required:** Homebrew
- **Not applicable:** OCI (opaque tags), TUF (integers), Nix (no version concept)

No ecosystem invented its own version format. They either adopt SemVer or stay out of version semantics.

### Publisher Always Controls Versioning
No registry auto-assigns versions. Exceptions: Go pseudo-versions (tooling), Homebrew `revision` (registry-side bump), TUF integers (repository operator).

### Handling Unversioned Content
| Approach | Examples |
|----------|----------|
| Reject it | Homebrew core |
| Synthesize a version | Go pseudo-versions |
| Use content hash as identity | Nix, OCI |
| Don't address it | npm, Cargo (version mandatory) |

### Mutability
- **Immutable versions:** npm, Cargo, Go (once published, version cannot be reused)
- **Mutable tags:** OCI (tags reassignable to different digests)
- **Immutable by construction:** Nix (different content = different hash)

## Decision Rationale

**Option D (OCI model)** chosen because:

1. **Matches MOAT's architecture.** Content hash is already the trust anchor. Making it the identity anchor is internally consistent.
2. **Handles diverse sources.** `source_uri` can point to anything — git repos, npm packages, tarballs. Can't assume the source has a version scheme.
3. **Proven at scale.** OCI's tag/digest separation works for millions of container images.
4. **Stronger than version pinning.** Lockfiles pin content hashes — you can't get different content even if a version label is reused.
5. **MOAT isn't a package manager.** No dependency resolution, no compatibility constraints. SemVer's value is expressing dependency compatibility, which MOAT doesn't need.

**Edge cases examined:**
- Same content, different labels across registries → hash proves identity regardless of labels
- Content changes without label update → hash catches the difference
- "Update available" logic → must be hash-first, timestamp-second (spec must spell this out)
- Cross-registry freshness → inherently ambiguous, but hash comparison makes it less so
- Rollback detection → `attested_at` comparison sufficient for trust model; ordering isn't MOAT's job

**Spec implications:**
- `version` is an optional, non-normative display label in manifest entries
- `content_hash` is the normative identifier
- Client verification: different hash + later `attested_at` = update; same hash + later `attested_at` = re-attestation (not an update)

## Sources
- [npm Registry API](https://github.com/npm/registry/blob/main/docs/REGISTRY-API.md)
- [Cargo Registry Index](https://doc.rust-lang.org/cargo/reference/registry-index.html)
- [Go Module Proxy Protocol](https://go.dev/ref/mod#module-proxy-protocol)
- [OCI Distribution Spec](https://github.com/opencontainers/distribution-spec/blob/main/spec.md)
- [OCI Image Spec: Descriptors](https://github.com/opencontainers/image-spec/blob/main/descriptor.md)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [TUF Specification](https://theupdateframework.github.io/specification/latest/)
- [Nix Content-Addressing Store Objects](https://nix.dev/manual/nix/2.26/store/store-object/content-address)
- [Semantic Versioning 2.0.0](https://semver.org/)
