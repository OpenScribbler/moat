# Normative vs. Informative Content

How to separate binding requirements from explanatory material in a specification.

## The Core Principle

**Normative content** defines what implementations MUST, SHOULD, or MAY do. It is binding. An implementer should be able to extract every normative statement into a conformance checklist.

**Informative content** explains WHY decisions were made, provides background, gives examples, and offers implementation guidance. It is not binding. Removing all informative content should not change what an implementation must do.

## How to Mark Content

### Section-level marking

Label sections explicitly in headings:

```markdown
## 3. Trigger Fields

...normative requirements...

## Appendix A: Trigger Field Mapping (Informative)

...mapping tables, implementation notes...
```

### Inline marking

For rationale within a normative section, use a clear marker. The examples below describe a generic record format; MOAT's own hashing rules are in `moat-spec.md` §Content Hashing.

```markdown
Implementations MUST normalize line endings to LF before computing
a record's checksum.

> **Rationale (informative):** Different platforms use different line
> endings (CRLF on Windows, LF on Unix). Without normalization,
> identical content produces different hashes depending on checkout
> settings.
```

Or use a simple label:

```markdown
Implementations MUST normalize line endings to LF before computing
a record's checksum.

*Note (informative):* This ensures identical hashes across platforms
regardless of git `core.autocrlf` settings.
```

### MOAT's forms

MOAT labels content inline rather than with appendices. Use the forms the spec already uses:

```markdown
### Registry Index Format (normative)

**Signature scheme (normative).** An Author-Key signature is ...

**No separate revocation endpoint (informative):** MOAT does not define ...
```

Sub-specs also put the keyword in the label, as in `**Hash input domain (normative — MUST):**`.

### What W3C says

> "It is important that informative (non-normative) material is
> clearly distinguished from normative material."
> — W3C Manual of Style

> "Avoid language that sounds normative in an informative section.
> It might lead the readers to wrong assumptions."
> — W3C QA Framework

## Rules

### 1. No RFC 2119 keywords in informative sections

If a section, appendix, or paragraph is labeled informative, it contains no MUST, SHOULD, MAY, or other RFC 2119 keyword in uppercase. These keywords carry normative weight by definition — using them in informative content creates a contradiction.

Use lowercase or rephrase:

| Instead of | Write |
|------------|-------|
| "Agents SHOULD cache..." (in informative appendix) | "Caching is recommended..." |
| "Registries MUST validate..." (in informative note) | "Registries are expected to validate..." |

### 2. Rationale does not belong inline with requirements

**Wrong:**

```markdown
Because 7 of 12 agents auto-load skills without approval, and skills
can contain executable scripts that could be activated without user
awareness, implementations MUST verify script_hashes before execution.
```

The "because" clause is informative motivation. The MUST is a normative requirement. Mixing them creates several problems:

- Implementers may think the requirement only applies in the stated scenario
- The rationale may become outdated while the requirement remains valid
- It's harder to extract requirements into a conformance checklist

**Right:**

```markdown
Implementations MUST verify script_hashes entries against actual file
hashes before executing any script within a skill directory.

> **Rationale (informative):** Multiple agents auto-load skills from
> cloned repositories without user consent. Script hash verification
> provides a building block for trust chains even on agents that
> currently lack approval mechanisms.
```

### 3. Examples illustrate, they do not define

Per RFC 2360: "Explanatory text must not rely on examples to explain the protocol."

If a behavior is only shown in an example but not stated in normative text, it is not part of the spec. Examples are always informative — they help readers understand, but the normative text must stand on its own.

**Wrong:** An example shows `version: "4.2.0"` but the normative text never states that versions must be semver strings without a leading `v`.

**Right:** Normative text says "Value is a Semver string. MUST NOT start with `v`." The example then illustrates: `version: "4.2.0"`.

### 4. Implementation mapping tables are informative

Tables that map spec fields to native agent mechanisms (e.g., "Convention Field X → Claude Code's Y, Cursor's Z") are implementation guidance, not requirements. In MOAT they sit in the section they map, under an `(informative)` label, such as `**Mapping to common npm-client architectures (informative):**` in `specs/npm-distribution.md`.

If these tables contain SHOULD or MUST language, that language is not binding. But readers may not realize that — so don't use RFC 2119 keywords in them.

## The Extraction Test

A well-structured spec passes this test:

1. Extract every sentence containing an RFC 2119 keyword (REQUIRED, SHALL, and RECOMMENDED included), plus normative content with no keyword: rules under a `(normative)` label and the definitions or tables a normative section declares
2. Read them in order, without surrounding prose
3. Can you build a conformant implementation from just these statements?

If yes — the normative content is properly separated. If no — informative context is load-bearing and needs to be either promoted to normative or the normative statement needs to be self-sufficient.
