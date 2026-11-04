# Source Standards

Authoritative references for spec-writing conventions. Read these when you need the primary source, not a summary.

## IETF / RFC

| Document | Title | URL | Use For |
|----------|-------|-----|---------|
| RFC 7322 | RFC Style Guide | https://www.rfc-editor.org/rfc/rfc7322 | Document structure, section ordering, editorial conventions |
| RFC 2119 | Key words for use in RFCs to Indicate Requirement Levels | https://www.rfc-editor.org/rfc/rfc2119 | MUST/SHOULD/MAY keyword definitions |
| RFC 8174 | Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words | https://www.rfc-editor.org/rfc/rfc8174 | Updated boilerplate, uppercase-only rule |
| RFC 2360 | Guide for Internet Standards Writers | https://datatracker.ietf.org/doc/html/rfc2360 | Completeness, error handling, design rationale norms |
| RFC 2026 | The Internet Standards Process — Revision 3 | https://www.rfc-editor.org/rfc/rfc2026 | Maturity levels (Proposed, Draft, Internet Standard) |

### Key IETF Community Resources

| Resource | URL | Use For |
|----------|-----|---------|
| IETF Blog: How to Read an RFC | https://www.ietf.org/blog/how-read-rfc/ | Understanding RFC structure from a reader's perspective |
| RFC Readability (IAB Wiki) | https://wiki.ietf.org/group/iab/RFC_Readability | Common readability problems and fixes |

## W3C

| Document | URL | Use For |
|----------|-----|---------|
| W3C Manual of Style | https://www.w3.org/Guide/manual-of-style/ | Editorial conventions, normative/informative marking, RFC 2119 in W3C context |
| QA Framework: Specification Guidelines | https://www.w3.org/TR/qaframe-spec/ | Conformance clauses, testability, variability |
| Variability in Specifications | https://www.w3.org/TR/spec-variability/ | Profiles, modules, extension points, companion spec patterns |
| W3C Process Document | https://www.w3.org/policies/process/ | Maturity levels (Working Draft, Candidate Rec, Recommendation) |

## Community Specifications (Examples of Well-Written Specs)

| Specification | URL | Notable For |
|---------------|-----|-------------|
| Semantic Versioning 2.0.0 | https://semver.org/ | Concise numbered rules, FAQ section, RFC 2119 usage |
| OpenAPI Specification 3.1 | https://spec.openapis.org/oas/v3.1.1.html | Definitions section, security considerations, appendices |
| JSON Schema (2020-12) | https://json-schema.org/draft/2020-12/json-schema-core | Vocabulary architecture, modular companion specs |
| CommonMark Spec | https://spec.commonmark.org/ | Exhaustive examples, formal grammar, edge case coverage |
| OpenTelemetry Versioning & Stability | https://opentelemetry.io/docs/specs/otel/versioning-and-stability/ | Per-signal stability levels, promotion criteria, backward-compat guarantees |

## When to Consult Each

| Question | Read |
|----------|------|
| "What sections does a spec need?" | RFC 7322, W3C Manual of Style |
| "How do I use MUST/SHOULD/MAY correctly?" | RFC 2119, RFC 8174 |
| "How do I handle references?" | RFC 7322 (normative vs informative split) |
| "How do I write a companion/extension spec?" | W3C Variability in Specifications |
| "How do I handle stability levels?" | OpenTelemetry Versioning & Stability |
| "How do I write a conformance clause?" | W3C QA Framework |
| "What are common spec-writing mistakes?" | RFC 2360, RFC Readability wiki |
| "How should I version my spec?" | Semver 2.0.0 |
