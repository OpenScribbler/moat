#!/usr/bin/env bash
# Slice-5 acceptance test for npm-distribution-spec-r4.
#
# Asserts that the slice-8 conformance script grows a new A7 check enforcing
# citation uniqueness in the §Conformance table, and that the previous A7
# (website mirror parity) has been renumbered to A8. Also asserts that the
# script's prose has been retitled from slice-7 to slice-8 (F8 mechanical
# drift sweep).
#
# Assertions:
#   5.1  slice-8-error-codes.sh stdout against the real spec contains
#        exactly one 'OK [A7]' line and exactly one 'OK [A8]' line, and
#        the A7 line names citation uniqueness (not mirror parity).
#   5.2  A synthetic duplicate-citation spec causes the script to exit 1
#        and emit 'FAIL [A7]'.
#   5.3  No 'slice-7' tokens remain in slice-8-error-codes.sh.
#
# Exits 0 when every assertion passes; non-zero on the first failure.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SLICE8="$REPO_ROOT/specs/conformance/npm-distribution/slice-8-error-codes.sh"
SPEC="$REPO_ROOT/specs/npm-distribution.md"
MIRROR="$REPO_ROOT/website/src/content/docs/spec/npm-distribution.md"

fail=0

# Assertion 5.1: run slice-8 against the real tree, capture stdout, assert
# exactly one OK [A7] (citation uniqueness) and exactly one OK [A8]
# (mirror parity).
real_out="$(bash "$SLICE8" 2>&1)"
real_rc=$?
if (( real_rc != 0 )); then
  echo "FAIL [slice-5.1]: slice-8-error-codes.sh exited $real_rc against the real tree"
  echo "$real_out"
  fail=1
else
  n_a7=$(echo "$real_out" | grep -cE '^OK +\[A7\]' || true)
  n_a8=$(echo "$real_out" | grep -cE '^OK +\[A8\]' || true)
  if (( n_a7 == 1 && n_a8 == 1 )); then
    a7_line=$(echo "$real_out" | grep -E '^OK +\[A7\]' | head -1)
    if echo "$a7_line" | grep -qiE 'unique|duplicate'; then
      echo "OK   [slice-5.1] A7 (citation uniqueness) + A8 (mirror parity) both pass against real tree"
    else
      echo "FAIL [slice-5.1]: A7 OK line does not name citation uniqueness: $a7_line"
      fail=1
    fi
  else
    echo "FAIL [slice-5.1]: expected exactly 1 OK [A7] and 1 OK [A8], got A7=$n_a7 A8=$n_a8"
    echo "$real_out"
    fail=1
  fi
fi

# Assertion 5.2: stage a scratch tree with a duplicate citation in the spec
# body, copy the slice-8 script and the website mirror unchanged, then run
# the script against the scratch REPO_ROOT and assert it exits non-zero and
# emits FAIL [A7]. The scratch tree mimics the layout slice-8 expects:
# REPO_ROOT/specs/conformance/npm-distribution/slice-8-error-codes.sh,
# REPO_ROOT/specs/npm-distribution.md, and the website mirror.
scratch="$(mktemp -d -t slice5-XXXXXX)"
trap 'rm -rf "$scratch"' EXIT

mkdir -p "$scratch/specs/conformance/npm-distribution"
mkdir -p "$scratch/website/src/content/docs/spec"
cp "$SLICE8"  "$scratch/specs/conformance/npm-distribution/slice-8-error-codes.sh"
cp "$MIRROR"  "$scratch/website/src/content/docs/spec/npm-distribution.md"

# Synthesize a duplicate citation: copy the spec and rewrite the second
# row of the §Conformance table so its citation points at the same line
# the first row already cites. Picks the first two NPM-* rows so the
# rewrite is deterministic.
first_cite="$(grep -oE 'specs/npm-distribution\.md:[0-9]+' "$SPEC" | head -1)"
second_row_pattern="$(grep -nE '^\| `NPM-' "$SPEC" | sed -n '2p' | cut -d: -f1)"
if [[ -z "$first_cite" || -z "$second_row_pattern" ]]; then
  echo "FAIL [slice-5.2]: could not synthesize duplicate-citation fixture"
  fail=1
else
  awk -v target_line="$second_row_pattern" -v cite="$first_cite" '
    NR == target_line {
      sub(/specs\/npm-distribution\.md:[0-9]+/, cite, $0)
    }
    { print }
  ' "$SPEC" > "$scratch/specs/npm-distribution.md"

  scratch_out="$(bash "$scratch/specs/conformance/npm-distribution/slice-8-error-codes.sh" 2>&1)"
  scratch_rc=$?
  if (( scratch_rc != 0 )) && echo "$scratch_out" | grep -qE '^FAIL +\[A7\]'; then
    echo "OK   [slice-5.2] synthetic duplicate-citation spec triggers FAIL [A7] (rc=$scratch_rc)"
  else
    echo "FAIL [slice-5.2]: expected rc!=0 and FAIL [A7] from synthetic spec, got rc=$scratch_rc"
    echo "$scratch_out"
    fail=1
  fi
fi

# Assertion 5.3: the slice-8 script must no longer contain 'slice-7' tokens
# (F8 mechanical drift sweep).
if grep -nE '\bslice-7\b' "$SLICE8" >/dev/null 2>&1; then
  echo "FAIL [slice-5.3]: 'slice-7' token still present in slice-8-error-codes.sh:"
  grep -nE '\bslice-7\b' "$SLICE8"
  fail=1
else
  echo "OK   [slice-5.3] no 'slice-7' tokens remain in slice-8-error-codes.sh"
fi

if (( fail == 0 )); then
  echo "slice-5 (A7 regression) conformance: OK"
  exit 0
fi

echo "slice-5 (A7 regression) conformance: FAIL"
exit 1
