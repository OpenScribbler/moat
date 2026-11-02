---
name: spec-writing
description: Write and audit MOAT's normative specs (moat-spec.md and the sub-specs under specs/) against IETF and W3C spec-writing norms and this repo's own conventions. Use when drafting a new spec or sub-spec, editing normative text, reviewing a spec draft, or checking RFC 2119 keyword use, normative/informative separation, references, conformance, or versioning.
---

# Spec Writing

Guidelines and workflows for writing MOAT's specifications so they follow standards-body conventions (IETF RFC, W3C, community specs) and this repo's own rules.

## MOAT's spec documents

| Document | Role |
|----------|------|
| `moat-spec.md` | The core specification. Its header carries the version and stage, such as `0.8.0 (Draft)`. |
| `specs/*.md`, `specs/github/*.md` | Sub-specs. Each is a companion to the core spec, versioned on its own, with `**Requires:** moat-spec.md ≥ x.y.z` and `**Part of:**` lines in its header. |
| `website/src/content/docs/spec/` | Website mirrors of each spec: `core.md` for `moat-spec.md`, and one page per sub-spec under the sub-spec's file name. |
| `lexicon.md` | Canonical vocabulary. Bold canonical names are used verbatim; listed aliases are avoided. |
| `CHANGELOG.md` | Public change record. Every spec edit gets an entry in the same commit. |
| `RELEASING.md` | Version bump levels, maturity stages, sub-spec versioning. |
| `docs/adr/` | Decision records for normative choices, with their context and the alternatives rejected. |

## MOAT conventions that override the generic guidance

The references describe IETF and W3C norms. Where this repo has its own rule, the repo wins:

1. **Repo-relative paths are allowed.** The repository is where the spec is published, so links from a spec to other published files in it (`specs/`, `lexicon.md`, `reference/`, `docs/`) are stable references. A path outside the repo, to an unmerged branch, or to working notes that never ship (such as `panel/`) is still never acceptable.
2. **Normative cross-references use `<path>:<line>`.** A citation names the line of the normative sentence it anchors on, such as `specs/npm-distribution.md:145`. In the `## Conformance (normative)` error-code table that line must hold `MUST` or `MUST NOT`; elsewhere in a spec body it may also hold `SHOULD`, which is what CI's `slice-8-error-codes.sh` accepts. `.claude/rules/spec-citations.md` has the full rule. A citation that no longer lands on such a line is stale and is fixed in the same commit as the edit that moved it.
3. **Normative and informative content is marked inline, not in appendices.** MOAT labels headings, such as `### Registry Index Format (normative)`, and paragraph leads, such as `**Signature scheme (normative).**` or `**No separate revocation endpoint (informative):**`. Sub-specs also name the keyword, as in `(normative — MUST)`, `(normative — MUST NOT)`, or `(normative — SHOULD)`, and some write `(Informative)` capitalized. Rationale and implementation mapping stay in the section they explain, under an `(informative)` label; no MOAT spec has an appendix. Where the generic references say to move content into an informative appendix, use an inline `(informative)` block instead.
4. **`lexicon.md` is the terminology source.** Check every defined term against it. A term the spec uses normatively that the lexicon lacks, or an alias the lexicon lists to avoid, is a finding.
5. **Every spec edit lands in its website mirror in the same commit.** Carry the edit to the mirror page under `website/src/content/docs/spec/`, following that mirror's own convention. `specs/npm-distribution.md`'s mirror is byte-identical below its frontmatter, and CI checks that with `specs/conformance/npm-distribution/slice-12-mirror.sh`. The other four mirrors are adapted: no H1, the header in a `:::note[Spec metadata]` block, the abstract unwrapped, and repo links rewritten, so a link to another spec becomes a `/spec/<page>` route (`/spec/core#<anchor>` for `moat-spec.md`) and a link to other repo files becomes a GitHub URL or a plain code span. Diff the mirror against its source before editing to see what it changes. A new sub-spec needs a new mirror page and a sidebar entry in `website/astro.config.mjs`.
6. **Every spec edit gets a changelog entry.** `.claude/rules/changelog.md` governs: log the edit under `[Unreleased]`, say whether it is normative or editorial, and keep internal process metadata out.
7. **Version bumps follow `RELEASING.md`.** Its table rates a normative inversion (MUST to SHOULD) MAJOR, a new SHOULD or optional field MINOR, and a clarification with no normative change PATCH. Its pre-1.0 notice overrides the table while the version is `0.x.y`: any minor version may break compatibility, so a breaking change ships as a MINOR bump (0.8.0 to 0.9.0), and 1.0.0 comes only with the Stable stage. When a sub-spec starts depending on a newer core rule, its `Requires:` line moves.
8. **`(Draft)` in a header is the document's stage, not a field's stability.** Every MOAT spec is `(Draft)` today, and its MUSTs are binding. The generic rule against MUST on draft content applies only to content a spec labels with a per-field or per-item stability level, never to the document stage.
9. **npm error codes carry citations.** Each `NPM-<SECTION>-<NN>` code in the `## Conformance (normative)` table of `specs/npm-distribution.md` cites the line of its MUST. CI checks these with the scripts in `specs/conformance/npm-distribution/`.

## Workflow routing

| Workflow | Trigger | File |
|----------|---------|------|
| **WriteSpec** | "write a spec", "new sub-spec", "draft a section" | `workflows/write-spec.md` |
| **AuditSpec** | "audit the spec", "review this section", "check spec" | `workflows/audit-spec.md` |

When invoked without arguments, display the Quick Checklist below.

## References

| File | Purpose |
|------|---------|
| `references/document-structure.md` | Required sections, ordering, what goes where |
| `references/rfc2119-guide.md` | RFC 2119/8174 keyword rules, boilerplate, usage examples |
| `references/references-and-citations.md` | Normative vs informative references, citation format |
| `references/normative-vs-informative.md` | Separating binding requirements from rationale |
| `references/companion-and-extension-specs.md` | Patterns for sub-specs that companion the core spec |
| `references/stability-and-versioning.md` | Maturity levels, semver for specs, promotion criteria |
| `references/anti-patterns.md` | Categorized spec-writing mistakes with examples |
| `references/source-standards.md` | Links to authoritative spec-writing standards |

## Quick checklist

A fast pass on any spec draft. Each item has a reference file with details.

### Structure
- [ ] Has an abstract or introduction (self-contained, no citations in the abstract)
- [ ] Defined terms match `lexicon.md` and are defined before first normative use
- [ ] Has a conformance section defining who must conform and what conformance means
- [ ] Has a Security Considerations section (not optional, even for metadata specs)
- [ ] Every cited external document has a reference entry, normative and informative kept apart
- [ ] Appendices and sections are labeled normative or informative

### Language
- [ ] RFC 2119/8174 boilerplate is present and cites BOTH RFCs
- [ ] RFC 2119 keywords appear ONLY in normative content
- [ ] No normative-sounding language in informative content
- [ ] Normative text is declarative (no persuasive or justification language)
- [ ] Rationale sits in separate informative blocks or in an ADR under `docs/adr/`

### References
- [ ] No paths outside the repo, to unmerged branches, or to working notes
- [ ] Normative cross-references cite `<path>:<line>` on a MUST, MUST NOT, or (outside the error-code table) SHOULD line
- [ ] Every in-text citation has a corresponding entry, and every entry is cited
- [ ] Data sources are published and verifiable, or findings are summarized inline

### Self-containment
- [ ] Normative content is implementable without reading informative sections
- [ ] Normative content is implementable without chasing unpublished documents
- [ ] Examples illustrate but do not define (normative text stands alone)

### Versioning and stability
- [ ] Version and stage label match actual maturity (`0.x (Draft)` = unstable)
- [ ] No contradiction between "Stable" labels and a 0.x version
- [ ] The edit's bump level matches `RELEASING.md`, pre-1.0 notice included
- [ ] The edit has a `CHANGELOG.md` entry stating normative or editorial
- [ ] The edit is carried to the spec's mirror under `website/src/content/docs/spec/`, with links converted where that mirror converts them

### Sub-specs
- [ ] `Requires:` and `Part of:` lines are present and current
- [ ] What the sub-spec adds versus what the core spec defines is stated near the top
- [ ] Core terms are used as the core spec and `lexicon.md` define them, never redefined

## Gotchas

- **RFC 8174 exists.** Many spec authors cite only RFC 2119. Since 2017, a spec using the keywords cites both RFC 2119 and RFC 8174. The RFC 8174 boilerplate adds the clause "when, and only when, they appear in all capitals."
- **"Stable" in a 0.x spec is contradictory.** Semver 0.x means anything can change, and `RELEASING.md` says the same. If you mark content "Stable," add a disclaimer that stability is intent, not a guarantee, until 1.0.0.
- **Security Considerations is mandatory.** RFC 7322 says it cannot be omitted. Even metadata specs have security implications (trust, provenance, script execution).
- **Rationale kills spec clarity.** "Because X, implementations MUST Y" mixes informative rationale with a normative requirement. Separate them. The normative statement must stand without the "because."
- **Editing a spec moves line numbers.** Any edit above a cited line shifts every `<path>:<line>` citation below it. Grep for citations into the file you edited and fix the ones that moved.
