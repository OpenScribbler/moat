# Write a Specification

Step-by-step workflow for writing a new MOAT sub-spec or a new section of `moat-spec.md`. For a new section of an existing spec, skip Steps 1, 2, 4, and 5, and run Step 3 and Steps 6 to 10 on the section.

## Pre-flight

Before writing, answer these questions:

1. **What does this spec define?** (One sentence. If you need two, the scope is too broad.)
2. **Who are the conformance classes?** (Which MOAT actors must follow it: Publisher, Registry, Conforming Client, End User? The core spec's Actors section and `lexicon.md` name them.)
3. **Is it a sub-spec of `moat-spec.md`?** (Almost always yes. Read `references/companion-and-extension-specs.md` first.)
4. **Which core version does it require?** (The lowest `moat-spec.md` version that has every core rule it depends on.)

## Step 1: Skeleton

Create the document with this section structure. Do NOT fill in content yet — just headings.

```markdown
# [Spec Title] Specification

**Version:** 0.1.0 (Draft)
**Requires:** moat-spec.md ≥ [x.y.z]
**Part of:** [MOAT Specification](../moat-spec.md)

> [One-paragraph abstract.]

---

## Introduction

## Requirements Language

## Conformance

## [Technical Sections — name based on domain]

## Security Considerations

## References

### Normative References

### Informative References

```

Add after Introduction:

```markdown
## Relationship to the MOAT Specification
```

Save the file under `specs/`, or under `specs/github/` for a GitHub Action, where the `Part of:` link becomes `../../moat-spec.md`. Add it to the `**Sub-specs:**` line in the `moat-spec.md` header.

## Step 2: Abstract

Write 2-4 sentences in the blockquote under the header. Rules:
- Self-contained: no citations, no references, no undefined terms
- Describes what the spec IS, not what it hopes to achieve
- No RFC 2119 keywords
- A reader seeing ONLY the abstract should understand the spec's purpose

## Step 3: Terminology

Check every term the spec will use against `lexicon.md`, and use the bold canonical name, never a listed alias. A term with a meaning specific to this spec that the lexicon lacks goes into `lexicon.md` in the same change, in its table format.

Do this BEFORE writing technical sections. You need the vocabulary before you can write requirements.

## Step 4: Requirements Language

Insert the RFC 2119/8174 boilerplate verbatim:

```
The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all
capitals, as shown here.
```

Add RFC 2119 and RFC 8174 to Normative References immediately.

## Step 5: Conformance

Define each class. For each class, state:
- Who is in this class (e.g., "a Conforming Client that installs npm-distributed Content Items")
- What sections apply to them
- What level of compliance is required (all MUST? all MUST + SHOULD?)

See `references/document-structure.md` for examples.

## Step 6: Technical Sections

Write the normative content. For each field, requirement, or mechanism:

1. **State the requirement** using RFC 2119 keywords
2. **Specify defaults** for optional fields ("If absent, X")
3. **Define error handling** ("If malformed, agents MUST/SHOULD...")
4. **Provide an example** (after the normative text, not instead of it)
5. **Add rationale** in a block labeled `(informative)` if the "why" isn't obvious; a design choice with rejected alternatives gets an ADR under `docs/adr/`
6. **Label it** with MOAT's forms: `(normative)` in the heading or a `**Label (normative).**` paragraph lead

### Self-check per section

- [ ] Every RFC 2119 keyword is justified (interop or harm prevention)
- [ ] Every optional field has a default
- [ ] No "because X, MUST Y" patterns (separate rationale from requirements)
- [ ] Examples illustrate but don't define
- [ ] No paths outside the repo; normative cross-references use `<path>:<line>` (`.claude/rules/spec-citations.md`)

## Step 7: Security Considerations

Address:
- What can be spoofed, forged, or faked?
- What self-asserted claims exist? What's the risk of trusting them?
- Are there executable components? What's the blast radius?
- What happens if integrity checks fail?
- What's the trust model?

This section is REQUIRED. "Security was not considered" is not acceptable.

## Step 8: References

Go through the entire document and, for every external document cited:
1. List every document cited → add to References
2. Classify each as Normative or Informative
3. For each entry: Author, Title, Date, Stable URL
4. Verify no orphans (every citation has an entry, every entry is cited)

## Step 9: Informative content

MOAT keeps informative content in the section it explains, under an `(informative)` label, and has no appendices:
- Implementation mapping tables, such as `**Mapping to common npm-client architectures (informative):**` in `specs/npm-distribution.md`
- Rationale, in a `**Rationale (informative):**` paragraph after the requirement it explains
- Design reasoning too long to sit inline, with the alternatives rejected, goes in an ADR under `docs/adr/` rather than in the spec

## Step 10: Changelog and final audit

Add a `CHANGELOG.md` entry under `[Unreleased]` per `.claude/rules/changelog.md`, stating whether the change is normative or editorial, and pick the bump level from `RELEASING.md`, whose pre-1.0 notice makes a breaking change a MINOR bump while the version is `0.x.y`. Then run the audit workflow (`workflows/audit-spec.md`) on your own draft and fix what it finds.

## Sub-spec additions

For a new sub-spec, also complete:
- [ ] "Relationship to the MOAT Specification" section with dependency direction and conformance relationship
- [ ] `Requires:` line naming the lowest core version it works with
- [ ] No redefined terms that conflict with the core spec or `lexicon.md`
- [ ] Explicit statement about what this sub-spec adds vs. what the core spec defines

See `references/companion-and-extension-specs.md` for details.
