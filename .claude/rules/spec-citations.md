# MOAT Spec Citation Conventions

Normative claims in MOAT specs are anchored on `<path>:<line>` citations. This is the citation form the public `## Conformance (normative)` error-code table in `specs/npm-distribution.md` uses to route a refusal back to the section of the spec that defines the rule.

## The citation form

Use `<path>:<line>` where `<path>` is a repo-relative path to a spec file and `<line>` is the line number of the normative sentence the citation anchors on.

Canonical example: `specs/npm-distribution.md:117` — the line where §Publisher Verification states the single normative Rekor query MUST.

Cross-spec citations follow the same form: `moat-spec.md:790`, `specs/github/publisher-action.md:42`.

## Where citations live

- **`## Conformance (normative)` table** — every `NPM-<SECTION>-<NN>` error code in the table at `specs/npm-distribution.md` carries a `specs/npm-distribution.md:<line>` citation in its third column. The cited line MUST contain a `MUST` or `MUST NOT` token. The conformance slice script (`specs/conformance/npm-distribution/slice-8-error-codes.sh`) verifies this on every CI run.
- **ADR Context paragraphs** — when an ADR's reasoning depends on a specific normative sentence from a sub-spec, cite the path:line so a future reader can find the sentence under spec evolution. Examples in `docs/adr/0010-*.md` and `docs/adr/0011-*.md`.
- **Cross-spec references in spec body text** — when one sub-spec references a normative rule from another sub-spec or from `moat-spec.md`, prefer `<path>:<line>` over heading-only references; line numbers are unambiguous, heading text drifts.

## Keeping citations current

Line numbers shift when a spec is edited. Two mitigations:

1. **Cite the closest `MUST` line, not the heading.** If the normative sentence moves by one line, only the citation moves by one line — not by the size of the prose block above it.
2. **CI catches stale citations.** The `slice-8-error-codes.sh` script reads each citation, runs `sed -n "${line}p"` against the cited path, and fails if the line does not contain `MUST` or `MUST NOT`. A citation that points at a non-normative line (a heading, an example, editorial prose) is the signal that a spec edit shifted the anchor; fix the citation in the same commit as the edit.

## Why this form

The `<path>:<line>` form is what a Conforming Client emits when it refuses to materialize a Content Item. A user looking at the refusal in a terminal can click or paste the citation into their editor and land on the exact sentence that defines the rule. Heading-only citations (`§Publisher Verification`) require the user to know which version of the spec they're reading and to search inside the section for the actual MUST; line citations don't.

The form is also machine-grep-able: `grep -oE 'specs/[a-z-]+\.md:[0-9]+'` finds every citation in the repo, which is what the conformance slice script uses to enforce the convention.

## When NOT to use line citations

Two cases where heading-only references are still acceptable:

- **Informative cross-references** between non-normative sections (e.g., "see the Influences section in `moat-spec.md`"). These survive spec evolution better than line numbers because the heading text is stable.
- **Linking to external documents** (CVEs, TUF sections, SLSA levels). Use the external document's native reference form; the `<path>:<line>` convention is internal to this repo.

For everything normative inside the MOAT repo, use `<path>:<line>`.
