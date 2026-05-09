#!/usr/bin/env bash
# Slice 3 conformance: package.json moat block schema (field-definition table,
# role-discriminated attestations[] array, worked-example JSON, role-uniqueness
# normative qualifier, canonical payload cite).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
fail=0

if [[ ! -f "$spec" ]]; then
  echo "FAIL [pre]: $spec missing"
  echo "slice-3 conformance: FAIL"
  exit 1
fi

# A1: a section heading "## package.json moat Block (normative)" or similar exists.
if ! grep -qE '^## .*package\.json.*moat.*\(normative' "$spec"; then
  echo "FAIL [A1]: section heading for the package.json moat block (normative) not found"
  fail=1
fi

# A2: field-definition table with the five required rows. The table opens with
# the header line | Field | Required | Description |. Each Required cell must
# carry an RFC 2119 keyword (REQUIRED, OPTIONAL, or a "REQUIRED for X" form).
table_header=$(grep -nE '^\|\s*Field\s*\|\s*Required\s*\|\s*Description\s*\|' "$spec" || true)
if [[ -z "$table_header" ]]; then
  echo "FAIL [A2]: no Field | Required | Description table header found"
  fail=1
fi

# Each row is asserted by a row-text grep that includes the field name and a
# Required keyword in the second column.
required_re='REQUIRED|OPTIONAL'
for row in 'moat\.contentDirectory' 'moat\.attestations\b' 'moat\.attestations\[\]\.role' 'moat\.attestations\[\]\.bundle' 'moat\.attestations\[\]\.rekor_log_index'; do
  if ! grep -nE "^\|.*\`${row}\`.*\|.*(${required_re}).*\|" "$spec" >/dev/null; then
    echo "FAIL [A2]: missing or malformed table row for ${row} (must carry RFC-2119 keyword in the Required column)"
    fail=1
  fi
done

# A3: a fenced ```json block follows the table and contains the role-
# discriminated attestations array with both publisher and registry entries.
json_block=$(awk '/^```json$/{flag=1; next} /^```$/{flag=0} flag' "$spec" || true)
if [[ -z "$json_block" ]]; then
  echo "FAIL [A3]: no fenced \`\`\`json block found"
  fail=1
else
  for needle in '"moat":[[:space:]]*{' '"contentDirectory":' '"attestations":[[:space:]]*\[' '"role":[[:space:]]*"publisher"' '"role":[[:space:]]*"registry"'; do
    if ! echo "$json_block" | grep -qE "$needle"; then
      echo "FAIL [A3]: fenced JSON missing pattern: $needle"
      fail=1
    fi
  done
fi

# A4: canonical attestation payload cited in its exact form.
if ! grep -qE '\{"_version":1,"content_hash":"sha256:[^"]+"\}' "$spec"; then
  echo "FAIL [A4]: canonical payload form {\"_version\":1,\"content_hash\":\"sha256:<hex>\"} not cited"
  fail=1
fi

# A5: bold-label inline normative qualifier for role uniqueness.
ru=$(grep -cE '\*\*Role uniqueness \(normative — MUST\):\*\*' "$spec")
ru=${ru:-0}
if [[ "$ru" -ne 1 ]]; then
  echo "FAIL [A5]: expected exactly 1 '**Role uniqueness (normative — MUST):**' qualifier, found $ru"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "slice-3 conformance: FAIL"
  exit 1
fi
echo "slice-3 conformance: OK"
exit 0
