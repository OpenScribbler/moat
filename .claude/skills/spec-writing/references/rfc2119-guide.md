# RFC 2119/8174 Usage Guide

Rules for using requirement-level keywords (MUST, SHOULD, MAY, etc.) in technical specifications.

## The Boilerplate

If your spec uses ANY of these keywords, you MUST include this boilerplate verbatim (from RFC 8174):

```
The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all
capitals, as shown here.
```

### Why both RFCs?

- **RFC 2119** (1997) defined the keywords but was ambiguous about case. Some implementers treated lowercase "must" as normative.
- **RFC 8174** (2017) resolved this: ONLY ALL-CAPS versions carry normative meaning. Lowercase "must" and "should" are ordinary English.
- Citing only RFC 2119 is incomplete. Cite both as normative references.

### Citation format

In the References section:

```
## Normative References

[RFC2119]  Bradner, S., "Key words for use in RFCs to Indicate
           Requirement Levels", BCP 14, RFC 2119,
           DOI 10.17487/RFC2119, March 1997,
           <https://www.rfc-editor.org/info/rfc2119>.

[RFC8174]  Leiba, B., "Ambiguity of Uppercase vs Lowercase in
           RFC 2119 Key Words", BCP 14, RFC 8174,
           DOI 10.17487/RFC8174, May 2017,
           <https://www.rfc-editor.org/info/rfc8174>.
```

## Keyword Meanings

| Keyword | Meaning | When to Use |
|---------|---------|-------------|
| **MUST** / REQUIRED / SHALL | Absolute requirement. No exceptions. | Interoperability depends on this. Violating it breaks things. |
| **MUST NOT** / SHALL NOT | Absolute prohibition. | Doing this would break interoperability or cause harm. |
| **SHOULD** / RECOMMENDED | Valid reasons to deviate exist, but implications must be understood first. | Best practice, but exceptions are legitimate and documented. |
| **SHOULD NOT** / NOT RECOMMENDED | Behavior is sometimes acceptable, but understand implications. | Usually wrong, but edge cases exist. |
| **MAY** / OPTIONAL | Truly optional. | Implementations with AND without this feature must interoperate. |

## Usage Rules

### 1. Use sparingly

RFC 2119 says keywords "MUST only be used where it is actually required for interoperation or to limit behavior which has potential for causing harm."

Every MUST in your spec is a burden on implementers. If something is a good idea but not essential for interoperability, use SHOULD. If it's truly optional, use MAY. If it doesn't need a keyword, don't use one.

### 2. Only in normative sections

RFC 2119 keywords MUST NOT appear in:
- Informative appendices
- Examples
- Rationale/motivation text
- Abstracts

If an appendix says "agents SHOULD support X", readers will ask: is that binding? It shouldn't be — appendices labeled "(Informative)" carry no normative weight. But the keyword creates confusion.

### 3. Don't use SHOULD when you mean MUST

The "wishy-washy SHOULD" is the most common spec-writing mistake (per IETF community feedback). If you write SHOULD because you want MUST but feel uncomfortable being that strong, reconsider:

- If interoperability breaks without it → MUST
- If there are legitimate exceptions → SHOULD, and document what exceptions are acceptable
- If you're not sure → you probably haven't analyzed the requirement deeply enough

### 4. Don't use keywords to impose preferences

Wrong: "Implementations MUST use SHA-256 for hashing."
(Unless interoperability actually requires SHA-256 specifically.)

Right: "Implementations MUST use a cryptographic hash function. The algorithm MUST be SHA-256."
(When the spec defines a specific algorithm as part of the format.)

### 5. MAY requires interop analysis

When you write "implementations MAY support X," you're saying: implementations that support X must interoperate with those that don't. If that's not true — if supporting X changes the format or behavior in a way that non-supporting implementations can't handle — then X is not truly optional.

## Common Mistakes

### Normative language in informative content

```markdown
## Appendix A: Implementation Notes (Informative)

Agents SHOULD cache the sidecar file to avoid repeated disk reads.
                                        ← WRONG: keyword in informative section
```

Fix: Use lowercase "should" or rephrase:

```markdown
## Appendix A: Implementation Notes (Informative)

Caching the sidecar file avoids repeated disk reads and is
recommended for performance.
```

### Rationale mixed with requirement

```markdown
Because 7 of 12 agents auto-load skills without approval,
implementations MUST verify script hashes before execution.
```

Fix: Separate the rationale from the requirement:

```markdown
Implementations MUST verify script hashes before execution.

*Rationale (informative):* A survey of agents found that the majority
auto-load skills without user approval, making pre-execution
verification critical.
```

### Hedging in normative text

```markdown
Implementations probably should reject duplicate keys.
```

Fix: Pick a keyword and commit:

```markdown
Implementations SHOULD reject a record with duplicate keys.
```
