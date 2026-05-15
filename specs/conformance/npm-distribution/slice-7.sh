#!/usr/bin/env bash
# Slice 3 conformance (Round 3): hard revocation without operator override.
# D3 deletes the §MOAT_ALLOW_REVOKED Operator Override block wholesale and
# rewrites the §Revocation MUSTs to drop the per-hash escape hatch; the
# resolve-time log entry now MUST identify the revocation source (lockfile
# vs Registry Manifest). ADR-0007 is flipped to `Superseded by ADR-0010`
# and ADR-0010 is added with the matching `Supersedes: ADR-0007` header.
#
# Conformance error codes asserted by this script (per §Conformance in
# specs/npm-distribution.md): NPM-REV-05 (resolve-time log MUST name
# `source`), NPM-REV-06 (Conforming Client MUST NOT honor a per-hash
# escape hatch), NPM-REV-07 (override env var / flag / config entry MUST
# be treated as if absent).
#
# This script remains named `slice-7.sh` because it succeeds the Round-2
# slice-7.sh that previously hardened the override; rewriting it in place
# preserves the conformance file map.
#
# Red before slice-3 impl; green after.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
mirror=website/src/content/docs/spec/npm-distribution.md
adr7=$(ls docs/adr/0007-*.md 2>/dev/null | head -1)
adr10=$(ls docs/adr/0010-*.md 2>/dev/null | head -1)
fail=0

if [[ ! -f "$spec" ]]; then
  echo "FAIL [pre]: $spec missing"
  echo "slice-3 conformance: FAIL"
  exit 1
fi

# A1: `MOAT_ALLOW_REVOKED` is absent from the spec body wholesale (D3).
if [[ $(grep -c MOAT_ALLOW_REVOKED "$spec") -eq 0 ]]; then
  echo "OK  A1 MOAT_ALLOW_REVOKED absent from $spec"
else
  echo "FAIL A1 MOAT_ALLOW_REVOKED still present in $spec ($(grep -c MOAT_ALLOW_REVOKED "$spec") matches)"
  fail=1
fi

# A2: the §MOAT_ALLOW_REVOKED Operator Override section heading is gone.
if grep -nE '^## .*MOAT_ALLOW_REVOKED' "$spec" >/dev/null; then
  echo "FAIL A2 §MOAT_ALLOW_REVOKED section heading still present"
  fail=1
else
  echo "OK  A2 §MOAT_ALLOW_REVOKED section heading removed"
fi

# A3: §Revocation block no longer offers an operator-acknowledged escape hatch.
# The Round-2 block contained the literal "Operator-acknowledged proceed" MAY
# clause; that label MUST be gone after D3.
rev_block="$(awk '/^## Revocation at the Materialization Boundary/{flag=1; next} flag && /^## /{flag=0} flag' "$spec")"
if [[ -z "$rev_block" ]]; then
  echo "FAIL A3 §Revocation at the Materialization Boundary section not found"
  fail=1
else
  if echo "$rev_block" | grep -iE 'operator[- ]acknowledged[[:space:]]+proceed' >/dev/null; then
    echo "FAIL A3 'Operator-acknowledged proceed' clause still present in §Revocation"
    fail=1
  else
    echo "OK  A3 'Operator-acknowledged proceed' clause removed from §Revocation"
  fi

  # A4: §Revocation's resolve-time log entry MUST name the `source` field
  # (lockfile vs Registry Manifest) as a structured field.
  if echo "$rev_block" | grep -iE '(\bsource\b[^.]*(lockfile|Registry[[:space:]]+Manifest)|(lockfile|Registry[[:space:]]+Manifest)[^.]*\bsource\b)' >/dev/null; then
    echo "OK  A4 resolve-time log entry names the structured 'source' field (lockfile vs Registry Manifest)"
  else
    echo "FAIL A4 §Revocation does not name the structured 'source' field for the resolve-time log entry"
    fail=1
  fi

  # A5: §Revocation MUST keep a structured-log MUST anchored to revocation refusal.
  if echo "$rev_block" | grep -iE 'MUST[[:space:]]+emit[[:space:]]+a[[:space:]]+structured[[:space:]]+log[[:space:]]+entry' >/dev/null; then
    echo "OK  A5 structured-log MUST preserved in §Revocation"
  else
    echo "FAIL A5 §Revocation lacks a 'MUST emit a structured log entry' clause"
    fail=1
  fi
fi

# A6: ADR-0007 has `Status: Superseded by ADR-0010` on line 4.
if [[ -z "$adr7" ]]; then
  echo "FAIL A6 ADR-0007 file not found under docs/adr/"
  fail=1
else
  status_line="$(sed -n '4p' "$adr7")"
  if [[ "$status_line" == "Status: Superseded by ADR-0010" ]]; then
    echo "OK  A6 ADR-0007 line 4 reads 'Status: Superseded by ADR-0010'"
  else
    echo "FAIL A6 ADR-0007 line 4 is '$status_line' (expected 'Status: Superseded by ADR-0010')"
    fail=1
  fi
fi

# A7: ADR-0010 exists and carries the `Supersedes: ADR-0007` header.
if [[ -z "$adr10" ]]; then
  echo "FAIL A7 ADR-0010 file not found under docs/adr/"
  fail=1
else
  if grep -nE '^Supersedes:[[:space:]]+ADR-0007\b' "$adr10" >/dev/null; then
    echo "OK  A7 ADR-0010 carries 'Supersedes: ADR-0007' header"
  else
    echo "FAIL A7 ADR-0010 missing 'Supersedes: ADR-0007' header"
    fail=1
  fi
fi

# A8: website mirror parity after stripping frontmatter.
if [[ -f "$mirror" ]]; then
  diff <(sed '1,/^---$/d' "$mirror") "$spec" >/tmp/slice-7-mirror-diff.txt
  if [[ $? -eq 0 ]]; then
    echo "OK  A8 website mirror byte-identical to spec body after stripping front-matter"
  else
    echo "FAIL A8 website mirror diverges from spec (see /tmp/slice-7-mirror-diff.txt)"
    fail=1
  fi
else
  echo "FAIL A8 website mirror missing: $mirror"
  fail=1
fi

if [[ "$fail" -eq 0 ]]; then
  echo "slice-3 conformance: OK"
  exit 0
else
  echo "slice-3 conformance: FAIL"
  exit 1
fi
