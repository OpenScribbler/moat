#!/usr/bin/env bash
# Slice-2 acceptance test for npm-distribution-spec-r4.
#
# Asserts that the two highest-density multi-anchored lines (:47 with NPM-REV-01..04
# and :66 with NPM-SCHEMA-02..05) have been split: each of the eight affected codes
# in §Conformance now cites a distinct specs/npm-distribution.md:<line>.
#
# Exits 0 when every assertion passes; non-zero on the first failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SPEC="$REPO_ROOT/specs/npm-distribution.md"
SLICE8="$REPO_ROOT/specs/conformance/npm-distribution/slice-8-error-codes.sh"

fail=0

# Pull the §Conformance table block (between the heading line and the next H2
# heading) into a temporary file once, then run column extracts off it.
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

# Assertion 2.1: NPM-REV-01..04 each cite a distinct line.
assert_distinct "slice-2.1" NPM-REV-01 NPM-REV-02 NPM-REV-03 NPM-REV-04

# Assertion 2.2: NPM-SCHEMA-02..05 each cite a distinct line.
assert_distinct "slice-2.2" NPM-SCHEMA-02 NPM-SCHEMA-03 NPM-SCHEMA-04 NPM-SCHEMA-05

# Assertion 2.3: union of the eight codes' citations contains 8 distinct lines.
all_citations="$(
  for c in NPM-REV-01 NPM-REV-02 NPM-REV-03 NPM-REV-04 \
           NPM-SCHEMA-02 NPM-SCHEMA-03 NPM-SCHEMA-04 NPM-SCHEMA-05; do
    extract_citation "$c"
  done | sort -u | wc -l | tr -d ' '
)"
if (( all_citations == 8 )); then
  echo "OK   [slice-2.3] union of REV-01..04 and SCHEMA-02..05 spans 8 distinct citations"
else
  echo "FAIL [slice-2.3]: expected 8 distinct citations across REV-01..04 + SCHEMA-02..05, got $all_citations"
  fail=1
fi

# Assertion 2.4: slice-8 A6 still passes — every new cited line carries MUST/MUST NOT.
if bash "$SLICE8" >/tmp/slice2-slice8.out 2>&1; then
  if grep -qE 'OK +\[A6\]' /tmp/slice2-slice8.out; then
    echo "OK   [slice-2.4] slice-8 A6 citation guard passes against post-edit spec"
  else
    echo "FAIL [slice-2.4]: slice-8 exited 0 but did not emit OK [A6]"
    cat /tmp/slice2-slice8.out
    fail=1
  fi
else
  echo "FAIL [slice-2.4]: slice-8-error-codes.sh exited non-zero against post-edit spec"
  cat /tmp/slice2-slice8.out
  fail=1
fi

if (( fail == 0 )); then
  echo "slice-2 (rev-schema-uniqueness) conformance: OK"
  exit 0
fi

echo "slice-2 (rev-schema-uniqueness) conformance: FAIL"
exit 1
