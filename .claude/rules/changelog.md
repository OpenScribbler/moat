---
description: MOAT changelog conventions — how to write CHANGELOG.md and when spec edits require an [Unreleased] entry
globs: CHANGELOG.md, moat-spec.md, specs/**/*.md
---

# MOAT Changelog Conventions

`CHANGELOG.md` is a public record read by spec consumers — publishers, registry operators, and conforming-client implementers. It documents **what changed** and **what the reader must do about it**. Nothing else belongs here.

## Every spec edit gets a changelog entry

Any change to `moat-spec.md` or a sub-spec under `specs/*.md` made after a release tag MUST be logged in `CHANGELOG.md` in the same commit. Editing spec content without a changelog entry creates silent drift between the tagged release and `main` — the release trail becomes meaningless.

- If there is no `[Unreleased]` section at the top of `CHANGELOG.md`, add one.
- Log the edit under the appropriate Keep-a-Changelog section (`Added`, `Changed`, `Removed`, `Fixed`, `Deprecated`, `Security`).
- State whether the edit is normative or editorial. If editorial, include a phrase like "no normative change" so readers know it's a PATCH-level clarification.
- When the next release is cut, the `[Unreleased]` contents move into the new versioned section per [RELEASING.md](../../RELEASING.md).

This applies even to single-line edits. Version bumping is batched per RELEASING.md's "batch editorial fixes" policy, but `[Unreleased]` tracking is **per-commit**, not batched.

Tooling-only changes (files under `scripts/`, `.github/`, `.gitignore`, `AGENTS.md`, `.claude/`, `ROADMAP.md`) are not spec content and do not need a changelog entry.

## Do not include internal process metadata

The following MUST NOT appear in changelog entries. They have no meaning to readers outside the working group:

- **Panel, review, or persona references.** Examples to avoid: "five-persona panel review", "adversarial review", "reviewer feedback", "agent consensus". If the working process produced the change, that belongs in commit messages and panel notes — not here.
- **Internal finding IDs.** Examples to avoid: `SC-2`, `DQ-5`, `SB-1`, `SC-1`–`SC-7`, any `XX-N` pattern used in panel notes, review scratchpads, or tracking systems.
- **Counts of internal artifacts.** Examples to avoid: "resolved 17 findings", "3 ship-blockers", "7 spec changes", "7 design questions".
- **References to internal documents or pipelines.** Examples to avoid: linking or naming `panel/`, bead IDs, internal working-group threads.

If a reader can't act on the detail without context from an internal thread, cut it.

## External references are welcome

These anchors are meaningful to readers and should be cited where relevant:

- CVE identifiers (e.g., `CVE-2024-23651`)
- External standards and their section numbers (e.g., TUF, in-toto, SLSA, OWASP, RFC 3339)
- Spec file locations and section headings (e.g., `moat-spec.md §Trust Model`, `specs/github/publisher-action.md`)
- Published test vector IDs (e.g., `TV-09`, `TV-MH4`) — these are part of the spec surface, not internal tracking

## Structure

- Use Keep-a-Changelog sections: `Added`, `Changed`, `Removed`, `Fixed`, `Deprecated`, `Security`.
- Open each version with **one paragraph** summarizing what the release delivers and any breaking changes that affect conformers. Do not open with process metadata.
- Each bullet must stand alone. A reader with zero knowledge of internal discussions should understand the change from the bullet text alone.
- Prefer the form **bold-label — explanation**. The label names the thing; the explanation says what changed and why it matters.

## Example

**Don't:**

> Five-persona panel review resolved all 17 findings (3 ship-blockers, 7 spec changes, 7 design questions). Breaking changes: …
>
> - **Version Transition section** (SC-2) — content hash checked before `_version`.
> - **Undiscovered content detection** (SC-4) — Publisher Action MUST warn about content-like directories.

**Do:**

> Breaking release: content type rename, field renames, new required lockfile fields, staleness model redesign.
>
> - **Version Transition section** — content hash is checked before `_version`; 6-month grace period defined for schema version bumps.
> - **Undiscovered content detection** — Publisher Action MUST warn about content-like directories not covered by discovery.

## When editing an existing entry

Before saving any edit to `CHANGELOG.md`, re-read the entry and confirm:

1. No panel/persona/review language.
2. No finding IDs of the form `SC-N`, `DQ-N`, `SB-N`, or similar.
3. No counts of internal artifacts ("N findings", "N ship-blockers").
4. The opening paragraph describes the release, not the process.
