# CRLF Normalization Research

**Date:** 2026-04-06
**Decision:** Proposed — hash raw bytes, normalize at registry ingestion (Go model). Pending panel review.
**Status:** Under review

## Research Question

How should MOAT handle line ending normalization in its content hashing algorithm? Three sub-questions:
1. Should normalization happen inside the hash algorithm or at the publish boundary?
2. How should text vs binary files be distinguished?
3. What are the adoption implications of each approach?

## Ecosystems Studied

### Git
- `.gitattributes` with `text=auto` triggers content-based auto-detection (NUL byte scan, lone CR check, printable ratio)
- Normalizes to LF in the index on checkin; converts to CRLF on checkout if configured
- Known problems: UTF-16 misclassified as binary (contains NUL bytes), per-user `core.autocrlf` settings cause inconsistencies, retroactive normalization requires `git add --renormalize`

### Go Module Checksums
- `dirhash` hashes raw bytes with zero normalization at the hash layer
- Normalization happens upstream: `git -c core.autocrlf=input -c core.eol=lf archive` forces LF at VCS extraction time
- Key design: normalization pushed to the boundary where content enters the system, not applied at hash time
- Real-world bug reports of checksum mismatches from line ending differences (golang/go#29281)

### Cargo (.crate archives)
- No line ending normalization in packaging pipeline
- Reproducibility efforts focused on tar metadata (timestamps, user/group), not file content
- Only normalizes `Cargo.lock` to LF; all other files left as-is

### npm (tarballs)
- No normalization. Known breakage: Windows CRLF in shebang lines breaks Unix execution
- npm team acknowledged the problem (npm/npm#13203), closed without resolution
- Integrity hashes computed over raw bytes

### OCI/Docker
- Pure content-addressable storage. Digests are SHA-256 of raw bytes
- Spec says implementations MAY canonicalize but are not required to
- Guidance: "avoid heavy processing before calculating a hash"

### Summary
No major package registry normalizes at hash time. All hash raw bytes. Go normalizes at the publish boundary. Others don't normalize at all.

## Text/Binary Detection Approaches

### Extension-based allowlist
- Maintain a list of known text extensions (.md, .yaml, .json, .txt, etc.)
- Everything not on the list treated as binary
- **Deterministic**: same file always gets same classification regardless of content
- **Safe failure mode**: unrecognized text extension treated as binary (hash mismatch, not corruption)
- Downside: list is never complete, new extensions require spec updates

### Content-based (NUL byte scanning)
- Used by git, WHATWG MIME sniffing
- Scan first N bytes for NUL/binary data bytes
- **Dangerous failure mode**: UTF-16 text contains NUL bytes, misclassified as binary
- Result can change if file content changes (non-deterministic)

### Hybrid (extension + content fallback)
- Check extension first, fall back to content scanning for unknowns
- Best of both but more complex to spec

### Recommendation
Extension-based for the spec. Safe failure mode (unrecognized text → binary) is detectable and fixable. Content-based has dangerous failure mode (UTF-16 misclassification) and is non-deterministic.

## The Three Design Options

### Option 1: Hash raw bytes, normalize at publish time (Go model) — PROPOSED
- Hash algorithm: SHA-256 of raw bytes. Period.
- Registry conformance: "A conforming registry MUST normalize text file line endings to LF before computing content hashes"
- Text/binary detection: defined in registry conformance section using extension-based allowlist
- Complexity lives in tooling (Registry Action), not in the core algorithm

### Option 2: Normalization inside the hash algorithm
- Hash algorithm includes text/binary detection and CRLF→LF normalization
- Most deterministic for interop
- But: every implementer must build normalization into hashing code — "the level of complexity we're expecting people to implement and not fuck up" (per reviewer feedback)

### Option 3: Hash raw bytes, no normalization anywhere (OCI model)
- Simplest spec
- Same content from Windows vs Linux = different hashes
- Defeats cross-platform consistency goal

## Stress Test Scenarios

### Scenario 1: Happy path (single registry, single source)
Registry crawls repo, normalizes, hashes, signs. Client verifies by re-hashing received bytes.
**Result:** Works. No issues.

### Scenario 2: Same skill, two conforming registries
Both normalize the same way → same content hash. Cross-registry identity works.
Non-conforming registry → different hash. Detectable conformance bug.
**Result:** Works when conforming. Non-conformance is the registry's bug, not a spec flaw.

### Scenario 3: Developer verifies against source
Linux: repo files already LF, normalization is no-op. Matches.
Windows with autocrlf: MOAT tooling normalizes CRLF→LF. Matches.
Without MOAT tooling: raw `sha256sum` won't match (expected — same as Go/npm).
**Crack identified:** can't verify with just `sha256sum`. But already true due to directory hashing (sort, per-file hash, concatenation). MOAT tooling required regardless.

### Scenario 4: Binary file in skill directory
Extension-based detection: .png/.wasm not on text list, hashed as-is. Safe.
Binary file misnamed as .txt: normalization corrupts hash input, but actual stored content unchanged. Authoring error, not protocol flaw.
**Result:** Safe.

### Scenario 5: Extensionless files
Default to binary. Minor mismatch risk for files like LICENSE/Makefile.
Uncommon in AI agent content (mostly .md, .yaml, .json, .ts, .py).
Optional small known-names allowlist for common extensionless files.
**Result:** Low concern.

### Scenario 6: Adversarial case
Normalization only affects hash input, not stored content. Hash verifies you received what was published. Malicious content is a curation problem, not a hashing problem.
**Result:** No new attack surface.

## Stress Test Summary

| Scenario | Outcome | Concern |
|----------|---------|---------|
| Happy path | Works | None |
| Two conforming registries | Same hash | None |
| Non-conforming registry | Different hash (their bug) | Low |
| Manual verification without tooling | Hash won't match | Low (expected) |
| Binary files | Safe | None |
| Extensionless files | Default binary, minor risk | Low |
| Adversarial | No new attack surface | None |

## Key Arguments For This Approach

1. **Hash algorithm stays trivially simple.** "SHA-256 of raw bytes" — anyone can implement, impossible to get wrong.
2. **Normalization lives in the right place.** Registry conformance section, not hash algorithm. Matches MOAT's architecture: registries do the work, not creators.
3. **Go model is proven.** Same architecture has worked for Go modules since 2019.
4. **Extension-based detection is deterministic.** Same file always classified the same way. Safe failure mode.
5. **Complexity in tooling, not in spec.** The Registry Action handles normalization. Third-party tools follow the conformance requirements.

## Key Arguments Against (for panel discussion)

1. **Normalization is implementation-defined.** If a third-party registry tool normalizes differently, hashes diverge. The spec can't enforce correct normalization the way it can enforce a hash algorithm.
2. **Extension list maintenance.** Needs updating as new file types emerge. Who decides? Spec version bump for a new extension?
3. **"Raw bytes" is a simplification.** Users might expect the hash to match what's on disk, but post-normalization bytes differ from source bytes on Windows. Could cause confusion.
4. **The reviewer's broader concern still applies.** "Multiple implementations will fuck it up" — just moved from the hash algorithm to the registry conformance section.

## Open Questions for Panel

1. Is the Go model (normalize at publish boundary) the right architecture, or should normalization be in the hash algorithm for maximum determinism?
2. Extension-based text detection: is the safe failure mode (unrecognized text → binary) acceptable, or do we need content-based fallback?
3. Should the spec define the text extensions list normatively, or should it be an informative recommendation that registries can extend?
4. Extensionless files: binary by default, or maintain a known-names allowlist?
5. Is the inability to verify with raw `sha256sum` an acceptable trade-off?

## Sources
- Git gitattributes docs, convert.c source
- Go golang.org/x/mod/zip, dirhash package, golang/go#29281
- Cargo cargo#12897
- npm npm/npm#13203
- OCI Distribution Spec
- RFC 2045 (MIME)
- WHATWG MIME Sniffing Standard
