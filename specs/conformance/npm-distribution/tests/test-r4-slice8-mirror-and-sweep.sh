#!/usr/bin/env bash
# Slice-8 acceptance test for npm-distribution-spec-r4.
#
# Asserts the final-validation safety net for R4:
#   8.1 Website mirror parity — `##` headings in
#       website/src/content/docs/spec/npm-distribution.md match the
#       canonical specs/npm-distribution.md, AND R4 anchors that landed in
#       slices 6-7 (NPM-SCOPE-01, the snake_case editorial note) are
#       present in the mirror.
#   8.2 [Unreleased] CHANGELOG body carries no panel/persona/finding-ID
#       language — the changelog-rule MUST list (panel, persona, reviewer,
#       adversarial, consensus, and `SC-N`/`DQ-N`/`SB-N` finding-ID
#       patterns) is rejected.
#   8.3 Every R4 slice acceptance test (specs/conformance/npm-distribution/
#       tests/test-r4-slice*.sh) exits 0 on the current tree.
#   8.4 The slice-8 error-codes lint (specs/conformance/npm-distribution/
#       slice-8-error-codes.sh) exits 0 — the canonical normative-property
#       lint for the R4 error-code surface.
#   8.5 PR #6 title matches the D-R4-7 target:
#       'npm-distribution Round 2-4: spec + reference workflow + remediation'
#       (ASCII hyphen between 2 and 4, per gh's title rendering).
#
# Exits 0 when every assertion passes; non-zero on the first failure.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SPEC="$REPO_ROOT/specs/npm-distribution.md"
MIRROR="$REPO_ROOT/website/src/content/docs/spec/npm-distribution.md"
CHANGELOG="$REPO_ROOT/CHANGELOG.md"
TESTS_DIR="$REPO_ROOT/specs/conformance/npm-distribution/tests"
SLICE8_LINT="$REPO_ROOT/specs/conformance/npm-distribution/slice-8-error-codes.sh"
PR_TARGET_TITLE='npm-distribution Round 2-4: spec + reference workflow + remediation'

fail=0

# 8.1a: ## headings diff is empty.
heading_diff="$(diff <(grep -E '^## ' "$SPEC") <(grep -E '^## ' "$MIRROR") || true)"
if [[ -z "$heading_diff" ]]; then
  echo "OK   [slice-8.1a] mirror ## headings match canonical"
else
  echo "FAIL [slice-8.1a] mirror ## headings drift from canonical:"
  echo "$heading_diff" | sed 's/^/  /'
  fail=1
fi

# 8.1b: mirror contains NPM-SCOPE-01 (slice-6 anchor).
if grep -qF 'NPM-SCOPE-01' "$MIRROR"; then
  echo "OK   [slice-8.1b] mirror carries NPM-SCOPE-01 (slice-6 anchor)"
else
  echo "FAIL [slice-8.1b] mirror missing NPM-SCOPE-01 — mirror is stale relative to slice 6"
  fail=1
fi

# 8.1c: mirror contains snake_case editorial note (slice-7 F5 anchor).
if grep -qF 'snake_case' "$MIRROR"; then
  echo "OK   [slice-8.1c] mirror carries snake_case editorial note (slice-7 F5 anchor)"
else
  echo "FAIL [slice-8.1c] mirror missing snake_case editorial note — mirror is stale relative to slice 7"
  fail=1
fi

# 8.2: [Unreleased] CHANGELOG body has no internal-process language.
unreleased_body="$(awk '
  /^## \[Unreleased\]/{p=1; next}
  p && /^## \[/{exit}
  p {print}
' "$CHANGELOG")"
if [[ -z "$unreleased_body" ]]; then
  echo "FAIL [slice-8.2] no [Unreleased] section found in CHANGELOG"
  fail=1
else
  # Scan for forbidden internal-process tokens. Pattern is anchored on
  # word-boundary or non-letter context so 'panel' never matches inside
  # words like 'plan' or 'channel'.
  bad="$(echo "$unreleased_body" \
    | grep -inE '\b(panel|persona|adversarial|reviewer feedback|agent consensus)\b|\b(SC|DQ|SB)-[0-9]+\b' \
    || true)"
  if [[ -z "$bad" ]]; then
    echo "OK   [slice-8.2] [Unreleased] CHANGELOG body free of internal-process language"
  else
    echo "FAIL [slice-8.2] [Unreleased] CHANGELOG body carries forbidden internal-process tokens:"
    echo "$bad" | sed 's/^/  /'
    fail=1
  fi
fi

# 8.3: every R4 slice acceptance test exits 0.
r4_tests=( "$TESTS_DIR"/test-r4-slice*.sh )
if [[ ${#r4_tests[@]} -eq 0 ]] || [[ ! -e "${r4_tests[0]}" ]]; then
  echo "FAIL [slice-8.3] no test-r4-slice*.sh acceptance tests found in $TESTS_DIR"
  fail=1
else
  r4_fail=0
  for t in "${r4_tests[@]}"; do
    # Skip this script itself — recursive invocation would not terminate.
    if [[ "$(basename "$t")" == "test-r4-slice8-mirror-and-sweep.sh" ]]; then
      continue
    fi
    if ! bash "$t" >/tmp/slice8-r4-run.out 2>&1; then
      echo "FAIL [slice-8.3] R4 slice acceptance test exited non-zero: $(basename "$t")"
      sed 's/^/    /' /tmp/slice8-r4-run.out
      r4_fail=1
      fail=1
    fi
  done
  if (( r4_fail == 0 )); then
    echo "OK   [slice-8.3] every R4 slice acceptance test (test-r4-slice*.sh) exits 0"
  fi
fi

# 8.4: slice-8 error-codes lint exits 0.
if bash "$SLICE8_LINT" >/tmp/slice8-lint.out 2>&1; then
  echo "OK   [slice-8.4] slice-8-error-codes.sh exits 0 (full normative-property lint)"
else
  echo "FAIL [slice-8.4] slice-8-error-codes.sh exited non-zero:"
  sed 's/^/  /' /tmp/slice8-lint.out
  fail=1
fi

# 8.5: PR #6 title matches D-R4-7 target.
if ! command -v gh >/dev/null 2>&1; then
  echo "FAIL [slice-8.5] gh CLI not available — cannot verify PR #6 title"
  fail=1
else
  pr_title="$(gh pr view 6 --json title -q .title 2>/dev/null || true)"
  if [[ -z "$pr_title" ]]; then
    echo "FAIL [slice-8.5] could not read PR #6 title (gh pr view failed)"
    fail=1
  elif [[ "$pr_title" == "$PR_TARGET_TITLE" ]]; then
    echo "OK   [slice-8.5] PR #6 title matches D-R4-7 target"
  else
    echo "FAIL [slice-8.5] PR #6 title drift:"
    echo "  got:    $pr_title"
    echo "  expect: $PR_TARGET_TITLE"
    fail=1
  fi
fi

if (( fail == 0 )); then
  echo "slice-8 (mirror-and-sweep) conformance: OK"
  exit 0
fi

echo "slice-8 (mirror-and-sweep) conformance: FAIL"
exit 1
