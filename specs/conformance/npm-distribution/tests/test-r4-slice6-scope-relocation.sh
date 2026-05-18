#!/usr/bin/env bash
# Slice-6 acceptance test for npm-distribution-spec-r4.
#
# Asserts that the Out-of-Scope MUST sentence (the rule that a Conforming
# Client encountering a `distribution_uri` whose host is not
# registry.npmjs.org MUST treat the item as outside this sub-spec's
# normative coverage) has been relocated out of `### Out of Scope` (which
# is non-normative by convention) and into a normative paragraph inside
# §Scope's "Current version" body. The relocation is accompanied by a new
# NPM-SCOPE-01 row in the §Conformance table that cites the new MUST line.
#
# Assertions:
#   6.1  The `### Out of Scope` body (between its H3 and the next H2/H3)
#        contains zero MUST or MUST NOT tokens.
#   6.2  The §Scope body (between its H2 and `### Out of Scope`) contains
#        at least one MUST / MUST NOT token AND the relocated sentence
#        (anchored by 'outside this sub-spec' phrase).
#   6.3  NPM-SCOPE-01 appears at least twice in the spec: once in the
#        relocated normative paragraph and once in the §Conformance table.
#   6.4  The §Conformance table row for NPM-SCOPE-01 cites a
#        specs/npm-distribution.md:<line> anchor whose target line carries
#        a MUST or MUST NOT token.
#
# Exits 0 when every assertion passes; non-zero on the first failure.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SPEC="$REPO_ROOT/specs/npm-distribution.md"

fail=0

# Extract the Out-of-Scope body — the lines between `### Out of Scope` and
# the next heading at the same or higher level (H2 or H3).
out_of_scope_body="$(awk '
  /^### Out of Scope/{p=1; next}
  p && /^(## |### )/{exit}
  p {print}
' "$SPEC")"

# Extract the §Scope body — the lines between `## Scope` and the
# following `### Out of Scope` H3.
scope_body="$(awk '
  /^## Scope/{p=1; next}
  p && /^### Out of Scope/{exit}
  p && /^## /{exit}
  p {print}
' "$SPEC")"

# Assertion 6.1: zero MUST / MUST NOT in Out-of-Scope body.
oos_must_count="$(echo "$out_of_scope_body" | grep -cE '\bMUST(\b| NOT\b)' || true)"
if (( oos_must_count == 0 )); then
  echo "OK   [slice-6.1] '### Out of Scope' body carries 0 MUST/MUST NOT tokens"
else
  echo "FAIL [slice-6.1]: '### Out of Scope' body still carries $oos_must_count MUST/MUST NOT token(s):"
  echo "$out_of_scope_body" | grep -nE '\bMUST(\b| NOT\b)' | sed 's/^/  /'
  fail=1
fi

# Assertion 6.2: §Scope body contains the relocated MUST sentence.
scope_must_count="$(echo "$scope_body" | grep -cE '\bMUST(\b| NOT\b)' || true)"
if (( scope_must_count >= 1 )) \
   && echo "$scope_body" | grep -qiE "outside this sub-spec"; then
  echo "OK   [slice-6.2] §Scope body carries $scope_must_count MUST/MUST NOT and the relocated sentence"
else
  echo "FAIL [slice-6.2]: §Scope body missing MUST or the relocated 'outside this sub-spec' phrase"
  fail=1
fi

# Assertion 6.3: NPM-SCOPE-01 appears at least twice (normative paragraph
# + conformance table row).
scope_code_hits="$(grep -cF 'NPM-SCOPE-01' "$SPEC" || true)"
if (( scope_code_hits >= 2 )); then
  echo "OK   [slice-6.3] NPM-SCOPE-01 appears $scope_code_hits times in $SPEC (paragraph + table)"
else
  echo "FAIL [slice-6.3]: NPM-SCOPE-01 appears $scope_code_hits time(s), expected ≥ 2"
  fail=1
fi

# Assertion 6.4: the §Conformance table row for NPM-SCOPE-01 cites a
# specs/npm-distribution.md:<line> anchor pointing at a MUST/MUST NOT line.
scope_row="$(grep -E '^\| `NPM-SCOPE-01`' "$SPEC" | head -1)"
if [[ -z "$scope_row" ]]; then
  echo "FAIL [slice-6.4]: no §Conformance table row for NPM-SCOPE-01 found"
  fail=1
else
  scope_cite="$(echo "$scope_row" | grep -oE 'specs/npm-distribution\.md:[0-9]+' | head -1)"
  if [[ -z "$scope_cite" ]]; then
    echo "FAIL [slice-6.4]: NPM-SCOPE-01 row has no specs/npm-distribution.md:<line> citation"
    fail=1
  else
    cited_line="${scope_cite##*:}"
    target="$(sed -n "${cited_line}p" "$SPEC")"
    if echo "$target" | grep -qE '\bMUST(\b| NOT\b)'; then
      echo "OK   [slice-6.4] NPM-SCOPE-01 cites $scope_cite which carries MUST/MUST NOT"
    else
      echo "FAIL [slice-6.4]: NPM-SCOPE-01 cites $scope_cite which does NOT carry MUST/MUST NOT"
      echo "  cited line: $target"
      fail=1
    fi
  fi
fi

if (( fail == 0 )); then
  echo "slice-6 (scope-relocation) conformance: OK"
  exit 0
fi

echo "slice-6 (scope-relocation) conformance: FAIL"
exit 1
