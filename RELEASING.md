# MOAT Release Process

This document defines the versioning scheme, spec maturity stages, changelog format, and release process for the MOAT specification.

---

## Pre-1.0 notice

Versions `0.x.y` carry no backwards-compatibility guarantees. Any minor version may introduce breaking changes to schema formats or normative requirements. Compatibility guarantees begin at `1.0.0`.

---

## Version numbering

MOAT uses [Semantic Versioning 2.0.0](https://semver.org/) (`MAJOR.MINOR.PATCH`).

Because MOAT is a specification, not a software library, SemVer levels apply to schema formats and normative requirements rather than API surfaces:

| Level | Triggers |
|---|---|
| **MAJOR** | Schema format breaks (new required fields, removed or renamed fields, changed field semantics in `meta.yaml`, manifest, or lockfile); normative inversions (MUST→SHOULD, SHOULD→MAY); removal of a content type or conformance class |
| **MINOR** | New optional fields; new normative sections; new SHOULD or RECOMMENDED requirements; new conformance class additions; new content types |
| **PATCH** | Typos, grammar, example corrections, clarifications that do not change the normative meaning of any requirement, test vector updates |

---

## Spec maturity stages

The spec header and CHANGELOG display a stage label alongside the version number (e.g., `0.4.0 (Draft)`).

| Stage | Label | Meaning |
|---|---|---|
| **Draft** | `(Draft)` | Incomplete or unvalidated. No compatibility guarantees. Subject to significant change. Current state. |
| **Release Candidate** | `(Release Candidate)` | Feature-complete and ready for final review. No new MUST requirements after RC. Semantic stability expected. |
| **Stable** | `(Stable)` | Production-ready. SemVer compatibility guarantees apply starting at this stage. Breaking changes require a MAJOR bump. |
| **Retired** | `(Retired)` | Superseded by a newer major version. The status section links to the successor. |

### Draft advancement criteria

The spec advances from Draft to Release Candidate when:

1. Two independent content hashing implementations in different languages pass all test vectors from `reference/generate_test_vectors.py`. The Python reference (`reference/moat_hash.py`) is one — a second in any other language is required.
2. The `moat-verify` reference implementation exists and validates the spec against real Rekor entries and real lockfiles.

See [ROADMAP.md](ROADMAP.md) for current implementation status.

### Release Candidate to Stable

After a Release Candidate is published:

- Announce to any known adopters and community channels.
- Hold a two-week comment window. Block only on new findings that reveal normative errors or security gaps.
- Once clean, merge RC → Stable and publish `1.0.0 (Stable)`.

---

## What triggers a version bump

**Cut a release** when a coherent unit of spec work is complete and stable enough that an implementer could base work on it.

**Do not cut a release** for work-in-progress or exploratory changes that may still reverse.

**Always cut a release** before publishing any external announcement or requesting external review.

At post-1.0:
- **PATCH**: Batch editorial fixes; release when there are more than a few or when an ambiguity is causing real confusion.
- **MINOR**: Release when a new feature is fully specified and review-complete.
- **MAJOR**: Only when breaking changes are unavoidable. Precede with a Deprecated notice in the previous minor release.

---

## Changelog format

MOAT uses [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format in [`CHANGELOG.md`](CHANGELOG.md).

### Conventions

- Use an `[Unreleased]` section at the top to track in-progress changes. On release, move its contents to a new versioned section.
- ISO 8601 dates (`YYYY-MM-DD`).
- Change sections: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- List the latest version first.
- Yanked releases: `## [x.y.z] — YYYY-MM-DD [YANKED]`

### Release header format

```md
## [0.5.0] — 2026-05-01 (Draft)

One-sentence summary of the release theme.

### Added
...
```

---

## Sub-specification versioning

`specs/moat-verify.md` and `specs/publisher-action.md` are versioned independently from the core specification using the same SemVer rules and stage labels.

Each sub-spec header carries:
- Its own version number
- A `Requires:` line indicating the minimum compatible core spec version

The same MAJOR/MINOR/PATCH semantics apply, scoped to each sub-spec's own interface:

| Level | Examples for moat-verify | Examples for Publisher Action |
|---|---|---|
| **MAJOR** | Changed exit codes, removed flags, changed output format | Changed attestation payload schema, removed inputs |
| **MINOR** | New optional flag, new output field | New optional input, new output file |
| **PATCH** | Clarification, typo fix | Clarification, typo fix |

Sub-spec changes are recorded in the main `CHANGELOG.md` under a sub-spec heading (e.g., `### moat-verify`). Sub-specs are released in the same commit as a core spec release when both changed, or independently when only the sub-spec changed.

---

## Release process

1. Move all `[Unreleased]` entries in `CHANGELOG.md` to a new versioned section. Add the release date and stage label.
2. Update `**Version:**` in the `moat-spec.md` header. Update sub-spec headers if their normative content changed — each gets its own version bump.
3. Commit: `spec: release v{VERSION}` — no other changes in this commit.
4. Tag: `git tag v{VERSION} && git push --tags`
5. Create a GitHub Release. Title: `v{VERSION}`. Body: paste the CHANGELOG entry for that version.
6. Mark the GitHub Release as **Pre-release** until `1.0.0 (Stable)`.

### Tag format

`v{MAJOR}.{MINOR}.{PATCH}` — for example, `v0.5.0`. Release candidates: `v1.0.0-rc.1`.

The stage label (`Draft`, `Release Candidate`, etc.) lives in the spec header and CHANGELOG, not in the version tag.
