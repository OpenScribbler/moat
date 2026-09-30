#!/usr/bin/env bash
# Slice 10 conformance (Round 3, part A): CHANGELOG.md release-section hygiene.
#
# Asserts the editorial sweep that closes Round 3:
#   A1: CHANGELOG.md has the `## [0.8.0]` section that shipped this work.
#   A2: [0.8.0] section body contains no reviewer/persona names.
#   A3: [0.8.0] section body contains no finding-ID patterns
#       (D1-D10, SC-N, DQ-N, SB-N).
#   A4: [0.8.0] section body contains no "Round 3" framing.
#   A5: [0.8.0] section body cites `specs/npm-distribution.md`
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

# A1: CHANGELOG.md has the `## [0.8.0]` release section. The entries this
# script checks were written under [Unreleased] and shipped in v0.8.0, so
# the checks follow them into the release section.
if grep -qE '^## \[0\.8\.0\]' "$cl"; then
  echo "OK  [A1] CHANGELOG.md has a '## [0.8.0]' section"
else
  echo "FAIL [A1]: no '## [0.8.0]' section in CHANGELOG.md"
  fail=1
fi

# Capture the [0.8.0] section body. Flag-toggle awk: open after the
# heading, close on the next H2.
unreleased="$(awk '/^## \[0\.8\.0\]/{flag=1; next} flag && /^## /{flag=0} flag' "$cl")"

if [[ -z "$unreleased" ]]; then
  echo "FAIL [A2-A5]: [0.8.0] body empty"
  fail=1
else
  # A2: no reviewer/persona names. The `.claude/rules/changelog.md` rule
  # forbids panel-review, adversarial-review, and persona-name references.
  # Word-boundary anchored case-insensitive grep so "remyriad" or "purist"
  # in unrelated text wouldn't false-positive.
  if echo "$unreleased" | grep -iqwE 'remy|SpecPurist|karpathy|adversarial|panel review|five-persona'; then
    echo "FAIL [A2]: [0.8.0] body names a reviewer/persona or review process:"
    echo "$unreleased" | grep -inE 'remy|SpecPurist|karpathy|adversarial|panel review|five-persona' | head -3 | sed 's/^/    /'
    fail=1
  else
    echo "OK  [A2] [0.8.0] body contains no reviewer/persona names"
  fi

  # A3: no finding IDs of the form D1-D10, SC-N, DQ-N, SB-N. We accept
  # NPM-<SECTION>-<NN> codes (those are the public Conformance error
  # codes, a different surface).
  bad_ids="$(echo "$unreleased" | grep -oE '\b(D[1-9][0-9]?|SC-[0-9]+|DQ-[0-9]+|SB-[0-9]+)\b' | sort -u || true)"
  if [[ -n "$bad_ids" ]]; then
    echo "FAIL [A3]: [0.8.0] body contains internal finding IDs:"
    echo "$bad_ids" | sed 's/^/    /'
    fail=1
  else
    echo "OK  [A3] [0.8.0] body contains no internal finding IDs"
  fi

  # A4: no 'Round 3' framing. "Round 3" is internal-process language.
  if echo "$unreleased" | grep -qE '\bRound 3\b|\bround-3\b|\bR3\b'; then
    echo "FAIL [A4]: [0.8.0] body uses 'Round 3' framing:"
    echo "$unreleased" | grep -inE '\bRound 3\b|\bround-3\b|\bR3\b' | head -3 | sed 's/^/    /'
    fail=1
  else
    echo "OK  [A4] [0.8.0] body contains no 'Round 3' framing"
  fi

  # A5: cites specs/npm-distribution.md and names at least three Round-3
  # changes by substance. Acceptable substance markers: distribution_uri,
  # hard revocation OR MOAT_ALLOW_REVOKED removal, single-path Rekor OR
  # rekorLogIndex removal.
  if ! echo "$unreleased" | grep -qF 'specs/npm-distribution.md'; then
    echo "FAIL [A5a]: [0.8.0] body does not cite 'specs/npm-distribution.md'"
    fail=1
  else
    echo "OK  [A5a] [0.8.0] cites 'specs/npm-distribution.md'"
  fi

  matched=0
  echo "$unreleased" | grep -qE 'distribution_uri' && matched=$((matched + 1))
  echo "$unreleased" | grep -qiE 'hard revocation|MOAT_ALLOW_REVOKED' && matched=$((matched + 1))
  echo "$unreleased" | grep -qiE 'single-path Rekor|rekorLogIndex' && matched=$((matched + 1))
  echo "$unreleased" | grep -qiE 'Conformance \(normative\)|error code table|NPM-[A-Z]+-[0-9]' && matched=$((matched + 1))
  if [[ "$matched" -ge 3 ]]; then
    echo "OK  [A5b] [0.8.0] names $matched Round-3 substance markers (need ≥ 3)"
  else
    echo "FAIL [A5b]: [0.8.0] names only $matched Round-3 substance markers (need ≥ 3)"
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
