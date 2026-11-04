# Document Structure

Required and recommended sections for a technical specification, based on RFC 7322, W3C Manual of Style, and community spec conventions.

## Section Order

The following order is conventional. Not every spec needs every section, but when present, they should appear in this order.

### Front Matter

1. **Title** — Concise, descriptive. No marketing language.
2. **Version** — Semver string (e.g., `0.1.0`).
3. **Status** — Draft, Proposed, Stable, etc. One clear label.
4. **Abstract** — 2-4 sentences. MUST be self-contained: no citations, no references, no undefined terms. This will appear in indexes and search results separate from the full document.

### Body (Numbered Sections)

1. **Introduction** — Context, motivation, scope. Establishes what problem this spec solves and who it's for. Should be understandable without reading any other section.

2. **How to Read This Document** *(recommended for companion specs)* — Who should read this vs. the parent spec. What this document adds, restricts, or profiles.

3. **Terminology** — Define every term used in normative sections before first use. In MOAT, `lexicon.md` holds the canonical terms; a spec uses them verbatim. If borrowing terms from another spec, cite the source and version.

4. **Requirements Language** — The RFC 2119/8174 boilerplate. See `rfc2119-guide.md` for the exact text.

5. **Conformance** — Define conformance classes: who must conform (agents, registries, authors, tools?) and what conformance means for each class. See examples below.

6. **Technical Specification** — The normative meat. Requirements, field definitions, algorithms, schemas. This is where MUST/SHOULD/MAY statements live.

7. **Security Considerations** — REQUIRED, even for metadata specs. Analyze actual security implications. "Security was not considered" is explicitly unacceptable per RFC 2360.

8. **References** — Split into two subsections:
   - **Normative References** — Documents required to implement this spec.
   - **Informative References** — Background, context, related reading. Not required for implementation.

### Back Matter (Unnumbered)

9. **Appendices** — MOAT specs have none; informative content stays inline under `(informative)` labels. Elsewhere, label each "(Informative)" or "(Normative)" in the heading. Most appendices are informative. Informative appendices MUST NOT contain RFC 2119 keywords.

10. **Acknowledgements** *(optional)* — Contributors, reviewers, influences.

11. **Change Log** — What changed between versions. MOAT keeps it in `CHANGELOG.md` rather than in the spec, under `.claude/rules/changelog.md`.

## Conformance Clause Examples

### Simple (single class)

```
## Conformance

An implementation conforms to this specification if it satisfies all
MUST and MUST NOT requirements. An implementation that additionally
satisfies all SHOULD requirements is said to be "fully conformant."
```

### Multi-class (different actors)

```
## Conformance

This specification defines three conformance classes:

**Conforming Publisher.** A Publisher conforms if its published
content and attestations satisfy every MUST requirement in the
sections that name the Publisher.

**Conforming Registry Operator.** A Registry Operator conforms if
the Registry Manifest, signatures, and revocations it publishes
satisfy every MUST requirement in the sections that name the
Registry Operator.

**Conforming Client.** A client conforms if it satisfies every
MUST requirement in the sections that name the Conforming Client.
Support for informative profiles is OPTIONAL.
```

## Security Considerations Examples

### Metadata spec

```
## Security Considerations

All provenance fields in this convention are self-asserted. Any skill
can claim any source_repo, any author, any content_hash. Consumers
MUST NOT make trust decisions based solely on self-asserted provenance
without independent verification (see Section 8, Attestation).

The script_hashes field enables integrity verification but does not
guarantee safety. A verified hash proves the bytes match — not that
the script is safe to execute.

Skills may contain executable scripts. Of the agents surveyed during
development, several auto-load skills without user approval. Skill
authors SHOULD document trust requirements in the skill body.
Distribution tools SHOULD warn users before installing skills that
contain executable files.
```

## What NOT to Include in Structure

- **No unlabeled "Motivation" or "Why" section in normative body.** Rationale belongs in a section or paragraph labeled `(informative)`, or in an ADR under `docs/adr/`. See `normative-vs-informative.md`.
- **No marketing or ecosystem-building language.** "To enable a vibrant ecosystem..." is not spec language. State what the spec defines, not what it hopes to achieve.
- **No changelog in the abstract.** The abstract describes what the spec IS, not what changed.
