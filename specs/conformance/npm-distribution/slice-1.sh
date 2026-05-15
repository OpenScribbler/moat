#!/usr/bin/env bash
# Slice 1 conformance (Round 3): tarballContentRoot REQUIRED for cooperative
# Publishers, with the tarball-root default explicitly scoped to Registry-
# backfilled items (D1). Fixed exclusion list reframed as a two-layer
# composition: global (protocol-internal) plus per-channel additive (D5).
#
# Red before slice-1 impl; green after.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
mirror=website/src/content/docs/spec/npm-distribution.md
fail=0

if [[ ! -f "$spec" ]]; then
  echo "FAIL [pre]: $spec missing"
  echo "slice-1 conformance: FAIL"
  exit 1
fi

# A1 (D1): schema table row for moat.tarballContentRoot reads REQUIRED.
# Pinned to a single span anchored on the row's `|` table delimiters.
if grep -nE '^\| `moat\.tarballContentRoot` \| REQUIRED \|' "$spec" >/dev/null; then
  echo "OK  A1 tarballContentRoot row REQUIRED in pipe-table format"
else
  echo "FAIL A1 schema row '| \`moat.tarballContentRoot\` | REQUIRED |' not found"
  fail=1
fi

# A2 (D1): the row carries a backfill-caveat anchor naming the Registry-backfilled
# scope of the tarball-root default. Asserted on the same physical line as the row.
if awk -F'|' '/^\| `moat\.tarballContentRoot` \| REQUIRED \|/ { print $4 }' "$spec" \
   | grep -iE '(backfill|Registry-backfilled)' >/dev/null; then
  echo "OK  A2 backfill-caveat anchor present in tarballContentRoot row prose"
else
  echo "FAIL A2 backfill-caveat anchor missing from tarballContentRoot row prose"
  fail=1
fi

# A3 (D1): Default-mode prose names the backfill scope explicitly with the
# specific token combinations Round 3 introduces. The Round-2 prose mentioned
# "let backfill work" as informative rationale; Round 3 requires a normative
# scope marker — one of: "for Registry-backfilled items only", "scoped to
# Registry-backfilled", or "applies when a Registry backfills".
default_block="$(awk '/\*\*Default \(normative — MUST\):/,/\*\*Subdirectory mode/' "$spec")"
if [[ -z "$default_block" ]]; then
  echo "FAIL A3 Default-mode normative block not found at expected anchor"
  fail=1
elif echo "$default_block" | grep -iE '(for Registry-backfilled items only|scoped to Registry-backfilled|applies when a Registry backfills|Registry-backfilled npm-only items)' >/dev/null; then
  echo "OK  A3 Default-mode prose carries Round-3 scope marker"
else
  echo "FAIL A3 Default-mode block lacks Round-3 backfill-scope marker (looked for: 'for Registry-backfilled items only', 'scoped to Registry-backfilled', 'applies when a Registry backfills', 'Registry-backfilled npm-only items')"
  fail=1
fi

# A4 (D5): exclusion-list MUST is reframed as a two-layer composition.
# Anchored on the "Fixed exclusion list (normative — MUST)" block.
excl_block="$(awk '/\*\*Fixed exclusion list \(normative — MUST\):/,/\*\*Rationale/' "$spec")"
if [[ -z "$excl_block" ]]; then
  echo "FAIL A4 Fixed-exclusion-list block not found at expected anchor"
  fail=1
elif echo "$excl_block" | grep -iE '(two[ -]layer|global.*per-channel|per-channel.*global)' >/dev/null; then
  echo "OK  A4 two-layer exclusion-list framing present"
else
  echo "FAIL A4 two-layer (global + per-channel additive) framing absent from exclusion-list MUST"
  fail=1
fi

# A5 (D5): Publishers MUST NOT extend either layer (no-Publisher-extension rule).
if echo "$excl_block" | grep -E 'Publisher MUST NOT extend' >/dev/null; then
  echo "OK  A5 'Publisher MUST NOT extend' rule preserved"
else
  echo "FAIL A5 'Publisher MUST NOT extend' rule missing or moved outside exclusion-list block"
  fail=1
fi

# A6: website mirror parity for the rewritten lines.
if [[ -f "$mirror" ]]; then
  diff <(sed '1,/^---$/d' "$mirror") "$spec" >/tmp/slice-1-mirror-diff.txt
  if [[ $? -eq 0 ]]; then
    echo "OK  A6 website mirror byte-identical to spec body after stripping front-matter"
  else
    echo "FAIL A6 website mirror diverges from spec (see /tmp/slice-1-mirror-diff.txt)"
    fail=1
  fi
else
  echo "FAIL A6 website mirror missing: $mirror"
  fail=1
fi

# A7: lexicon.md §Content & Layout row for **Content Directory** acknowledges
# the REQUIRED-vs-default split. Scope the grep to that single table row.
if [[ -f lexicon.md ]]; then
  cd_row="$(grep -nE '^\| \*\*Content Directory\*\* \|' lexicon.md)"
  if [[ -z "$cd_row" ]]; then
    echo "FAIL A7 **Content Directory** row not found in lexicon.md"
    fail=1
  elif echo "$cd_row" | grep -iE '(REQUIRED.*cooperative|cooperative.*REQUIRED|REQUIRED.*for[[:space:]]+(npm|cooperative)|backfilled[[:space:]]+items|default.*backfill)' >/dev/null; then
    echo "OK  A7 lexicon **Content Directory** row acknowledges REQUIRED-vs-default split"
  else
    echo "FAIL A7 lexicon.md **Content Directory** row missing REQUIRED-vs-default cross-reference clause"
    fail=1
  fi
else
  echo "FAIL A7 lexicon.md missing"
  fail=1
fi

if [[ "$fail" -eq 0 ]]; then
  echo "slice-1 conformance: OK"
  exit 0
else
  echo "slice-1 conformance: FAIL"
  exit 1
fi
