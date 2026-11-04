# Stability and Versioning

How specs handle maturity levels, version numbers, and stability guarantees.

## Spec Version Numbers

Most community specs use Semantic Versioning for the spec document itself:

| Version | Signal | Meaning |
|---------|--------|---------|
| 0.x.y | Unstable / Draft | Anything may change at any time. No backward-compatibility guarantees. |
| 1.0.0 | First stable release | Public API (or spec surface) is defined and committed to. |
| 1.x.y (minor) | Backward-compatible additions | New fields, new optional features. Nothing breaks. |
| x.0.0 (major) | Breaking changes | Removed fields, changed semantics, incompatible changes. |

**0.1.0 is correct for a draft.** It signals "this is early, expect changes." Move to 1.0.0 when: the spec is implemented in production, you have a surface you're committing to, or you need to promise backward compatibility. MOAT sets its own path: `RELEASING.md` reaches 1.0.0 only through Draft, Release Candidate, and Stable, with the advancement criteria it lists.

## Document-Level Maturity

Most standards bodies use a single maturity label for the entire document:

### IETF Track

| Level | Requirements |
|-------|-------------|
| Proposed Standard | Generally stable, resolved design choices. Implementation experience desirable. |
| Draft Standard | At least 2 independent interoperable implementations. |
| Internet Standard | Significant implementation AND operational experience. |

### W3C Track

| Level | Requirements |
|-------|-------------|
| Working Draft | Under active development. May change significantly. |
| Candidate Recommendation | Stable enough for implementation testing. |
| Recommendation | Final. W3C consensus achieved. |

### Community Specs (Typical)

| Label | Meaning |
|-------|---------|
| Draft | Under development. Breaking changes expected. |
| Release Candidate | Feature-complete. Testing phase. |
| Stable / Released | Committed. Follows semver for changes. |

## Per-Field Stability Levels

Per-field stability is unusual but not unprecedented. **OpenTelemetry** is the best model:

### OpenTelemetry's Approach

Stability applies at the **signal level** (traces, metrics, logs), not individual fields:

| Level | Meaning | Guarantees |
|-------|---------|------------|
| Development | May change at any time | None |
| Stable | Long-term backward-compatibility | Cannot be removed. Semantics frozen. |
| Deprecated | Superseded. Still works. | Must have stable replacement before deprecating. |

Key rules:
- Development content MAY change at any time
- Stable content gets backward-compatibility guarantees
- "Signals MUST NOT be marked as deprecated unless the replacement is stable"
- Development content cannot break stable content

### If You Use Per-Field Stability

If your spec truly needs per-field stability (most don't), you MUST define:

1. **What each level means for implementers**
   ```
   Stable: Semantics will not change in minor versions. Field may be
   removed only in a major version with a deprecation period.

   Draft: May change or be removed in any version. Implementers should
   expect possible breaking changes.
   ```

2. **Promotion criteria**
   ```
   A field advances from Draft to Stable when:
   - Implemented by at least 2 independent agents or tools
   - No breaking changes needed for at least 2 convention releases
   - Community review period of at least 30 days completed
   ```

3. **Backward-compatibility guarantees per level**
   ```
   Stable fields: semantics frozen. Removal requires major version bump
   plus 12-month deprecation notice.

   Draft fields: may change in minor versions. Removal requires release
   notes but no deprecation period.
   ```

4. **Interaction with spec version**

   If the overall spec is 0.x, per-field "Stable" labels are aspirational, not binding:
   ```
   Until this specification reaches 1.0.0, all fields remain subject
   to change regardless of their stability designation. Stability
   levels indicate intended maturity and forward-compatibility intent.
   ```

## Common Mistakes

### "Stable" in a 0.x spec

Semver 0.x means "anything MAY change at any time." Marking fields as "Stable" within a 0.x spec sends contradictory signals. Either:
- Add the disclaimer above (stability = intent, not guarantee, until 1.0)
- Don't use per-field stability until the spec itself is 1.0
- Use different labels that don't imply guarantees (e.g., "Mature" vs "Experimental")

### No promotion criteria

Without criteria, "Draft" becomes permanent. There's no incentive or mechanism to advance fields. Define what must happen for promotion and who decides.

### Draft fields with MUST requirements

This applies to per-field or per-item stability labels only. A document-level stage such as MOAT's `(Draft)` header does not make the document's MUSTs non-binding.

If a field is Draft (meaning it may change), but the spec says "implementations MUST support field X," that creates tension. If the field changes, all implementations must change too — but they were told the field was unstable. Use SHOULD or MAY for Draft fields. Reserve MUST for Stable fields.
