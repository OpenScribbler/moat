#!/usr/bin/env bash
# Slice 2 conformance (Round 3): single-path Rekor-query Publisher Verification.
# Path 1 / rekorLogIndex hint is dropped (D2). The §Publisher Verification block
# specifies one query algorithm, one tiebreaker rule (logIndex descending), and
# one anti-rollback clause. The reference workflow no longer writes rekorLogIndex
# and no longer needs `contents: write`.
#
# Red before slice-2 impl; green after.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
mirror=website/src/content/docs/spec/npm-distribution.md
refwf=reference/moat-npm-publisher.yml
fail=0

if [[ ! -f "$spec" ]]; then
  echo "FAIL [pre]: $spec missing"
  echo "slice-2 conformance: FAIL"
  exit 1
fi
if [[ ! -f "$refwf" ]]; then
  echo "FAIL [pre]: $refwf missing"
  echo "slice-2 conformance: FAIL"
  exit 1
fi

# A1: rekorLogIndex absent from spec body (D2: Path 1 dropped wholesale).
if [[ $(grep -c rekorLogIndex "$spec") -eq 0 ]]; then
  echo "OK  A1 rekorLogIndex absent from $spec"
else
  echo "FAIL A1 rekorLogIndex still present in $spec ($(grep -c rekorLogIndex "$spec") matches)"
  fail=1
fi

# A2: rekorLogIndex absent from reference workflow.
if [[ $(grep -c rekorLogIndex "$refwf") -eq 0 ]]; then
  echo "OK  A2 rekorLogIndex absent from $refwf"
else
  echo "FAIL A2 rekorLogIndex still present in $refwf ($(grep -c rekorLogIndex "$refwf") matches)"
  fail=1
fi

# A3: reference workflow's permissions block no longer requests `contents: write`.
perm_block="$(awk '/^permissions:/{flag=1; next} flag && /^[^[:space:]]/{flag=0} flag' "$refwf")"
if [[ -z "$perm_block" ]]; then
  echo "FAIL A3 permissions: block not found in $refwf"
  fail=1
elif echo "$perm_block" | grep -E '^[[:space:]]+contents:[[:space:]]+write' >/dev/null; then
  echo "FAIL A3 'contents: write' still present in $refwf permissions block"
  fail=1
else
  echo "OK  A3 'contents: write' permission removed"
fi

# A4: §Publisher Verification block exists and contains the single-path tiebreaker
# (logIndex + most-recent semantics) and the anti-rollback clause.
pv_block="$(awk '/^## Publisher Verification/{flag=1; next} flag && /^## /{flag=0} flag' "$spec")"
if [[ -z "$pv_block" ]]; then
  echo "FAIL A4 §Publisher Verification section not found"
  fail=1
else
  if echo "$pv_block" | grep -iE '(logIndex[^.]*most[[:space:]]+recent|most[[:space:]]+recent[^.]*logIndex|logIndex[^.]*descending|descending[^.]*logIndex)' >/dev/null; then
    echo "OK  A4a tiebreaker phrase (logIndex + most-recent/descending) present"
  else
    echo "FAIL A4a tiebreaker phrase missing from §Publisher Verification"
    fail=1
  fi
  if echo "$pv_block" | grep -iE '(anti[- ]rollback|strictly[[:space:]]+greater|never[[:space:]]+smaller|monotonic)' >/dev/null; then
    echo "OK  A4b anti-rollback clause present"
  else
    echo "FAIL A4b anti-rollback clause missing from §Publisher Verification"
    fail=1
  fi
  if echo "$pv_block" | grep -E '\*\*Path [12]' >/dev/null; then
    echo "FAIL A4c Path 1 / Path 2 dichotomy header still present in §Publisher Verification"
    fail=1
  else
    echo "OK  A4c Path 1 / Path 2 dichotomy removed"
  fi
fi

# A5: publisherSigning.rekorLogIndex schema row is removed.
if grep -nE '^\| `publisherSigning\.rekorLogIndex` \|' "$spec" >/dev/null; then
  echo "FAIL A5 publisherSigning.rekorLogIndex schema row still present"
  fail=1
else
  echo "OK  A5 publisherSigning.rekorLogIndex schema row removed"
fi

# A6: worked-example JSON no longer carries the rekorLogIndex line.
ex_block="$(awk '/Worked example/,/^---$/' "$spec")"
if echo "$ex_block" | grep -F 'rekorLogIndex' >/dev/null; then
  echo "FAIL A6 worked-example JSON still contains rekorLogIndex"
  fail=1
else
  echo "OK  A6 worked-example JSON no longer carries rekorLogIndex"
fi

# A7: website mirror parity after stripping frontmatter.
if [[ -f "$mirror" ]]; then
  diff <(sed '1,/^---$/d' "$mirror") "$spec" >/tmp/slice-2-mirror-diff.txt
  if [[ $? -eq 0 ]]; then
    echo "OK  A7 website mirror byte-identical to spec body after stripping front-matter"
  else
    echo "FAIL A7 website mirror diverges from spec (see /tmp/slice-2-mirror-diff.txt)"
    fail=1
  fi
else
  echo "FAIL A7 website mirror missing: $mirror"
  fail=1
fi

if [[ "$fail" -eq 0 ]]; then
  echo "slice-2 conformance: OK"
  exit 0
else
  echo "slice-2 conformance: FAIL"
  exit 1
fi
