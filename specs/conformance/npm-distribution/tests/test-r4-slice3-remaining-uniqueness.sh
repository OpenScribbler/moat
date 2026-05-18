#!/usr/bin/env bash
# Slice-3 acceptance test for npm-distribution-spec-r4.
#
# Asserts that the remaining eight multi-anchored source lines have been split
# per the methodical pattern: every NPM-* code in the §Conformance table now
# cites a unique specs/npm-distribution.md:<line>, and the eight per-line splits
# (NPM-CDIR-01..02, NPM-CDIR-04..05, NPM-REV-06..07, NPM-DUAL-01..02,
# NPM-PUB-01..03, NPM-PUB-05..06, NPM-BACKFILL-02..03, NPM-BACKFILL-04..05)
# each anchor on distinct lines.
#
# Exits 0 when every assertion passes; non-zero on the first failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SPEC="$REPO_ROOT/specs/npm-distribution.md"
SLICE8="$REPO_ROOT/specs/conformance/npm-distribution/slice-8-error-codes.sh"

fail=0

# Extract the §Conformance block (between the heading and the next H2).
conf_block="$(awk '/^## Conformance/{p=1; next} p && /^## /{exit} p' "$SPEC")"

# extract_citation <code> -> prints the cited path:line for that NPM-* code
extract_citation() {
  local code="$1"
  echo "$conf_block" \
    | grep -E "^\| \`${code}\`" \
    | sed -E 's/.*`(specs\/npm-distribution\.md:[0-9]+)`.*/\1/'
}

assert_distinct() {
  local label="$1"; shift
  local -a codes=("$@")
  local -a lines=()
  local code line
  for code in "${codes[@]}"; do
    line="$(extract_citation "$code")"
    if [[ -z "$line" ]]; then
      echo "FAIL [$label]: no citation found in §Conformance table for $code"
      fail=1
      return
    fi
    lines+=("$line")
  done
  local unique_count
  unique_count="$(printf '%s\n' "${lines[@]}" | sort -u | wc -l | tr -d ' ')"
  if (( unique_count == ${#codes[@]} )); then
    echo "OK   [$label] ${#codes[@]} codes each cite a distinct line: ${lines[*]}"
  else
    echo "FAIL [$label]: expected ${#codes[@]} distinct citations, got $unique_count (${lines[*]})"
    fail=1
  fi
}

# Assertion 3.1: the §Conformance table has no duplicate citations anywhere.
dup_lines="$(
  echo "$conf_block" \
    | grep -oE 'specs/npm-distribution\.md:[0-9]+' \
    | sort \
    | uniq -d
)"
if [[ -z "$dup_lines" ]]; then
  echo "OK   [slice-3.1] §Conformance table has no duplicate citations"
else
  echo "FAIL [slice-3.1]: §Conformance table has duplicate citations:"
  echo "$dup_lines" | sed 's/^/  /'
  fail=1
fi

# Per-group spot checks (Slice-3 split outcomes):
assert_distinct "slice-3.2" NPM-CDIR-01     NPM-CDIR-02
assert_distinct "slice-3.3" NPM-CDIR-04     NPM-CDIR-05
assert_distinct "slice-3.4" NPM-REV-06      NPM-REV-07
assert_distinct "slice-3.5" NPM-DUAL-01     NPM-DUAL-02
assert_distinct "slice-3.6" NPM-PUB-01      NPM-PUB-02      NPM-PUB-03
assert_distinct "slice-3.7" NPM-PUB-05      NPM-PUB-06
assert_distinct "slice-3.8" NPM-BACKFILL-02 NPM-BACKFILL-03
assert_distinct "slice-3.9" NPM-BACKFILL-04 NPM-BACKFILL-05

# Assertion 3.10: slice-8 A6 still passes — every cited line carries MUST/MUST NOT.
if bash "$SLICE8" >/tmp/slice3-slice8.out 2>&1; then
  if grep -qE 'OK +\[A6\]' /tmp/slice3-slice8.out; then
    echo "OK   [slice-3.10] slice-8 A6 citation guard passes against post-edit spec"
  else
    echo "FAIL [slice-3.10]: slice-8 exited 0 but did not emit OK [A6]"
    cat /tmp/slice3-slice8.out
    fail=1
  fi
else
  echo "FAIL [slice-3.10]: slice-8-error-codes.sh exited non-zero against post-edit spec"
  cat /tmp/slice3-slice8.out
  fail=1
fi

if (( fail == 0 )); then
  echo "slice-3 (remaining-uniqueness) conformance: OK"
  exit 0
fi

echo "slice-3 (remaining-uniqueness) conformance: FAIL"
exit 1
