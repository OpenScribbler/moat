# moatspec.org Website Plan

## Scope Decisions (Locked)

- **Option B: Spec + guides** — not spec-only, not full ecosystem
- **Single-page spec** with sticky TOC sidebar and section anchors
- **URL-based versioning** (`/spec/v0.3/`)
- **Guides at launch:** threat model + implementer notes
- **Blog at launch:** one "Introducing MOAT" post
- **Deferred:** adopters page, tools registry, enhancement proposals, FAQ

## Site Structure

```
moatspec.org/
├── /                          # Landing page
├── /spec/v0.3/                # Full spec, single page, sticky TOC
├── /get-started/              # Orientation — what, why, who, quick overview
├── /guides/
│   ├── threat-model/          # Attack scenarios, security context
│   └── implementers/          # Practical notes for tool authors
├── /community/                # GitHub, contribution guidelines, contact
├── /blog/
│   └── introducing-moat/      # Launch post
└── /about/                    # License, governance, project history
```

## Tech Stack

- **Astro + Starlight** — Holden's expertise, markdown-native, built for docs/specs
- **Hosting:** TBD (Vercel, Netlify, or GitHub Pages)
- **Domain:** moatspec.org (needs registration)

## Implementation Tasks

### Phase 1: Project Setup
1. Initialize Astro/Starlight project in a new directory (or `website/` subdirectory)
2. Configure Starlight with MOAT branding (colors, logo, favicon)
3. Set up URL-based versioning structure for `/spec/v0.3/`
4. Configure sidebar navigation

### Phase 2: Content Migration
5. Migrate `moat-spec.md` into Starlight as a single-page spec
   - Ensure section anchors work for deep linking
   - Add "View on GitHub" link
   - Verify sticky TOC sidebar auto-generates correctly
6. Write landing page content (hero, what/why/who, CTA)
7. Write get-started page
8. Extract threat model from spec security considerations into guide
9. Write implementer notes guide
10. Write community page (GitHub link, contribution guidelines)
11. Write about page (license, governance basics)

### Phase 3: Blog
12. Write "Introducing MOAT" blog post
13. Configure blog with RSS feed

### Phase 4: Polish & Deploy
14. Test all internal links and section anchors
15. Set up deployment pipeline
16. Configure custom domain (moatspec.org)
17. Add OpenGraph/meta tags for social sharing

## Research Sources

Patterns drawn from analysis of 7 spec websites:
- **SLSA** (slsa.dev) — closest structural analog, clean spec/guides separation
- **Sigstore** (sigstore.dev) — three-site split (overkill for us)
- **TUF** (theupdateframework.io) — URL-based versioning, TAPs process
- **OpenTelemetry** (opentelemetry.io) — role-based onboarding, status matrix
- **in-toto** (in-toto.io) — adopters table, GitHub-hosted specs
- **SPDX** (spdx.dev) — persona-based nav (About/Learn/Engage/Use)

Key takeaways:
- Render spec on-site (don't just link to GitHub like Sigstore/in-toto)
- URL-based versioning is universal (`/spec/v{X.Y}/`)
- Separate normative spec from practical guides
- Empty sections (adopters, tools) look worse than no section — add when real
- Single "Introducing X" blog post gives the site life without committing to a cadence
