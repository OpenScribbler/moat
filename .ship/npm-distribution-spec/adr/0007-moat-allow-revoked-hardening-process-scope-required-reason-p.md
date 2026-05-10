# 0007. MOAT_ALLOW_REVOKED hardening — Process-scope + REQUIRED reason + per-entry RFC 3339 expiry vs Round 1 minimal form

Date: 2026-05-09
Status: Accepted
Feature: npm-distribution-spec

## Context

The Round 1 form passes the "operator can override at all" bar but fails three of the four MOAT design tests. Works-fine-without-it (`CLAUDE.md:125`): an operator who sets the env var and forgets to record why has overridden a security boundary with no auditable record — the operation works fine without the reason, so the reason gets skipped. Enforcement (`CLAUDE.md:127`): "trust that people will write good operational logs" is exactly the answer the test forbids — the protocol provides no mechanism to detect or enforce a reason being recorded. Day-one (`CLAUDE.md:121`): the Round 1 form has no expiry, which means an override set during incident response persists across process restarts and across the eventual revocation-was-a-mistake retraction — the override outlives its purpose. The chosen form fixes all three: process-scope (no hot-reload, the override is a deliberate single action), REQUIRED reason co-variable with hard-fail enforcement (the protocol refuses to honor the override without the reason — "works fine without it" no longer applies), per-entry expiry (the override has a built-in retraction time). The lockfile-only alternative was rejected in Round 1 (high-friction for legitimate incident-response use); Round 2 doesn't revisit that decision. The structured-logging requirement is what makes the override auditable: a downstream operator reviewing logs after the incident can reconstruct exactly which hash was overridden, by whom (via the reason string), when, and until when (via the expiry).

## Decision

Chose **Process-scope, REQUIRED `MOAT_ALLOW_REVOKED_REASON` co-variable, per-entry encoded as `<sha256-hex>:<RFC3339-timestamp>`, structured override-applied logging (C-3)** over **Round 1 minimal form (simple comma-separated hash list, optional reason in operational logs, no expiry); Lockfile-only override (no env-var, hand-edit a `revocation_overrides[]` field — Round 1 design.md option D)**.

## Consequences

A Conforming Client that reads `MOAT_ALLOW_REVOKED` MUST also read `MOAT_ALLOW_REVOKED_REASON`; if the reason is unset or empty, the Conforming Client MUST emit a structured error and refuse to honor the override. A Conforming Client that re-reads either variable mid-process is non-conformant — the read-once discipline is what makes the override a single auditable action. Each override entry MUST be of the form `<sha256-hex>:<RFC3339-timestamp>`; entries without the timestamp delimiter MUST be ignored as malformed (no permanent overrides — the spec forbids them by syntax). A Conforming Client past an entry's RFC 3339 timestamp MUST treat the entry as if absent (no warning, no log — silent expiry). When an override is applied (the Conforming Client proceeds to materialize a hash that appeared in `revoked_hashes`), the Conforming Client MUST log a structured event whose fields include: the package identity (npm package name + version), the matched canonical Content Hash, the operator-supplied reason string, and the entry's expiry timestamp. The override-applied event is a normative log shape — implementers MUST produce it on every override application; it is the audit anchor.
