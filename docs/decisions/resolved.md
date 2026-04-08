# Resolved Design Decisions

These issues were opened during the pre-spec design phase and are now resolved.
Preserved here as institutional memory — these questions will re-emerge and the
reasoning behind the decisions should not have to be reconstructed.

---

## Decision 1: Version semantics

**Resolution:** Content hash is the normative identifier. Version is an optional,
non-normative display label (OCI model). Registries and publishers populate it however
they want (semver, date strings, or omit entirely). Clients determine freshness by
comparing content hashes first, then `attested_at` timestamps — never by version label.

"Update available" logic: different hash + later `attested_at` = update; same hash +
later `attested_at` = re-attestation, not an update. Spec must spell this out in the
client verification section.

---

## Decision 2: `name` field constraints

**Resolution:** Two-layer naming model.

- `name` — REQUIRED. ASCII machine identifier. Regex: `[a-z0-9][a-z0-9-]*[a-z0-9]`.
  128-character MUST limit. Immutable once published. Protocol plumbing — not user-facing.
- `display_name` — OPTIONAL. UTF-8 string for human presentation. Mutable. No format
  constraints beyond valid UTF-8. Clients SHOULD prefer `display_name` in user-facing
  contexts when present.

`name` is the protocol identifier (machines use this). `display_name` is the presentation
label (humans see this). Content without `display_name` falls back to `name` for display.

---

## Decision 3: CRLF normalization

**Resolution (panel reviewed):**

Architecture: hash raw bytes, normalize at registry ingestion boundary (Go model). Spec
frames hash input as "canonical byte sequence."

- **Text detection:** Extension-based allowlist, normative, spec-versioned.
  Case-insensitive. Match final extension only. NUL-byte guard: if first 8 KB contain
  `\x00`, treat as binary regardless of extension.
- **Normalization:** Single left-to-right pass, greedy CRLF matching. Streaming.
  `\r\n` → `\n`, lone `\r` → `\n`. `\r\r\n` → `\n\n`.
- **BOM handling:** Strip UTF-8 BOM (EF BB BF) from text files.
- **Extensionless files:** Binary by default. Dotfiles with no second dot are extensionless.
- **VCS directories:** Excluded (`.git`, `.svn`, `.hg`, `.bzr`, `_darcs`, `.fossil`).
- **`moat-attestation.json`:** Excluded from content hashing (circular dependency).
- **Symlinks:** Reject at ingestion.

Defined by normative reference implementation (`moat_hash.py`), not pseudocode.
Conformance test suite ships with spec as a first-class artifact.

---

## Decision 4 (renumbered): `scan_status` structure

**Resolution:** REQUIRED in manifest schema; `result: "not_scanned"` is a valid value.
Every entry is parseable. Registries that don't scan must say so explicitly.

```json
{
  "scan_status": {
    "result": "clean" | "findings" | "not_scanned",
    "scanner": [{ "name": "semgrep", "version": "1.89.0" }],
    "scanned_at": "2026-04-05T12:00:00Z",
    "findings_url": "https://..."
  }
}
```

- `scanner` is a structured array (not a free-form string).
- `scanner` and `scanned_at` required when `result` is `clean` or `findings`; omitted
  when `not_scanned`.
- `findings_url` optional; only when `result: "findings"` and a public report exists.
- No normative staleness threshold in v1. `scanned_at` is RFC 3339.
- Scanner names are an open list — no central registry.

---

## Decision 5 (renumbered): `risk_tier` structure

**Resolution:** REQUIRED in manifest schema; `not_analyzed` is a valid value.
Registry-assigned, never publisher self-declared. Advisory by default.

| Tier | Observable capability |
|---|---|
| `L0` | Read-only. No shell, filesystem writes, or network. |
| `L1` | Reads user files or config outside content dir. No writes, shell, or network. |
| `L2` | Writes files outside content dir, OR makes network requests. No shell, no credential access. |
| `L3` | Invokes a shell, executes arbitrary commands, or reads/writes credentials. |
| `not_analyzed` | Registry did not attempt analysis. |
| `indeterminate` | Ran analysis; could not classify conclusively. |

Key rules: ties resolve upward; `not_analyzed` ≠ `indeterminate`; unknown tier strings
from future spec versions MUST be treated as `not_analyzed`; rubric is about capability
granted, not strings present.

---

## Decision 6 (renumbered): Revocation mechanism

**Resolution:** `revocations` array REQUIRED in manifest (empty array if none).
Optional `revocation_feed_url` for low-latency revocation.

Reason values (normative): `malicious`, `compromised`, `deprecated`, `policy_violation`.

Client behavior: MUST block install for `malicious`/`compromised`; SHOULD warn for
`deprecated`/`policy_violation`. MUST NOT use cached manifest older than configurable
threshold (default: 24h) for revocation checks. MUST NOT autonomously uninstall.
Re-install of `malicious`/`compromised` hash MUST be blocked with no override path.

Cross-registry: clients SHOULD check all trusted registries' revocations against all
installed content hashes. Registry A revoking hash X warns users who installed from
Registry B — attributed to its source, additive not transitive.

Publisher-side: warnings not hard blocks. Registry is gating authority for hard blocks.

Unknown future reason codes collapse to `policy_violation` (least-alarming safe default).
