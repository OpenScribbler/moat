#!/usr/bin/env bash
# Slice-1 acceptance test for npm-distribution-spec-r4.
#
# Asserts that the no-operator-override MUST NOT at specs/npm-distribution.md:53
# is scoped to Registry-source revocations and defers to moat-spec.md:636 for
# Publisher-source revocations. Verifies the slice-8 A6 citation guard still
# passes against the post-edit spec.
#
# Exits 0 when every assertion passes; non-zero on the first failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SPEC="$REPO_ROOT/specs/npm-distribution.md"
SLICE8="$REPO_ROOT/specs/conformance/npm-distribution/slice-8-error-codes.sh"

fail=0

# Slice-3 splits multi-MUST paragraphs in §Revocation, so anchor assertions to
# the §Revocation section (between its H2 heading and the next H2), not to
# fixed line numbers. The slice-1 contract is "scope qualifier + defer-reference
# present inside §Revocation at the Materialization Boundary."
rev_section="$(awk '/^## Revocation at the Materialization Boundary/{p=1; next} p && /^## /{exit} p' "$SPEC")"

# Assertion 1: a "Registry-source" qualifier is present in §Revocation.
if echo "$rev_section" | grep -qE 'Registry-source'; then
  hit_line="$(grep -nE 'Registry-source' "$SPEC" | head -1 | cut -d: -f1)"
  echo "OK   [slice-1.1] 'Registry-source' qualifier present in §Revocation at :$hit_line"
else
  echo "FAIL [slice-1.1]: no 'Registry-source' qualifier found in §Revocation at the Materialization Boundary"
  fail=1
fi

# Assertion 2: §Revocation defers explicitly to moat-spec.md §Revocation —
# either a verbatim 'moat-spec.md:636' citation or a linked anchor.
defer_hits="$(echo "$rev_section" | grep -cE 'moat-spec\.md:636|moat-spec\.md#revocation' || true)"
if (( defer_hits < 1 )); then
  echo "FAIL [slice-1.2]: no defer-reference to moat-spec.md:636 (or moat-spec.md#revocation) inside §Revocation"
  fail=1
else
  echo "OK   [slice-1.2] $defer_hits defer-reference(s) to moat-spec.md revocation present in §Revocation"
fi

# Assertion 3: the slice-8 A6 citation guard still exits 0. The :53 line must
# continue to carry MUST or MUST NOT after the in-place rewrite so that the
# existing NPM-REV-* table rows that cite :53 remain valid.
if bash "$SLICE8" >/tmp/slice1-slice8.out 2>&1; then
  if grep -qE 'OK +\[A6\]' /tmp/slice1-slice8.out; then
    echo "OK   [slice-1.3] slice-8 A6 citation guard passes against post-edit spec"
  else
    echo "FAIL [slice-1.3]: slice-8 exited 0 but did not emit OK [A6]"
    cat /tmp/slice1-slice8.out
    fail=1
  fi
else
  echo "FAIL [slice-1.3]: slice-8-error-codes.sh exited non-zero against post-edit spec"
  cat /tmp/slice1-slice8.out
  fail=1
fi

if (( fail == 0 )); then
  echo "slice-1 (revocation-scope) conformance: OK"
  exit 0
fi

echo "slice-1 (revocation-scope) conformance: FAIL"
exit 1
