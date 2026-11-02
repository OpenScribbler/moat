# Audit a Specification

Checklist-driven workflow for reviewing `moat-spec.md`, a sub-spec, or one section of either against established norms and MOAT's conventions (see "MOAT conventions that override the generic guidance" in `SKILL.md`).

## How to use

An audit is read-only: it changes no spec file. Collect every finding before recommending fixes, because auditing and fixing are separate phases.

1. **Pick the scope.** A whole document, or one section. `<spec>` below is the file you are auditing, such as `moat-spec.md` or `specs/npm-distribution.md`. For a section, find its line range from the headings:

   ```bash
   awk '/^ *```/{f=!f} !f && /^#/{print NR": "$0}' <spec>
   ```

   The command skips fenced code blocks, whose shell comments also start with `#`. The section runs from its heading to the line before the next heading of the same or higher level.

2. **Read for context.** Read the scope once in full. For a section, also read the document header (version, stage, `Requires:`) and skim the headings around it.

3. **Run the checks.** A whole-document audit runs every check below. A section audit runs checks 2 to 6 and 9 on the section, and runs a check from 1, 7, or 8 only when the section itself carries that content (a section that defines conformance classes gets the conformance row; a sub-spec's header gets check 8). Mark each row pass, fail, or n/a, with a `<path>:<line>` for every fail.

4. **Report** as described at the end.

## 1. Structure check (whole document)

| Check | Pass/Fail | Notes |
|-------|-----------|-------|
| Has an abstract or introduction (self-contained, no citations in the abstract) | | |
| Defined terms match `lexicon.md` and appear before first normative use | | |
| Has a Requirements Language section with RFC 2119/8174 boilerplate | | |
| Has a conformance section defining classes and compliance levels | | |
| Has a Security Considerations section (not hand-waved) | | |
| Every cited external document has a reference entry, normative and informative kept apart | | |
| Sections and appendices are labeled normative or informative | | |
| If a sub-spec: has `Requires:` and `Part of:` header lines | | |

**Reference:** `references/document-structure.md`

## 2. RFC 2119/8174 check

| Check | Pass/Fail | Notes |
|-------|-----------|-------|
| The document's boilerplate cites BOTH RFC 2119 and RFC 8174 | | |
| Boilerplate includes "when, and only when, they appear in all capitals" | | |
| Keywords appear ONLY in ALL CAPS (no lowercase "must" carrying a requirement) | | |
| Keywords appear ONLY in normative content (not in informative blocks or examples) | | |
| Every MUST is justified by interoperability or harm prevention | | |
| Every SHOULD has identifiable legitimate exceptions | | |
| Every MAY has been analyzed for interop (with and without must work together) | | |
| No "wishy-washy SHOULD" (SHOULD used where MUST was intended) | | |
| Each requirement names who it binds (a conformance class from the spec, such as Conforming Client or Registry Operator) | | |

List every keyword in scope, with line numbers, to drive this check:

```bash
sed -n '<start>,<end>p' <spec> | grep -nE '\b(MUST|SHALL|SHOULD|MAY|REQUIRED|RECOMMENDED|OPTIONAL)\b'
```

Add `<start> - 1` to each printed line number to get the line in the file. The spec wraps prose, so read each hit's whole sentence, which can continue onto the next line.

**Reference:** `references/rfc2119-guide.md`

## 3. References and citations check

| Check | Pass/Fail | Notes |
|-------|-----------|-------|
| No paths outside the repo, to unmerged branches, or to working notes such as `panel/` | | |
| Repo-relative links resolve to files that exist | | |
| Normative cross-references cite `<path>:<line>`, and the cited line holds `MUST` or `MUST NOT` (or `SHOULD`, for a citation outside the `## Conformance (normative)` error-code table) | | |
| Every in-text citation of an external document has a reference entry, and every entry is cited | | |
| Normative references point only to stable, published, accessible documents | | |
| No unnamed data sources ("Behavior matrix Q1", etc.) | | |
| Research or survey data is either published or summarized inline | | |

To check a cited line: `sed -n '<line>p' <path>`.

**Reference:** `references/references-and-citations.md`, `.claude/rules/spec-citations.md`

## 4. Normative vs. informative separation

| Check | Pass/Fail | Notes |
|-------|-----------|-------|
| Every section and labeled paragraph is identifiable as normative or informative | | |
| Labels use MOAT's forms: `(normative)` or `(informative)` in headings and paragraph leads, `(normative — MUST)`, `(normative — MUST NOT)`, or `(normative — SHOULD)` in sub-specs; `(Informative)` capitalized is also in use | | |
| No RFC 2119 keywords in content labeled informative | | |
| No "because X, MUST Y" patterns (rationale mixed with requirements) | | |
| No persuasive or marketing language in normative content | | |
| No first-person voice ("we designed...") | | |
| Examples illustrate but do not define (normative text stands alone) | | |
| Implementation mapping tables and rationale sit in labeled `(informative)` blocks in the section they explain | | |

**Reference:** `references/normative-vs-informative.md`

## 5. Self-containment check

| Check | Pass/Fail | Notes |
|-------|-----------|-------|
| Normative content is implementable without informative sections | | |
| Normative content is implementable without chasing unpublished documents | | |
| All terms are defined (in the spec or `lexicon.md`) before first normative use | | |
| No lexicon alias-to-avoid used where the canonical term is meant | | |

## 6. Completeness check

| Check | Pass/Fail | Notes |
|-------|-----------|-------|
| Every optional field has an explicit default stated | | |
| Error handling is specified (missing values, malformed input, unknowns) | | |
| Unknown field and value handling is specified (ignore? error? warn?) | | |
| Edge cases are addressed (empty arrays, missing optional parents, etc.) | | |
| Security implications are analyzed, not hand-waved | | |

## 7. Versioning and stability check (whole document)

| Check | Pass/Fail | Notes |
|-------|-----------|-------|
| Version and stage label match actual maturity | | |
| No "Stable" labels in a 0.x spec without a disclaimer | | |
| No MUST requirements on content a spec labels with a per-field or per-item draft or experimental stability (the document's `(Draft)` stage does not count) | | |
| Every spec edit since the last release tag has a `CHANGELOG.md` entry under `[Unreleased]` | | |

To list spec edits since the last tag, committed and not: `git log --oneline "$(git describe --tags --abbrev=0)"..HEAD -- moat-spec.md 'specs/*.md' 'specs/github/*.md'`, then `git status --short -- moat-spec.md specs/` for uncommitted and untracked spec files. Files under `specs/conformance/` are tooling and need no entry.

**Reference:** `references/stability-and-versioning.md`, `RELEASING.md`

## 8. Sub-spec check

Skip for `moat-spec.md` itself.

| Check | Pass/Fail | Notes |
|-------|-----------|-------|
| `Requires:` names a core version that has every core rule the sub-spec depends on | | |
| Conformance relationship to the core spec is stated | | |
| No core term redefined with a different meaning | | |
| What this sub-spec adds versus what the core spec defines is stated near the top | | |

**Reference:** `references/companion-and-extension-specs.md`

## 9. The extraction test

As a final validation:

1. Extract every sentence in scope containing an RFC 2119 keyword (MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY, OPTIONAL; the `grep` from check 2 finds the lines). Add the normative content that carries no keyword: every rule under a `(normative)` label, such as the list after `Serialization rules (normative):` in `moat-spec.md` §Attestation Payload, and every definition or table a normative section declares, such as the terminal-state table in `moat-spec.md` §Trust State Error Vocabulary.
2. Read them in sequence without surrounding prose.
3. Ask: can a competent implementer build a conformant implementation from ONLY these statements?

If yes, the normative content is self-contained. If no, record a finding for each statement that needs surrounding context, with a suggested fix: make the statement self-sufficient, or promote the context to normative. The audit itself edits nothing.

## Reporting

After completing all checks, list findings by severity:

- **Critical**: breaks fundamental spec norms (missing conformance, broken references, normative/informative confusion)
- **Major**: deviates from conventions in ways that harm clarity or implementability
- **Minor**: polish that improves quality but does not block publication

For each finding, give the `<path>:<line>`, what is wrong, which convention it violates, and a suggested fix. A fix that later edits a spec file needs a `CHANGELOG.md` entry and the matching edit to its website mirror (see `SKILL.md` convention 5), in the same commit.
