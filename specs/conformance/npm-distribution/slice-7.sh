#!/usr/bin/env bash
# Slice 7 conformance: MOAT_ALLOW_REVOKED Operator Override hardening.
#
# The Round 2 expansion of `## MOAT_ALLOW_REVOKED Operator Override (normative)`
# in `specs/npm-distribution.md` carries four normative MUSTs (process-scope
# read-once, REQUIRED MOAT_ALLOW_REVOKED_REASON co-variable with hard-fail
# enforcement, per-entry <sha256-hex>:<RFC3339-timestamp> encoding, structured
# override-applied event), names the four log-event field names from
# design.md Question 1 (`package`, `content_hash`, `reason`, `expires_at`),
# and states the expired-as-absent and malformed-rejected rules.
#
# This script greps the spec body and asserts the website mirror is
# byte-identical to the canonical spec after stripping Starlight front-matter.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
mirror=website/src/content/docs/spec/npm-distribution.md
fail=0

if [[ ! -f "$spec" ]]; then
  echo "FAIL [pre]: $spec missing"
  echo "slice-7 conformance: FAIL"
  exit 1
fi
if [[ ! -f "$mirror" ]]; then
  echo "FAIL [pre]: $mirror missing"
  echo "slice-7 conformance: FAIL"
  exit 1
fi

# Extract the override section by flag-toggle range:
#   start: a heading whose text mentions MOAT_ALLOW_REVOKED and the
#          (normative) qualifier
#   end:   the next "^## " heading (the next sibling section)
section="$(awk '/^## .*MOAT_ALLOW_REVOKED.*normative/{flag=1; next} flag && /^## /{flag=0} flag' "$spec" || true)"

if [[ -z "$section" ]]; then
  echo "FAIL [pre]: no '## MOAT_ALLOW_REVOKED ... (normative ...)' section heading found"
  echo "slice-7 conformance: FAIL"
  exit 1
fi

assert_in_section() {
  local description="$1"
  local pattern="$2"
  if echo "$section" | grep -qE "$pattern"; then
    echo "OK  $description"
  else
    echo "FAIL  $description (pattern: $pattern)"
    fail=1
  fi
}

# A1 — process-scope read-once MUST.
assert_in_section "process-scope read-once MUST is named" \
  '(read[[:space:]]+once|process[ -]scope[d]?[[:space:]]+(only|read))'
assert_in_section "section uses RFC-2119 keyword for the process-scope rule" \
  '(MUST|MUST NOT)[^A-Za-z]+.*(re-?read|re-?evaluate|process[ -]scope|read[[:space:]]+once)|(read[[:space:]]+once|process[ -]scope[d]?).*(MUST|MUST NOT)'

# A2 — REQUIRED MOAT_ALLOW_REVOKED_REASON co-variable + hard-fail enforcement.
assert_in_section "MOAT_ALLOW_REVOKED_REASON named as REQUIRED co-variable" \
  'MOAT_ALLOW_REVOKED_REASON.*REQUIRED|REQUIRED.*MOAT_ALLOW_REVOKED_REASON'
assert_in_section "hard-fail enforcement when REASON is missing or empty" \
  '(MUST[[:space:]]+(refuse|fail|reject)|fail[[:space:]]+with[[:space:]]+a[[:space:]]+structured[[:space:]]+error|refuse[[:space:]]+to[[:space:]]+honor)'

# A3 — per-entry encoding <sha256-hex>:<RFC3339-timestamp>.
assert_in_section "per-entry encoding uses <sha256-hex>:<RFC3339-timestamp>" \
  '<sha256-hex>:<RFC3339-timestamp>|sha256-hex.*RFC[[:space:]]?3339|RFC[[:space:]]?3339.*timestamp'
assert_in_section "expiry encoding cites RFC 3339" \
  'RFC[[:space:]]?3339'

# A4 — structured override-applied event.
assert_in_section "section names a structured override-applied event" \
  'structured.*(override[- ]applied|override[ -]event)|override[- ]applied.*structured'

# A5 — field names from design.md Question 1: package, content_hash, reason, expires_at.
assert_in_section "log event names field 'package'" '\bpackage\b'
assert_in_section "log event names field 'content_hash'" 'content_hash'
assert_in_section "log event names field 'reason'" '\breason\b'
assert_in_section "log event names field 'expires_at'" 'expires_at'

# A6 — expired entries treated as if absent (no warning, no log).
assert_in_section "expired entries treated as if absent" \
  '(treated[[:space:]]+as[[:space:]]+if[[:space:]]+absent|ignored[[:space:]]+as[[:space:]]+if[[:space:]]+absent|past[[:space:]]+(its|their)[[:space:]]+(RFC[[:space:]]?3339[[:space:]]+)?(expiry[[:space:]]+)?timestamp)'
assert_in_section "expired-entry rule states no warning and no log" \
  '(no[[:space:]]+warning.*no[[:space:]]+log|no[[:space:]]+log.*no[[:space:]]+warning|silently[[:space:]]+ignored)'

# A7 — malformed entries (missing timestamp delimiter) MUST be ignored as malformed.
assert_in_section "malformed entries (missing timestamp delimiter) MUST be ignored" \
  '(without[[:space:]]+the[[:space:]]+timestamp[[:space:]]+delimiter|missing[[:space:]]+the[[:space:]]+timestamp[[:space:]]+delimiter|no[[:space:]]+timestamp[[:space:]]+delimiter|malformed).*MUST[[:space:]]+(be[[:space:]]+)?(ignored|rejected)'

# A8 — mirror byte-identity.
diff <(sed '1,/^---$/d' "$mirror") "$spec" >/tmp/slice-7-mirror-diff.txt
diff_exit=$?
if [[ "$diff_exit" -eq 0 ]]; then
  echo "OK  website mirror byte-identical to spec body after stripping front-matter"
else
  echo "FAIL  website mirror diverges from spec (see /tmp/slice-7-mirror-diff.txt)"
  fail=1
fi

if [[ "$fail" -eq 0 ]]; then
  echo "slice-7 conformance: OK"
  exit 0
else
  echo "slice-7 conformance: FAIL"
  exit 1
fi
