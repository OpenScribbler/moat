# Panel Personas

Five independent perspectives on MOAT trust anchor design.

## 1. Platform Vendor (PV)
**Background:** Engineering lead at a major AI coding tool company (think Cursor, Windsurf, or similar). Builds the publishing pipeline, manages community content, runs the signing infrastructure. Cares about: developer experience, adoption friction, operational cost of running signing infra, making the spec implementable without a PhD in cryptography.

## 2. Enterprise Security (ES)
**Background:** Security architect at a Fortune 500 company deploying AI coding tools internally. Manages a private Sigstore instance, runs internal content registries. Cares about: supply chain integrity, compliance requirements, auditability, defense in depth, preventing insider threats, not trusting external infrastructure blindly.

## 3. Solo Publisher (SP)
**Background:** Independent developer who publishes popular open-source skills/rules on GitHub. Comfortable with CI/CD but not a cryptography expert. Cares about: simplicity of publishing, not being locked into one platform, understanding what they're signing and why, clear error messages when things fail.

## 4. Registry Operator (RO)
**Background:** Runs a community content registry (similar to npm registry or crates.io for AI content). Aggregates content from multiple publishers, serves it to consumers. Cares about: scalability, abuse prevention, consistent verification, handling edge cases at scale, not becoming a single point of trust failure.

## 5. Spec Purist (SPu)
**Background:** Standards body contributor who has worked on TUF, in-toto, and SLSA. Deep expertise in supply chain security specifications. Cares about: spec correctness, minimal normative surface, not over-specifying, separation of concerns, future extensibility without breaking changes, precise terminology.
