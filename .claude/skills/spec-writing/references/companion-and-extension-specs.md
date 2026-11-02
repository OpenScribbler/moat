# Companion and Extension Specs

Patterns for specifications that extend, companion, or profile another specification. In MOAT, every file under `specs/` is a companion to `moat-spec.md`.

## Terminology

| Pattern | Meaning | Example |
|---------|---------|---------|
| **Extension** | Adds new capabilities to the parent spec | JSON Schema Validation extends JSON Schema Core |
| **Companion** | Provides structured conventions that complement the parent | `specs/npm-distribution.md` companions `moat-spec.md` |
| **Profile** | Defines a subset of the parent for a specific community | W3C accessibility profiles of HTML |
| **Module** | Self-contained unit that can be adopted independently | CSS modules (Flexbox, Grid, etc.) |

## Required Documentation

A companion or extension spec documents the following near the top of the document, in its header lines or a "Relationship to [Parent]" section:

### 1. Dependency direction

Is the parent aware of this spec? Does the parent need to change?

```markdown
This sub-spec is a companion to the MOAT Specification. The core
spec lists it on its Sub-specs line and does not depend on it.
Where this sub-spec narrows or departs from a core rule, it says so
at that rule.
```

### 2. Conformance relationship

Can you conform to this spec without conforming to the parent?

```markdown
A Conforming Client of this sub-spec is also a Conforming Client of
moat-spec.md. This sub-spec adds requirements for npm-distributed
Content Items.
```

A sub-spec that makes an exception to a core requirement states it where the exception applies and names the core rule. `specs/npm-distribution.md` does this for `source_uri`: the core spec requires it on every Registry Manifest entry, and the sub-spec's backfill rule omits it when no upstream Source Repository is known, citing the core rule. Never claim a sub-spec relaxes nothing without checking for such exceptions.

### 3. Version compatibility

Which versions of the parent does this spec work with?

MOAT states this in each sub-spec's header:

```markdown
**Version:** 0.3.0 (Draft)
**Requires:** moat-spec.md ≥ 0.7.1
```

Raise `Requires:` whenever the sub-spec starts relying on a core rule added in a later core version.

### 4. What this spec adds vs. what the parent defines

Be explicit about boundaries:

```markdown
The core spec defines the Content Hash algorithm and the Lockfile.
This sub-spec defines where the Content Hash is computed for an npm
package, what package.json metadata a Publisher embeds, and when a
Conforming Client refuses to materialize a Content Item.
```

## Anti-Patterns

### Redefining parent terms

If the core spec defines "Registry" as a MOAT registry and a sub-spec uses "registry" to mean the npm Registry without qualification, you've created ambiguity. `lexicon.md` settles most of these; where it doesn't, either:
- Use the parent's definition and work within its constraints
- Use a different term for your concept
- Explicitly document the distinction

### Normative dependency on an unstable parent

If the parent spec is 0.x (unstable), your companion has a normative dependency on something that can change at any time. `moat-spec.md` is 0.x, so every MOAT sub-spec carries this risk, and the `Requires:` line plus the `RELEASING.md` pre-1.0 notice are how MOAT documents it. A core change that breaks a sub-spec's assumptions needs that sub-spec revisited in the same release.

### Implicit assumptions about parent behavior

Don't assume the parent spec's behavior without citing it:

```markdown
## Wrong
Clients ignore the unknown package.json field.

## Right
A Conforming Client MUST ignore unknown fields in the moat object
of package.json.
```

If the core spec already has the rule, cite it by `<path>:<line>` (`.claude/rules/spec-citations.md`) instead of restating it.

## Examples from Established Specs

### JSON Schema (companion specs done right)

JSON Schema splits into:
- **Core** — defines the schema language, referencing, vocabularies
- **Validation** — defines validation keywords (type, minimum, pattern, etc.)
- **Hyper-Schema** — defines hypermedia keywords

Each is independently versioned. Each declares its dependency:
> "This document... defines a vocabulary of keywords... which is built upon the core vocabulary defined in JSON Schema Core."

### W3C Modules

CSS uses a modular approach where each module (Flexbox, Grid, Animations) is a self-contained spec that references CSS core concepts. Each module:
- Declares which CSS level it extends
- Defines its own conformance requirements
- Can advance through maturity levels independently
