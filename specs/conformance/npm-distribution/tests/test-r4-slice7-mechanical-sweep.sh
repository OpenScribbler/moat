#!/usr/bin/env bash
# Slice-7 acceptance test for npm-distribution-spec-r4.
#
# Asserts that the mechanical-drift sweep covers F2-F5, F11, F14, and the
# A2 row-count confirmation. Per-finding mapping:
#   7.1 (F2)  No 'seven-step' tokens in specs/npm-distribution.md or CHANGELOG.md.
#   7.2 (F11) No 'lines 766' brittle-range citations in specs/npm-distribution.md.
#   7.3 (F4)  docs/adr/0013-...md carries no '88–98' or '117–122' range
#             citations; both refs are single-line anchors.
#   7.4 (F3)  CHANGELOG.md tarballContentRoot rename bullet states REQUIRED
#             and does NOT say 'now OPTIONAL'.
#   7.5 (F5)  specs/npm-distribution.md carries a snake_case editorial note
#             (at least one mention of 'snake_case' in the schema area).
#   7.6 (F14) CHANGELOG.md structured-log narrative uses the 'source in
#             addition to reason code' phrasing (no 'instead of reason code').
#   7.7 (A2)  slice-8-error-codes.sh reports ≥ 30 data rows in §Conformance.
#
# Exits 0 when every assertion passes; non-zero on the first failure.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SPEC="$REPO_ROOT/specs/npm-distribution.md"
CHANGELOG="$REPO_ROOT/CHANGELOG.md"
ADR="$REPO_ROOT/docs/adr/0013-where-the-new-distribution-uri-field-lives-in-the-package-js.md"
SLICE8="$REPO_ROOT/specs/conformance/npm-distribution/slice-8-error-codes.sh"

fail=0

# 7.1 (F2) — 'seven-step' eliminated.
hits_seven=$(grep -nE 'seven-step' "$SPEC" "$CHANGELOG" 2>/dev/null || true)
if [[ -z "$hits_seven" ]]; then
  echo "OK   [slice-7.1] no 'seven-step' tokens in spec or CHANGELOG"
else
  echo "FAIL [slice-7.1]: 'seven-step' still present:"
  echo "$hits_seven" | sed 's/^/  /'
  fail=1
fi

# 7.2 (F11) — brittle 'lines 766–807' range citation replaced with a
# single-line moat-spec.md anchor.
hits_range_766=$(grep -nE 'lines 766' "$SPEC" 2>/dev/null || true)
if [[ -z "$hits_range_766" ]]; then
  echo "OK   [slice-7.2] no 'lines 766' brittle-range citation in spec"
else
  echo "FAIL [slice-7.2]: 'lines 766' brittle range still present:"
  echo "$hits_range_766" | sed 's/^/  /'
  fail=1
fi

# 7.3 (F4) — ADR-0013 brittle-range citations eliminated.
if [[ ! -f "$ADR" ]]; then
  echo "FAIL [slice-7.3]: ADR-0013 file missing at $ADR"
  fail=1
else
  hits_adr_ranges=$(grep -nE '88[-–]98|117[-–]122' "$ADR" 2>/dev/null || true)
  if [[ -z "$hits_adr_ranges" ]]; then
    echo "OK   [slice-7.3] no 88–98 / 117–122 brittle-range citations in ADR-0013"
  else
    echo "FAIL [slice-7.3]: ADR-0013 still cites a brittle range:"
    echo "$hits_adr_ranges" | sed 's/^/  /'
    fail=1
  fi
fi

# 7.4 (F3) — CHANGELOG tarballContentRoot rename bullet reflects REQUIRED.
rename_bullet=$(grep -nE 'tarballContentRoot' "$CHANGELOG" | head -1)
if [[ -z "$rename_bullet" ]]; then
  echo "FAIL [slice-7.4]: no tarballContentRoot mention in CHANGELOG"
  fail=1
else
  rename_line="${rename_bullet%%:*}"
  rename_text="$(sed -n "${rename_line}p" "$CHANGELOG")"
  if echo "$rename_text" | grep -qiE 'now OPTIONAL'; then
    echo "FAIL [slice-7.4]: CHANGELOG tarballContentRoot bullet still says 'now OPTIONAL'"
    fail=1
  elif echo "$rename_text" | grep -qE '\bREQUIRED\b'; then
    echo "OK   [slice-7.4] CHANGELOG tarballContentRoot bullet states REQUIRED, no 'now OPTIONAL'"
  else
    echo "FAIL [slice-7.4]: CHANGELOG tarballContentRoot bullet missing REQUIRED status"
    fail=1
  fi
fi

# 7.5 (F5) — snake_case editorial note.
if grep -qiE 'snake_case' "$SPEC"; then
  echo "OK   [slice-7.5] snake_case editorial note present in spec"
else
  echo "FAIL [slice-7.5]: no snake_case editorial note in spec"
  fail=1
fi

# 7.6 (F14) — D7 narrative bullet reads 'source in addition to reason
# code', not 'instead of reason code'.
if grep -qiE 'instead of reason code' "$CHANGELOG"; then
  echo "FAIL [slice-7.6]: CHANGELOG still says 'instead of reason code'"
  fail=1
elif grep -qiE 'source.{0,30}in addition to.{0,30}reason code' "$CHANGELOG"; then
  echo "OK   [slice-7.6] CHANGELOG carries 'source ... in addition to ... reason code' phrasing"
else
  echo "FAIL [slice-7.6]: CHANGELOG missing 'source ... in addition to reason code' phrasing"
  fail=1
fi

# 7.7 (A2 confirmation) — slice-8 reports ≥ 30 data rows.
if bash "$SLICE8" > /tmp/slice7-slice8.out 2>&1; then
  rows_line=$(grep -E 'OK +\[A2\]' /tmp/slice7-slice8.out | head -1)
  rows=$(echo "$rows_line" | grep -oE '[0-9]+ data rows' | grep -oE '[0-9]+')
  if [[ -n "$rows" ]] && (( rows >= 30 )); then
    echo "OK   [slice-7.7] slice-8 A2 reports $rows data rows (≥ 30)"
  else
    echo "FAIL [slice-7.7]: slice-8 A2 row count not parseable as ≥ 30"
    echo "  $rows_line"
    fail=1
  fi
else
  echo "FAIL [slice-7.7]: slice-8-error-codes.sh exited non-zero"
  cat /tmp/slice7-slice8.out
  fail=1
fi

if (( fail == 0 )); then
  echo "slice-7 (mechanical-sweep) conformance: OK"
  exit 0
fi

echo "slice-7 (mechanical-sweep) conformance: FAIL"
exit 1
