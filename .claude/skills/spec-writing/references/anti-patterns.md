# Spec Writing Anti-Patterns

Categorized mistakes found in technical specifications, drawn from RFC 2360, W3C QA Framework, IETF community guidance, and direct audit experience.

## Structural

### Missing Security Considerations

RFC 2360: "It is no longer acceptable that Security Considerations sections consist solely of statements to the effect that security was not considered."

Every spec has security implications. Metadata specs deal with trust, provenance, and potentially executable content. Protocol specs have authentication, authorization, and data integrity. Even format specs have parsing vulnerabilities.

If you think your spec has no security implications, you haven't thought hard enough.

### Missing Conformance Clause

Without a conformance clause, "MUST" is ambiguous — who must? An agent? A registry? A skill author? A distribution tool? Define conformance classes explicitly.

### Missing Error Handling

RFC 2360: Implementations diverge most when specs don't detail responses to out-of-spec input, resource exhaustion, or edge cases.

For every field, ask: what happens when the value is missing? Malformed? An unknown enum value? Too long? The spec should say.

### No References Section

Every cited document needs a formal reference entry. Every reference entry needs an in-text citation. No orphans either way. Split into Normative and Informative subsections.

## Language

### The Wishy-Washy SHOULD

The most common RFC keyword mistake. Authors write SHOULD when they mean MUST because they're uncomfortable with the strength of MUST. This creates ambiguity — is there a real reason to deviate, or is the author just hedging?

If you write SHOULD, document what legitimate exceptions exist. If you can't think of any, it's a MUST.

### Overusing Keywords

Not every sentence needs a keyword. "The sky MUST be blue" adds nothing. Use keywords only for interoperability requirements or harm prevention. Conversational requirements can use plain English.

### Multiple Descriptions of the Same Thing

If a behavior is described in two places with slightly different wording, implementers pick the version they prefer. If multiple descriptions exist, identify one as authoritative and have the other cite it.

### Machine-Readable Syntax as Sole Spec

ABNF, JSON Schema, YAML schema — these supplement prose, they don't replace it. The prose is the spec. The formal grammar is a tool for verification.

## Completeness

### Missing Defaults

Every optional field needs an explicit default. "If absent, the implementation may choose" is a divergence factory. State the default.

### Examples Without Normative Backing

If a behavior is shown in an example but not stated in normative text, it's not part of the spec. Examples illustrate — they don't define.

### Missing Design Rationale

RFC 2360: Without explaining WHY a mechanism exists, implementers take shortcuts when the mechanism seems unnecessarily complex. But rationale must be clearly separated from requirements (see `normative-vs-informative.md`).

## References

### Local File Path References

```markdown
See [Token Efficiency Decision](reference/foo.md)
```

Readers outside your repository get a dead link. Every reference must be to a published, accessible document or inlined into the spec. In MOAT, a link to a published file in the repo is fine; a link to working notes such as `panel/`, an unmerged branch, or anything outside the repo is not (see `references-and-citations.md`).

### Unnamed Data Sources

```markdown
Data source: Behavior matrix Q1
```

Unverifiable. Either publish the data, summarize findings inline, or remove the citation.

### Orphaned References

A reference entry that's never cited in the text, or an in-text citation with no reference entry. Both are errors.

## Tone

### Persuasive Language in Normative Sections

```markdown
This elegant approach enables a vibrant ecosystem...
```

Specs state requirements. They do not sell approaches. Marketing language undermines credibility.

### First Person

```markdown
We designed this field to address...
```

Specs don't have a narrator. Use passive or third-person: "This field addresses..."

### Justification Embedded in Requirements

```markdown
Because research shows X, implementations MUST do Y.
```

The "because" is informative. The MUST is normative. Separating them prevents readers from thinking the requirement only applies in the stated scenario.

## Stability

### "Stable" Fields in 0.x Spec

Contradictory signals. Semver 0.x = anything can change. "Stable" = won't change. Pick one or add a disclaimer.

### No Promotion Criteria

If fields have stability levels but no defined path from Draft to Stable, "Draft" becomes permanent. Define what must happen for promotion.

### Draft Fields with MUST Requirements

If a field carries a Draft stability label (it can change), requiring implementations to support it (MUST) creates tension. Use SHOULD or MAY for such fields. This is about per-field labels; a document whose header stage is `(Draft)`, as every MOAT spec is today, still has binding MUSTs.

## The Audit Shortcut

For a quick audit, run these checks in order:

1. **Structure**: Abstract? Terminology? Conformance? Security? References (split)?
2. **Boilerplate**: RFC 2119+8174 cited? Correct boilerplate text?
3. **Self-containment**: Any paths outside the published repo? Any unnamed sources? Any dead links? Any `<path>:<line>` citation off its normative line (MUST, MUST NOT, or SHOULD outside the error-code table)?
4. **Separation**: Any RFC 2119 keywords in informative sections? Any "because X, MUST Y" patterns?
5. **Defaults**: Every optional field has a stated default?
6. **Versioning**: Version matches maturity? Stability labels consistent with version?
