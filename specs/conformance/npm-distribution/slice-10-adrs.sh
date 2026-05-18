#!/usr/bin/env bash
# Slice 9 conformance (Round 3): ADR supersession with meta-convention.
#
# Asserts the in-repo ADR supersession convention codified by the (draft)
# ADR-0014 meta-decision: the new ADR carries a `Supersedes:` header between
# `Feature:` and the first blank line; the old ADR flips its `Status:` value
# to `Superseded by ADR-NNNN`. Slice 3 already applied this pattern to the
# ADR-0007 / ADR-0010 pair; this slice extends it to the ADR-0008 / ADR-0011
# pair (D2 single-path Rekor query reversing Round-2 Path 1) and promotes
# ADR-0012 through ADR-0015 from `.ship/npm-distribution-spec-r3/adr/`
# drafts to `docs/adr/` with `Status: Accepted`.
#
# Conformance error codes asserted by this script (per §Conformance in
# specs/npm-distribution.md): NPM-PUB-NN — none directly; this slice is
# strictly meta about the ADR audit trail. The codes anchored on §Publisher
# Verification (NPM-PUB-*) are validated indirectly because ADR-0011 is the
# new normative home for the single-path query decision they cite.
#
# Red before slice-9 impl; green after.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

fail=0

# Resolve ADR files by numeric prefix glob — title slugs differ across ADRs.
adr7=$(ls docs/adr/0007-*.md 2>/dev/null | head -1)
adr8=$(ls docs/adr/0008-*.md 2>/dev/null | head -1)
adr10=$(ls docs/adr/0010-*.md 2>/dev/null | head -1)
adr11=$(ls docs/adr/0011-*.md 2>/dev/null | head -1)

# A1: ADR-0007:4 reads `Status: Superseded by ADR-0010` (preserved from Slice 3).
if [[ -z "$adr7" ]]; then
  echo "FAIL [A1]: ADR-0007 file not found under docs/adr/"
  fail=1
else
  line4="$(sed -n '4p' "$adr7")"
  if [[ "$line4" == "Status: Superseded by ADR-0010" ]]; then
    echo "OK  [A1] ADR-0007 line 4 reads 'Status: Superseded by ADR-0010'"
  else
    echo "FAIL [A1]: ADR-0007 line 4 is '$line4' (expected 'Status: Superseded by ADR-0010')"
    fail=1
  fi
fi

# A2: ADR-0008:4 reads `Status: Superseded by ADR-0011` (Slice 9 flip).
if [[ -z "$adr8" ]]; then
  echo "FAIL [A2]: ADR-0008 file not found under docs/adr/"
  fail=1
else
  line4="$(sed -n '4p' "$adr8")"
  if [[ "$line4" == "Status: Superseded by ADR-0011" ]]; then
    echo "OK  [A2] ADR-0008 line 4 reads 'Status: Superseded by ADR-0011'"
  else
    echo "FAIL [A2]: ADR-0008 line 4 is '$line4' (expected 'Status: Superseded by ADR-0011')"
    fail=1
  fi
fi

# A3: ADR-0010 carries `Supersedes: ADR-0007` between `Feature:` and the
# first blank line. The convention from the meta-ADR (0014) is one header
# line, not two new keys; we anchor with a flag-toggle awk that opens on
# the `Feature:` line and closes on the first blank line.
if [[ -z "$adr10" ]]; then
  echo "FAIL [A3]: ADR-0010 file not found under docs/adr/"
  fail=1
else
  header_block="$(awk '
    /^Feature:/ {flag=1; next}
    flag && /^$/ {flag=0}
    flag
  ' "$adr10")"
  if echo "$header_block" | grep -qE '^Supersedes:[[:space:]]+ADR-0007\b'; then
    echo "OK  [A3] ADR-0010 carries 'Supersedes: ADR-0007' between Feature: and blank line"
  else
    echo "FAIL [A3]: ADR-0010 header block (Feature: → blank) lacks 'Supersedes: ADR-0007':"
    echo "$header_block" | sed 's/^/    /'
    fail=1
  fi
fi

# A4: ADR-0011 exists and carries `Supersedes: ADR-0008` between `Feature:`
# and the first blank line.
if [[ -z "$adr11" ]]; then
  echo "FAIL [A4]: ADR-0011 file not found under docs/adr/"
  fail=1
else
  header_block="$(awk '
    /^Feature:/ {flag=1; next}
    flag && /^$/ {flag=0}
    flag
  ' "$adr11")"
  if echo "$header_block" | grep -qE '^Supersedes:[[:space:]]+ADR-0008\b'; then
    echo "OK  [A4] ADR-0011 carries 'Supersedes: ADR-0008' between Feature: and blank line"
  else
    echo "FAIL [A4]: ADR-0011 header block (Feature: → blank) lacks 'Supersedes: ADR-0008':"
    echo "$header_block" | sed 's/^/    /'
    fail=1
  fi
  # A4b: ADR-0011 line 4 reads `Status: Accepted` (not `Proposed`).
  line4_11="$(sed -n '4p' "$adr11")"
  if [[ "$line4_11" == "Status: Accepted" ]]; then
    echo "OK  [A4b] ADR-0011 line 4 reads 'Status: Accepted'"
  else
    echo "FAIL [A4b]: ADR-0011 line 4 is '$line4_11' (expected 'Status: Accepted')"
    fail=1
  fi
fi

# A5: ADR-0012 through ADR-0015 exist in docs/adr/ with `Status: Accepted`
# on line 4. The drafts in `.ship/npm-distribution-spec-r3/adr/` are
# `Status: Proposed`; promotion to `docs/adr/` is the impl step that flips
# them. Conformance asserts the post-promotion state.
for n in 0012 0013 0014 0015; do
  adr=$(ls docs/adr/${n}-*.md 2>/dev/null | head -1)
  if [[ -z "$adr" ]]; then
    echo "FAIL [A5-${n}]: ADR-${n} not found under docs/adr/"
    fail=1
    continue
  fi
  line4="$(sed -n '4p' "$adr")"
  if [[ "$line4" == "Status: Accepted" ]]; then
    echo "OK  [A5-${n}] ADR-${n} line 4 reads 'Status: Accepted'"
  else
    echo "FAIL [A5-${n}]: ADR-${n} line 4 is '$line4' (expected 'Status: Accepted')"
    fail=1
  fi
done

# A6: ADRs 0001-0006 and 0009 remain `Status: Accepted` — supersession is
# scoped, not a sweep. The seven control ADRs are the ones not touched by
# Round-3 reversals; if any of them flip status, the slice has overreached.
for n in 0001 0002 0003 0004 0005 0006 0009; do
  adr=$(ls docs/adr/${n}-*.md 2>/dev/null | head -1)
  if [[ -z "$adr" ]]; then
    echo "FAIL [A6-${n}]: ADR-${n} not found under docs/adr/"
    fail=1
    continue
  fi
  line4="$(sed -n '4p' "$adr")"
  if [[ "$line4" == "Status: Accepted" ]]; then
    echo "OK  [A6-${n}] ADR-${n} line 4 still 'Status: Accepted' (control)"
  else
    echo "FAIL [A6-${n}]: control ADR-${n} line 4 is '$line4' (expected 'Status: Accepted')"
    fail=1
  fi
done

# A7: the meta-ADR (0014) Feature field MUST name the parent feature, not
# the round suffix — the convention applies to the whole npm-distribution
# sub-spec, not just one round. Drafts carry `npm-distribution-spec-r3`;
# promotion strips the `-r3` suffix.
if [[ -n "$(ls docs/adr/0014-*.md 2>/dev/null | head -1)" ]]; then
  adr14=$(ls docs/adr/0014-*.md | head -1)
  feature_line="$(grep -m1 '^Feature:' "$adr14" || true)"
  if [[ "$feature_line" == "Feature: npm-distribution-spec" ]]; then
    echo "OK  [A7] ADR-0014 Feature line is 'npm-distribution-spec' (round suffix stripped)"
  else
    echo "FAIL [A7]: ADR-0014 Feature line is '$feature_line' (expected 'Feature: npm-distribution-spec')"
    fail=1
  fi
fi

if [[ "$fail" -eq 0 ]]; then
  echo "slice-9 (adrs) conformance: OK"
  exit 0
else
  echo "slice-9 (adrs) conformance: FAIL"
  exit 1
fi
