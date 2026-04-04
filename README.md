# MOAT — Metadata for Origin, Authorship, and Trust

A portable sidecar format for recording provenance of AI coding tool content.

| | |
|---|---|
| **Version** | 0.3.0 (Draft) |
| **Status** | Draft — not yet validated by multiple independent implementations |
| **Specification** | [`moat-spec.md`](moat-spec.md) |
| **License** | [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |

## The Problem

AI coding tool content — skills, agents, hooks, rules, MCP configurations, and commands — is increasingly authored, shared, and installed across tools and organizations. As this ecosystem grows, consumers need answers to basic provenance questions:

- **Who made this?**
- **Has it been modified?**
- **Where did it come from?**
- **What was it derived from?**

The ecosystem has mature standards for content formats and packaging, but no standard addresses provenance. MOAT fills this gap.

## What MOAT Provides

MOAT defines a single `meta.yaml` sidecar file placed alongside content. The sidecar records a four-link trust chain:

1. **Content integrity** — SHA-256 of the directory tree manifest
2. **Metadata integrity** — SHA-256 of provenance metadata bound to the content hash
3. **Identity binding** — Cryptographic signature via [Sigstore](https://sigstore.dev) or SSH
4. **Source binding** — Verification that the signer controls the claimed source repository

Without a signature, provenance metadata is informational. With a signature, it's cryptographically verifiable. With source binding, it's end-to-end: from content files to the repository that produced them.

## Key Design Decisions

- **Tool-agnostic.** Any content management or distribution system can produce and consume MOAT metadata.
- **Platform-side, not author-side.** Content authors click "Publish" — the platform computes hashes, signs, and produces `meta.yaml`. MOAT is the interoperability contract between platforms.
- **Sigstore-native.** Keyless signing via OIDC identity, transparency logging via Rekor, ephemeral certificates via Fulcio. No long-lived keys to manage.
- **Graceful degradation.** Content without `meta.yaml` still works. Unsigned content with `meta.yaml` provides informational provenance. The trust chain is additive.

## Specification

The full specification is in [`moat-spec.md`](moat-spec.md). It covers:

- Sidecar format and field definitions (Section 5)
- Conformance classes for publishers, consumers, and registries (Section 6)
- Content hash algorithm with symlink resolution and NFC normalization (Section 7)
- Meta hash algorithm with JCS canonicalization (Section 8)
- Sigstore and SSH signing methods (Section 9)
- Lineage model for forks, conversions, and adaptations (Section 10)
- Security considerations — 26 subsections covering trust model through OIDC token exfiltration (Section 11)
- Normative test vectors (Appendix B)

## Status

MOAT is a Draft specification. Before advancing beyond Draft:

- Test vectors (Appendix B) must be confirmed by at least two independent implementations in different languages.
- No reference implementation exists yet. This repository contains only the specification.

See [`CHANGELOG.md`](CHANGELOG.md) for version history.

## Contributing

This specification is in active development. Feedback is welcome via [GitHub Issues](https://github.com/OpenScribbler/moat/issues).

Areas where feedback is especially valuable:

- Ambiguities or contradictions in normative language
- Security considerations that are missing or under-specified
- Implementation experience reports (especially cross-language YAML parsing behavior)
- Test vector validation against independent implementations

## License

Copyright 2026 Holden Hewett. Licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
