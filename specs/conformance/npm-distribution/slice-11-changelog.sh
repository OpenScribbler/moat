#!/usr/bin/env bash
# Slice 10 conformance (Round 3, part A): CHANGELOG.md [Unreleased] hygiene.
#
# Asserts the editorial sweep that closes Round 3:
#   A1: CHANGELOG.md has an `## [Unreleased]` section as the first H2.
#   A2: [Unreleased] section body contains no reviewer/persona names.
#   A3: [Unreleased] section body contains no finding-ID patterns
#       (D1-D10, SC-N, DQ-N, SB-N).
#   A4: [Unreleased] section body contains no "Round 3" framing.
#   A5: [Unreleased] section body cites `specs/npm-distribution.md`
#       and names at least three Round-3 changes (distribution_uri,
#       hard revocation, single-path Rekor query).
#
# The CHANGELOG hygiene rules live at `.claude/rules/changelog.md`;
# this slice script is the enforcement layer for the "no internal process
# metadata" clause of that rule.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

cl=CHANGELOG.md
fail=0

if [[ ! -f "$cl" ]]; then
  echo "FAIL [pre]: $cl missing"
  echo "slice-10 (changelog) conformance: FAIL"
  exit 1
fi

# A1: first H2 in CHANGELOG.md is `## [Unreleased]`. Anchoring on "first H2"
# is the convention from `.claude/rules/changelog.md`: [Unreleased] sits at
# the top and versioned releases follow it.
first_h2="$(grep -m1 '^## ' "$cl" || true)"
if [[ "$first_h2" == "## [Unreleased]" ]]; then
  echo "OK  [A1] first H2 in CHANGELOG.md is '## [Unreleased]'"
else
  echo "FAIL [A1]: first H2 is '$first_h2' (expected '## [Unreleased]')"
  fail=1
fi

# Capture the [Unreleased] section body. Flag-toggle awk: open after the
# heading, close on the next H2.
unreleased="$(awk '/^## \[Unreleased\]/{flag=1; next} flag && /^## /{flag=0} flag' "$cl")"

if [[ -z "$unreleased" ]]; then
  echo "FAIL [A2-A5]: [Unreleased] body empty"
  fail=1
else
  # A2: no reviewer/persona names. The `.claude/rules/changelog.md` rule
  # forbids panel-review, adversarial-review, and persona-name references.
  # Word-boundary anchored case-insensitive grep so "remyriad" or "purist"
  # in unrelated text wouldn't false-positive.
  if echo "$unreleased" | grep -iqwE 'remy|SpecPurist|karpathy|adversarial|panel review|five-persona'; then
    echo "FAIL [A2]: [Unreleased] body names a reviewer/persona or review process:"
    echo "$unreleased" | grep -inE 'remy|SpecPurist|karpathy|adversarial|panel review|five-persona' | head -3 | sed 's/^/    /'
    fail=1
  else
    echo "OK  [A2] [Unreleased] body contains no reviewer/persona names"
  fi

  # A3: no finding IDs of the form D1-D10, SC-N, DQ-N, SB-N. We accept
  # NPM-<SECTION>-<NN> codes (those are the public Conformance error
  # codes, a different surface).
  bad_ids="$(echo "$unreleased" | grep -oE '\b(D[1-9][0-9]?|SC-[0-9]+|DQ-[0-9]+|SB-[0-9]+)\b' | sort -u || true)"
  if [[ -n "$bad_ids" ]]; then
    echo "FAIL [A3]: [Unreleased] body contains internal finding IDs:"
    echo "$bad_ids" | sed 's/^/    /'
    fail=1
  else
    echo "OK  [A3] [Unreleased] body contains no internal finding IDs"
  fi

  # A4: no 'Round 3' framing. "Round 3" is internal-process language.
  if echo "$unreleased" | grep -qE '\bRound 3\b|\bround-3\b|\bR3\b'; then
    echo "FAIL [A4]: [Unreleased] body uses 'Round 3' framing:"
    echo "$unreleased" | grep -inE '\bRound 3\b|\bround-3\b|\bR3\b' | head -3 | sed 's/^/    /'
    fail=1
  else
    echo "OK  [A4] [Unreleased] body contains no 'Round 3' framing"
  fi

  # A5: cites specs/npm-distribution.md and names at least three Round-3
  # changes by substance. Acceptable substance markers: distribution_uri,
  # hard revocation OR MOAT_ALLOW_REVOKED removal, single-path Rekor OR
  # rekorLogIndex removal.
  if ! echo "$unreleased" | grep -qF 'specs/npm-distribution.md'; then
    echo "FAIL [A5a]: [Unreleased] body does not cite 'specs/npm-distribution.md'"
    fail=1
  else
    echo "OK  [A5a] [Unreleased] cites 'specs/npm-distribution.md'"
  fi

  matched=0
  echo "$unreleased" | grep -qE 'distribution_uri' && matched=$((matched + 1))
  echo "$unreleased" | grep -qiE 'hard revocation|MOAT_ALLOW_REVOKED' && matched=$((matched + 1))
  echo "$unreleased" | grep -qiE 'single-path Rekor|rekorLogIndex' && matched=$((matched + 1))
  echo "$unreleased" | grep -qiE 'Conformance \(normative\)|error code table|NPM-[A-Z]+-[0-9]' && matched=$((matched + 1))
  if [[ "$matched" -ge 3 ]]; then
    echo "OK  [A5b] [Unreleased] names $matched Round-3 substance markers (need ≥ 3)"
  else
    echo "FAIL [A5b]: [Unreleased] names only $matched Round-3 substance markers (need ≥ 3)"
    fail=1
  fi
fi

if [[ "$fail" -eq 0 ]]; then
  echo "slice-10 (changelog) conformance: OK"
  exit 0
else
  echo "slice-10 (changelog) conformance: FAIL"
  exit 1
fi
