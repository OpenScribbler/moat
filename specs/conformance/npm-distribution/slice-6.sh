#!/usr/bin/env bash
# Slice 6 conformance (D7 + D8 — Round 3): npm Provenance table reduced to
# 2 columns (state | Trust Tier impact); no MUST or MUST NOT inside table
# cells; the row-1 MUST NOT ("Client MUST NOT infer one signal from the
# other") and the row-3 MUST ("the Client MUST display [Unsigned]") appear
# as prose under the table, not inside cells; resolve-time refusal log MUST
# names the structured `source` field (which authority issued the
# revocation) with values `lockfile` and `registry_manifest` per D7.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
fail=0

if [[ ! -f "$spec" ]]; then
  echo "FAIL [pre]: $spec missing"
  echo "slice-6 conformance: FAIL"
  exit 1
fi

# Capture the §npm Provenance section body. The flag-toggle awk pattern
# skips the start heading line and clears on the next `## ` heading, so
# `prov_block` is just the body of the npm Provenance section — table
# rows, separator, and surrounding prose.
prov_block="$(awk '/^## npm Provenance \(informative\)/{flag=1; next} flag && /^## /{flag=0} flag' "$spec")"

# A1 (D8): the npm Provenance section contains a Markdown pipe table whose
# header row is exactly 2-column. We locate the header by finding the first
# pipe-row inside the section that is NOT a separator (`|---|`). Counting
# internal pipe separators on the stripped header gives (cells - 1); the
# header MUST have exactly 1 internal pipe (i.e. 2 cells).
if [[ -z "$prov_block" ]]; then
  echo "FAIL [A1]: §npm Provenance (informative) section not found"
  fail=1
else
  header="$(echo "$prov_block" | grep -m1 -E '^\|' | grep -vE '^\|[[:space:]]*-+' || true)"
  if [[ -z "$header" ]]; then
    echo "FAIL [A1]: no Markdown pipe-table header line found inside §npm Provenance"
    fail=1
  else
    stripped="${header#|}"
    stripped="${stripped%|}"
    n_seps="$(echo "$stripped" | tr -cd '|' | wc -c)"
    n_cells=$((n_seps + 1))
    if [[ "$n_cells" -ne 2 ]]; then
      echo "FAIL [A1]: expected 2-column table header inside §npm Provenance, found $n_cells columns:"
      echo "  $header"
      fail=1
    else
      echo "OK  [A1] npm Provenance table header is 2-column"
    fi
  fi
fi

# A2 (D8): the second column of the npm Provenance table header MUST contain
# the literal phrase 'Trust Tier impact'. The first column MUST contain the
# word 'state' (any casing, with or without a qualifier like "Signal state").
# This anchors the table's interpretation to the canonical tier-effect axis.
if [[ -n "$prov_block" ]]; then
  header="$(echo "$prov_block" | grep -m1 -E '^\|' | grep -vE '^\|[[:space:]]*-+' || true)"
  if [[ -n "$header" ]]; then
    if echo "$header" | grep -iqE '\bstate\b' \
       && echo "$header" | grep -qF 'Trust Tier impact'; then
      echo "OK  [A2] npm Provenance table header pairs '...state...' with 'Trust Tier impact'"
    else
      echo "FAIL [A2]: npm Provenance table header does not pair 'state' with 'Trust Tier impact':"
      echo "  $header"
      fail=1
    fi
  fi
fi

# A3 (D8): no MUST / MUST NOT / SHALL appears inside any cell of the npm
# Provenance table. We extract every pipe-row line in the section (excluding
# the separator) and grep for normative keywords. Tables are display rules;
# normative MUSTs belong in prose so a future-spec author cannot bury a
# requirement inside a cell where the cell-position renders it easy to miss.
if [[ -n "$prov_block" ]]; then
  table_rows="$(echo "$prov_block" | grep -E '^\|' | grep -vE '^\|[[:space:]]*-+' || true)"
  if [[ -n "$table_rows" ]] && echo "$table_rows" | grep -qE '\b(MUST|MUST NOT|SHALL|SHALL NOT)\b'; then
    bad="$(echo "$table_rows" | grep -nE '\b(MUST|MUST NOT|SHALL|SHALL NOT)\b' || true)"
    echo "FAIL [A3]: normative keyword (MUST / MUST NOT / SHALL) found inside npm Provenance table cells:"
    echo "$bad"
    fail=1
  else
    echo "OK  [A3] no MUST / MUST NOT / SHALL inside npm Provenance table cells"
  fi
fi

# A4 (D8): the row-1 MUST NOT (Client MUST NOT infer one signal from the
# other) appears as prose UNDER the table — i.e. on a non-table line that
# follows the last table row inside §npm Provenance. The awk one-liner
# records every line and the line number of the last `|`-row, then prints
# everything after it.
if [[ -n "$prov_block" ]]; then
  post_table="$(echo "$prov_block" | awk '
    { lines[NR]=$0 }
    /^\|/ { last_table=NR }
    END {
      for (i=last_table+1; i<=NR; i++) print lines[i]
    }')"
  if [[ -z "$post_table" ]]; then
    echo "FAIL [A4]: no prose found after the npm Provenance table"
    fail=1
  elif echo "$post_table" | grep -qE 'MUST NOT.*(infer|signal)'; then
    echo "OK  [A4] row-1 MUST NOT (Client MUST NOT infer one signal from the other) appears as prose under the table"
  else
    echo "FAIL [A4]: row-1 MUST NOT (Client MUST NOT infer one signal from the other) missing from prose under the npm Provenance table"
    fail=1
  fi
fi

# A5 (D8): the row-3 MUST (Client MUST display the package's MOAT Trust Tier
# as Unsigned when only npm provenance is present) appears as prose under
# the table.
if [[ -n "$prov_block" ]]; then
  post_table="$(echo "$prov_block" | awk '
    { lines[NR]=$0 }
    /^\|/ { last_table=NR }
    END {
      for (i=last_table+1; i<=NR; i++) print lines[i]
    }')"
  if echo "$post_table" | grep -qE 'MUST display.*Unsigned'; then
    echo "OK  [A5] row-3 MUST (Client MUST display ... Unsigned) appears as prose under the table"
  else
    echo "FAIL [A5]: row-3 MUST (Client MUST display ... Unsigned) missing from prose under the npm Provenance table"
    fail=1
  fi
fi

# A6 (D7): the resolve-time refusal log MUST in §Revocation at the
# Materialization Boundary names the structured `source` field with the
# literal values `lockfile` and `registry_manifest`. This surfaces WHICH
# authority issued the revocation so an operator reading the log can route
# their correction to the right place (lockfile vs Registry Manifest).
rev_block="$(awk '/^## Revocation at the Materialization Boundary/{flag=1; next} flag && /^## /{flag=0} flag' "$spec")"
if [[ -z "$rev_block" ]]; then
  echo "FAIL [A6]: §Revocation at the Materialization Boundary section not found"
  fail=1
else
  if echo "$rev_block" | grep -qE 'Resolve-time logging.+MUST' \
     && echo "$rev_block" | grep -qF '`source`' \
     && echo "$rev_block" | grep -qF '`lockfile`' \
     && echo "$rev_block" | grep -qF '`registry_manifest`'; then
    echo "OK  [A6] resolve-time logging MUST names structured \`source\` field with values \`lockfile\` and \`registry_manifest\`"
  else
    echo "FAIL [A6]: resolve-time logging MUST does not name the structured \`source\` field with values \`lockfile\` and \`registry_manifest\`"
    fail=1
  fi
fi

# A7 (D8): website mirror parity — mirror's first H1 line matches the
# canonical spec's first H1. Regression guard against forgotten mirror sync.
mirror=website/src/content/docs/spec/npm-distribution.md
if [[ ! -f "$mirror" ]]; then
  echo "FAIL [A7]: $mirror does not exist"
  fail=1
else
  mirror_h1="$(grep -m1 '^# ' "$mirror" || true)"
  canon_h1="$(grep -m1 '^# ' "$spec" || true)"
  if [[ "$mirror_h1" == "$canon_h1" && -n "$mirror_h1" ]]; then
    echo "OK  [A7] mirror first H1 matches canonical"
  else
    echo "FAIL [A7]: mirror H1 does not match canonical:"
    echo "  mirror:    $mirror_h1"
    echo "  canonical: $canon_h1"
    fail=1
  fi
fi

if [[ "$fail" -ne 0 ]]; then
  echo "slice-6 conformance: FAIL"
  exit 1
fi
echo "slice-6 conformance: OK"
exit 0
