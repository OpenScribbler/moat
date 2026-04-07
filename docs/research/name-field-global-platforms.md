# Name Field Research: Global Platforms and Content Registries

**Date:** 2026-04-06
**Decision:** Two-layer model — ASCII `name` (machine ID) + optional UTF-8 `display_name` (human label)
**Status:** Resolved
**Context:** Follow-up research after agent ecosystem reviewer flagged Chinese characters in skill names. Initial research only covered developer-facing package registries (all ASCII). This round examined app stores, AI platforms, and internationalization specs.

## Research Question

Is the ASCII-only approach for identifiers too restrictive for a globally-used AI content protocol? How do platforms serving global, non-developer audiences handle naming?

## App Stores and Content Platforms

### Google Play Store
- **Machine ID:** Application ID (`com.example.myapp`). Strictly ASCII: `[a-zA-Z0-9_]` with dot separators. Reverse-DNS. Immutable once published.
- **Display name:** Separate field. Fully localizable per-market. Unicode.
- **Two-names confusion:** Not a problem — users never see the Application ID.

### Apple App Store
- **Machine ID:** Bundle Identifier (`CFBundleIdentifier`). ASCII-only: "only Roman alphabet upper/lower case (A-Z, a-z), dot (.), and hyphen (-)." Even more restrictive than Android.
- **Display name:** `CFBundleDisplayName`. Separate, localizable. Full Unicode.
- **Two-names confusion:** Clean separation. Users see display name on Home Screen/Siri. Bundle ID is invisible.

### WordPress Plugin Directory
- **Machine ID:** Plugin slug. ASCII-only. "Only English letters and Arabic numbers are permitted." Auto-generated from plugin name. Permanent after approval.
- **Display name:** Separate field. Mutable.
- **Two-names confusion:** Slug appears in URLs, so users do see it. Known pain point when branding changes but slug can't.

### Chrome Web Store
- **Machine ID:** System-generated 32-character hash of extension's public key. Opaque, meaningless to humans.
- **Display name:** `name` field in manifest.json. Localizable via `_locales`. Full Unicode.
- **Two-names confusion:** Nonexistent — nobody tries to remember a Chrome extension ID.

### Hugging Face
- **Machine ID:** `{owner}/{repo-name}`. ASCII alphanumeric + hyphens/underscores/dots. No separate display name.
- **Two-names confusion:** Avoided by having only one name, but forces ASCII on global users.
- **Note:** Non-English orgs use English or romanized names (e.g., `Qwen/Qwen2.5-72B` from Alibaba).

## AI-Specific Platforms

### Ollama
- **Machine ID:** Docker-style: `{host}/{namespace}/{model}:{tag}@{digest}`. All ASCII. Namespace/model: `[a-zA-Z0-9_]` start, then `[a-zA-Z0-9_.-]`. Max 80 chars each.
- **Display name:** None. Single name only.
- **Note:** Intentionally follows Docker conventions for developer familiarity.

### FlowGPT (Prompt Marketplace)
- **Machine ID:** System-generated opaque ID (likely UUID).
- **Display name:** Separate `promptTitle`. Unicode supported. Consumer-facing.
- **Two-names confusion:** URL uses opaque ID, so renaming doesn't break links.

### Smithery (MCP Server Registry)
- **Machine ID:** npm-style `@scope/name`. ASCII alphanumeric + hyphens.
- **Display name:** Separate, updatable via API. Independent of identifier.

## Internationalization Specs

### IRIs (RFC 3987)
- Extend URIs to allow Unicode via well-defined mapping: NFC normalization → UTF-8 encoding → percent-encoding.
- Every IRI has a canonical URI form. Every URI is already a valid IRI.
- Proves Unicode identifiers are viable in protocols but require clear canonical form and ASCII mapping.

### PRECIS Framework (RFC 8264)
- IETF's recommendation for Unicode in protocol identifiers. Replaces older Stringprep.
- Defines two string classes:
  - **IdentifierClass** — restrictive (letters, numbers, minimal punctuation). For usernames, room names, protocol identifiers.
  - **FreeformClass** — permissive (letters, numbers, symbols, spaces). For passwords and display names.
- Normalization pipeline: width mapping → additional mappings → case mapping → NFC → directionality.
- Unicode-version-agile (classifies by property, not enumerated code points).
- **Key insight:** PRECIS formalizes the exact split we're using — `name` maps to IdentifierClass, `display_name` maps to FreeformClass.

### WHATWG URL Spec (IDN)
- Unicode domain labels converted to ASCII via Punycode.
- Created real-world problems: homograph attacks, user confusion about Unicode vs Punycode forms, inconsistent browser display.
- The "two names" problem is very real here — `münchen.de` and `xn--mnchen-3ya.de` look completely different.
- Lesson: forcing Unicode into protocol plumbing creates security and UX issues.

## Cross-Cutting Patterns

### The universal two-layer model
Every global platform converges on:
| Layer | Purpose | Character set | Mutability |
|-------|---------|---------------|------------|
| Machine ID | Routing, dedup, resolution | ASCII (restrictive) | Immutable |
| Display name | Human presentation, discovery | Unicode (permissive) | Mutable |

Platforms without display names (Hugging Face, Ollama) serve predominantly English-speaking developer audiences.

### Key lessons
- **Immutability of machine ID is critical.** Platforms that allow renaming identifiers regret it or build redirect systems.
- **Scoping (`@scope/name`) prevents biggest practical problems.** Name squatting, collisions, attribution.
- **"Two names" confusion is manageable.** App stores have handled it for 15+ years. Display name dominates in user-facing contexts.
- **Opaque IDs hurt developer ergonomics.** For developer-facing registries, readable identifiers (`@alice/git-hooks`) matter.

## Decision Rationale

Two-layer model chosen because:
1. Content appears in config files and CLI commands — ASCII is a practical requirement for the machine identifier
2. Unicode-in-identifiers is not proven at scale (IDN's problems are instructive)
3. The display name layer is where global inclusivity lives — search, discovery, and UI all use it
4. PRECIS framework (RFC 8264) formalizes exactly this pattern as IdentifierClass/FreeformClass
5. 15+ years of app store precedent proves the model works

Spec must clearly disambiguate the two fields: `name` is protocol plumbing (machines), `display_name` is presentation (humans). `display_name` is completely optional — content without it falls back to `name` for display.

## Sources
- Google Play Application ID: developer.android.com
- Apple Bundle Identifier: developer.apple.com
- WordPress Plugin Slugs: developer.wordpress.org/plugins
- Chrome Extension IDs: developer.chrome.com/docs/extensions
- Hugging Face Model Hub: huggingface.co/docs
- Ollama Model Library: github.com/ollama/ollama
- Smithery MCP Registry: smithery.ai/docs
- RFC 3987 (IRIs)
- RFC 8264 (PRECIS Framework)
- WHATWG URL Spec: url.spec.whatwg.org
