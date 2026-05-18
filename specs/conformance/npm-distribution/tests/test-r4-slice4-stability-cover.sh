#!/usr/bin/env bash
# Slice-4 acceptance test for npm-distribution-spec-r4.
#
# Asserts that the §Conformance intro paragraph in specs/npm-distribution.md
# carries the three-sentence code-stability cover (MUST NOT change spelling/meaning;
# Reserved (was: <description>) retention; SHOULD surface codes verbatim), all on
# the same source line, and that ADR-0015's Consequences section gains an addendum
# pointing at the spec's intro line and naming the slice-8 lint.
#
# Exits 0 when every assertion passes; non-zero on the first failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SPEC="$REPO_ROOT/specs/npm-distribution.md"
ADR="$REPO_ROOT/docs/adr/0015-format-of-the-new-conformance-error-code-table.md"

fail=0

# Resolve the §Conformance intro line — the first non-blank, non-heading line
# under `## Conformance`. The slice-4 contract is "augment the intro line in
# place", so all three phrases MUST land on that single line.
heading_line="$(grep -nE '^## Conformance' "$SPEC" | head -1 | cut -d: -f1)"
if [[ -z "$heading_line" ]]; then
  echo "FAIL [slice-4.0]: no '## Conformance' heading in $SPEC"
  exit 1
fi
intro_line="$((heading_line + 2))"

# Assertion 1: MUST NOT change appears on the intro line.
phrase_line() {
  grep -nF -- "$1" "$SPEC" 2>/dev/null | cut -d: -f1 | head -1 || true
}

assert_phrase_on_intro() {
  local label="$1" phrase="$2"
  local line
  line="$(phrase_line "$phrase")"
  if [[ -z "$line" ]]; then
    echo "FAIL [$label]: phrase not found in spec: $phrase"
    fail=1
  elif [[ "$line" != "$intro_line" ]]; then
    echo "FAIL [$label]: phrase found at :$line, expected on §Conformance intro line :$intro_line"
    fail=1
  else
    echo "OK   [$label] '$phrase' on §Conformance intro line :$intro_line"
  fi
}

assert_phrase_on_intro "slice-4.1" "MUST NOT change"
assert_phrase_on_intro "slice-4.2" "Reserved (was:"
assert_phrase_on_intro "slice-4.3" "SHOULD surface codes verbatim"

# Assertion 4: ADR-0015 contains an addendum that cites the spec intro line and
# names the slice-8 lint (the conformance script that enforces the citation
# guard). The addendum is appended after the existing Consequences paragraph.
adr_intro_cite="specs/npm-distribution.md:${intro_line}"
if grep -qF -- "$adr_intro_cite" "$ADR"; then
  echo "OK   [slice-4.4] ADR-0015 cites $adr_intro_cite"
else
  echo "FAIL [slice-4.4]: ADR-0015 does not cite $adr_intro_cite"
  fail=1
fi

if grep -qE 'slice-8-error-codes\.sh|slice-8 (A6|A7)|A7 lint' "$ADR"; then
  echo "OK   [slice-4.5] ADR-0015 names the slice-8 lint"
else
  echo "FAIL [slice-4.5]: ADR-0015 does not name the slice-8 lint (slice-8-error-codes.sh or slice-8 A6/A7)"
  fail=1
fi

if (( fail == 0 )); then
  echo "slice-4 (stability-cover) conformance: OK"
  exit 0
fi

echo "slice-4 (stability-cover) conformance: FAIL"
exit 1
