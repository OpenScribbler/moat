#!/usr/bin/env bash
# Slice 2 conformance: specs/npm-distribution.md house-style header,
# RFC-2119 heading parentheticals, no algorithm re-implementation,
# revoked_hashes only cited (not redefined).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
fail=0

# A1: file exists.
if [[ ! -f "$spec" ]]; then
  echo "FAIL [A1]: $spec does not exist"
  echo "slice-2 conformance: FAIL"
  exit 1
fi

# A2: house-style metadata header.
header=$(head -9 "$spec")
if ! echo "$header" | grep -qE '^# .+ Specification$'; then
  echo "FAIL [A2]: H1 missing or not ending in 'Specification'"
  fail=1
fi
if ! echo "$header" | grep -qE '^\*\*Version:\*\*'; then
  echo "FAIL [A2]: missing **Version:** line"
  fail=1
fi
if ! echo "$header" | grep -qE '^\*\*Requires:\*\*'; then
  echo "FAIL [A2]: missing **Requires:** line"
  fail=1
fi
if ! echo "$header" | grep -qE '^\*\*Part of:\*\* \[MOAT Specification\]\(\.\./moat-spec\.md\)'; then
  echo "FAIL [A2]: **Part of:** must read '[MOAT Specification](../moat-spec.md)'"
  fail=1
fi
if ! echo "$header" | grep -qE '^>'; then
  echo "FAIL [A2]: missing blockquote one-liner under the metadata"
  fail=1
fi
if ! echo "$header" | grep -qE '^---$'; then
  echo "FAIL [A2]: missing trailing --- separator within first 9 lines"
  fail=1
fi

# A3: every '## ' heading ends in one of the RFC-2119 parentheticals.
# Allowed: (normative), (normative — MUST), (normative — SHOULD), (informative), (optional).
# Exempt: '## Scope' is a closing document-level meta-section (which versions
# of npm distribution this sub-spec covers); it is neither normative nor
# informative to the protocol, so it is exempt from the parenthetical rule.
bad_headings=$(grep -nE '^## ' "$spec" | grep -vE ':## Scope[[:space:]]*$' | grep -vE '\((normative|informative|optional)([^)]*)?\)\s*$' || true)
if [[ -n "$bad_headings" ]]; then
  echo "FAIL [A3]: section headings missing RFC-2119 status parenthetical:"
  echo "$bad_headings"
  fail=1
fi

# A4: algorithm is cited, not redefined. The reference algorithm in
# reference/moat_hash.py uses 'def content_hash', 'rglob', and 'NFC'. The spec
# MUST NOT include any of those literal markers.
algo=$(grep -nE 'def content_hash|rglob|NFC' "$spec" || true)
if [[ -n "$algo" ]]; then
  echo "FAIL [A4]: algorithm appears to be re-implemented in the spec:"
  echo "$algo"
  fail=1
fi

# A5: revoked_hashes mentions are references — not field-definition table rows.
# A field-definition row matches a 3-column table with REQUIRED/OPTIONAL in the
# Required column. Anything else is a reference.
defs=$(grep -nE '^\s*\|.*\b(revoked_hashes)\b.*\|\s*(REQUIRED|OPTIONAL)' "$spec" || true)
if [[ -n "$defs" ]]; then
  echo "FAIL [A5]: revoked_hashes appears to be defined (table row), not just referenced:"
  echo "$defs"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "slice-2 conformance: FAIL"
  exit 1
fi
echo "slice-2 conformance: OK"
exit 0
