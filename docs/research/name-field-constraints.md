# Name Field Constraints Research

**Date:** 2026-04-06
**Decision:** ASCII-only, regex-defined, 128-character MUST limit
**Status:** Resolved

## Research Question

How should MOAT constrain the `name` field in registry manifest entries? The v0.3.0 draft had a 128-character limit that was arbitrary, and "character" is ambiguous cross-language (bytes vs code points vs grapheme clusters).

## Ecosystems Studied

### npm
- **Characters:** Lowercase ASCII alphanumeric + `-._`. No `~)('!*` or non-URL-safe characters.
- **Length:** 214 (UTF-16 code units, but effectively bytes since ASCII-only).
- **Scoping:** `@scope/name`.
- **Definition:** Procedural (series of if-checks), not regex.
- **Normalization:** Lowercase required.

### Cargo / crates.io
- **Characters:** ASCII alphanumeric + `-_`. Explicitly ASCII-only.
- **Length:** 64 characters (code points, but ASCII-only so = bytes).
- **Scoping:** None (flat namespace).
- **Definition:** Implied regex `^[a-zA-Z0-9_-]+$`.
- **Normalization:** Hyphens and underscores treated as equivalent (`foo-bar` == `foo_bar`).

### Go Modules
- **Characters:** ASCII alphanumeric + `-._~`.
- **Length:** No explicit limit.
- **Scoping:** Domain-based paths (`github.com/user/repo`).
- **Definition:** Prose constraints.

### OCI / Container Registries
- **Characters:** Lowercase alphanumeric + `-._/` (with separator rules).
- **Length:** 255 for full reference (repo), 128 for tags.
- **Scoping:** `registry/namespace/repo`.
- **Definition:** Formal regex — the gold standard. Tag regex: `[\w][\w.-]{0,127}`.

### PyPI
- **Characters:** ASCII alphanumeric + `-._`.
- **Length:** No explicit limit.
- **Scoping:** None (flat namespace).
- **Definition:** Formal regex `^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$` (case-insensitive).
- **Normalization:** Most aggressive — collapses `-`, `_`, `.` runs into single `-`.

### Homebrew
- **Characters:** Lowercase alphanumeric + `-_@`.
- **Length:** No explicit limit.
- **Scoping:** Tap-based (`user/repo/formula`).
- **Definition:** Convention/prose.

### Helm
- **Characters:** Lowercase alphanumeric + `-`. RFC 1123 DNS label.
- **Length:** 63 (DNS label limit).
- **Scoping:** OCI registry paths.
- **Definition:** Regex inherited from RFC 1123.

## Key Patterns

### Every ecosystem is ASCII-only
None allow Unicode in package names. The bytes-vs-characters ambiguity doesn't arise in practice because 1 ASCII byte = 1 character in every language.

### Length limits cluster around 64-128
Cargo: 64. OCI tags: 128. Helm: 63. npm: 214 (outlier, historical). Go/PyPI/Homebrew: unlimited.

### Regex is the best definition method
OCI and PyPI use formal regex. This is clearest, most implementable, eliminates prose ambiguity, and is directly usable as a validator.

### Separator normalization prevents confusion
Cargo (`-` = `_`) and PyPI (`-` = `_` = `.`) normalize separators. Simplest approach: allow only one separator character.

## Unicode Consideration

Real-world data shows Chinese and other non-Latin characters in AI skill names (from 180K+ skill corpus analysis). However:

- No established registry allows Unicode names
- Unicode introduces normalization, homoglyph, and cross-implementation divergence risks
- ASCII is valid UTF-8 — extending to Unicode later is a clean, non-breaking migration
- Starting with Unicode and discovering normalization bugs is a breaking fix

**Decision:** ASCII for v0.4.0 with forward-looking note about future UTF-8 extension. Prove the protocol first, expand character space later.

## Decision Details

- **Regex:** `[a-z0-9][a-z0-9-]*[a-z0-9]` (lowercase alphanumeric + hyphens, start/end with alphanumeric)
- **Length:** 128 characters, MUST (normative). OCI precedent. Bytes = characters since ASCII-only.
- **Separator:** Hyphen only. No normalization needed.
- **Scoping:** Separate design question (not resolved here).

## Sources
- [validate-npm-package-name](https://github.com/npm/validate-npm-package-name)
- [Cargo Manifest Reference](https://doc.rust-lang.org/cargo/reference/manifest.html)
- [Go Modules Reference](https://go.dev/ref/mod#module-path)
- [OCI Distribution Spec](https://github.com/opencontainers/distribution-spec/blob/main/spec.md)
- [PEP 508](https://peps.python.org/pep-0508/)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Helm Conventions](https://helm.sh/docs/chart_best_practices/conventions/)
