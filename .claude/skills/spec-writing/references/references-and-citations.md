# References and Citations

How to handle references in technical specifications, based on RFC 7322 and W3C conventions.

## The Two Reference Types

A spec splits its References section into two subsections when both types are present:

### Normative References

Documents that you MUST read to implement the spec. These are hard dependencies.

- If the referenced document changes, it could affect this spec's requirements
- Normative references MUST point to stable, versioned, publicly accessible documents
- Internet-Drafts (I-Ds) can NEVER be normative references — they're unstable by definition
- A normative reference to an unstable document means your spec is built on sand

### Informative References

Documents that provide background, context, or related reading. Helpful but not required.

- You can implement the spec without reading any informative reference
- Research papers, blog posts, surveys, and design rationale docs go here
- Internet-Drafts CAN be informative references (with "Work in Progress" designation)

## Citation Rules

### Every citation must be bidirectional

- Every in-text citation `[RFC2119]` needs a corresponding entry in the References section
- Every entry in the References section needs to be cited somewhere in the text
- No orphans in either direction. Tooling should enforce this.

### Citation format

Each reference entry must include enough information for the reader to locate the document independently:

```
[RFC7322]  Flanagan, H. and S. Ginoza, "RFC Style Guide", RFC 7322,
           DOI 10.17487/RFC7322, September 2014,
           <https://www.rfc-editor.org/info/rfc7322>.

[SEMVER]   Preston-Werner, T., "Semantic Versioning 2.0.0",
           <https://semver.org/spec/v2.0.0.html>.

[OTEL-STABILITY]  OpenTelemetry Authors, "Versioning and stability
           for OpenTelemetry clients",
           <https://opentelemetry.io/docs/specs/otel/versioning-and-stability/>.
```

Required fields: Author/Editor, Title, Date (when available), Stable URL or identifier.

### URIs are supplementary, not sufficient

A bare URL is not a citation. This is wrong:

```
See https://semver.org/ for versioning rules.
```

This is right:

```
Version strings follow Semantic Versioning [SEMVER].

...

[SEMVER]  Preston-Werner, T., "Semantic Versioning 2.0.0",
          <https://semver.org/spec/v2.0.0.html>.
```

## What Is NOT Acceptable as a Reference

### Local file paths

```markdown
See the [Token Efficiency Decision](reference/token-efficiency-metadata-separation.md)
for the full design rationale.
```

This is a broken link for every reader who doesn't have your local repository.

**MOAT exception:** the spec is published as the GitHub repository, so a repo-relative link to a published file in it (`specs/npm-distribution.md`, `lexicon.md`, `reference/moat_hash.py`) resolves for every reader and is acceptable. A normative cross-reference uses the `<path>:<line>` form in `.claude/rules/spec-citations.md`. What stays unacceptable is a path outside the repo, to an unmerged branch, or to working notes that never ship, such as `panel/`.

**Fix options:**
1. **Inline the content** — Summarize the key rationale in 2-4 sentences within the spec
2. **Appendix** — Move the full analysis to an informative appendix
3. **Publish and link** — If it's substantial enough, publish it as a standalone document with a stable URL

### Unnamed internal artifacts

```markdown
**Data source:** Behavior matrix Q1 — discovery depth across 12 agents.
```

"Behavior matrix Q1" is meaningless to readers outside your team. They can't verify, reproduce, or even understand what this references.

**Fix options:**
1. **Summarize inline** — "Based on analysis of 12 agents' discovery mechanisms (conducted March 2026), we found that..."
2. **Publish the data** — Put the behavior matrix in a public repo and cite it formally
3. **Remove the citation** — If the data informed the design but isn't needed to understand the spec, just state the conclusion without citing the source

### Unpublished or unstable documents

- Internal wikis, Google Docs, Notion pages — not stable, not public
- Git branches or PRs — may be deleted or force-pushed
- Slack messages or email threads — ephemeral

If the content matters, publish it somewhere stable before referencing it.

## Citing Research and Survey Data

When spec decisions are informed by research (surveys, competitive analysis, agent behavior testing), the spec should:

1. **State the conclusion** in the normative or informative text
2. **Summarize the methodology** briefly (number of subjects, what was measured, when)
3. **Cite a published analysis** if one exists, OR summarize findings inline if not

### Example: Good

```markdown
### Rationale (Informative)

Analysis of 12 AI coding agents (March 2026) found three distinct
loading architectures: dedicated skill tools (5 agents), standard
file-read mechanisms (1 agent), and implicit injection (6 agents).
The sidecar pattern was chosen because it requires no changes to
agents using file-read architectures — the SKILL.md frontmatter
contains at most one unrecognized field.
```

### Example: Bad

```markdown
**Data source:** Behavior matrix Q1, Q2, Q8 — loading mechanisms,
tool architecture, and activation paths across 12 agents.
```
