#!/usr/bin/env bash
# Slice 6 inline conformance assertions.
#
# Slice 6 introduces a four-state (npm provenance × MOAT attestation)
# disagreement table inside the `## npm Provenance` section, with columns
# (npm provenance, MOAT attestation, Conforming Client display, Trust Tier
# impact) and four data rows: both-present, MOAT-only, provenance-only,
# neither. The orthogonality statement already lives in the section; the
# new artifact is the table.
#
# This wrapper script exists so the ship-tdd-evidence hook can capture
# red/green metadata via ship-run-test; it does not introduce a new
# slice-N.sh in the spec-conformance series.

set -uo pipefail

repo_root="$(cd "$(dirname "$0")/../../.." && pwd)"
spec="$repo_root/specs/npm-distribution.md"
mirror="$repo_root/website/src/content/docs/spec/npm-distribution.md"

fail=0

ok() { echo "OK  $1"; }
no() { echo "FAIL  $1"; fail=1; }

# Extract the npm Provenance section body for downstream assertions.
section="$(awk '/^## npm Provenance/{flag=1; next} flag && /^## /{flag=0} flag' "$spec" || true)"
if [ -z "$section" ]; then
    no "cannot locate '## npm Provenance' section"
    echo "Slice 6 inline conformance: FAIL"
    exit 1
fi

# A1 — section contains a pipe table with the four expected column headers.
header_re='\|[[:space:]]*npm provenance[[:space:]]*\|[[:space:]]*MOAT attestation[[:space:]]*\|[[:space:]]*Conforming Client display[[:space:]]*\|[[:space:]]*Trust Tier impact[[:space:]]*\|'
if echo "$section" | grep -qE "$header_re"; then
    ok "table header names columns (npm provenance, MOAT attestation, Conforming Client display, Trust Tier impact)"
else
    no "table header missing one or more required columns"
fi

# A2 — section contains a Markdown pipe-table separator row immediately after
# the header (e.g. |---|---|---|---|).
if echo "$section" | grep -qE '^\|[[:space:]]*-+[[:space:]]*\|[[:space:]]*-+[[:space:]]*\|[[:space:]]*-+[[:space:]]*\|[[:space:]]*-+[[:space:]]*\|[[:space:]]*$'; then
    ok "table separator row present (4 columns)"
else
    no "table separator row missing or wrong column count"
fi

# A3 — at least four data rows after the separator. Count pipe-rows that are
# neither the header row nor the separator row, and that contain at least
# three internal pipes (so ≥4 columns).
data_rows=$(echo "$section" | awk '
  /\| *npm provenance *\| *MOAT attestation *\| *Conforming Client display *\| *Trust Tier impact *\|/ { in_table=1; next }
  in_table && /^\| *-+ *\| *-+ *\| *-+ *\| *-+ *\| *$/ { next }
  in_table && /^\|.*\|.*\|.*\|.*\|/ { count++; next }
  in_table && !/^\|/ { in_table=0 }
  END { print count+0 }
')
if [ "$data_rows" -ge 4 ]; then
    ok "table has at least 4 data rows (found $data_rows)"
else
    no "table has fewer than 4 data rows (found $data_rows)"
fi

# A4 — the four data rows cover the four states. We look for indicative tokens
# in the section body: "both", "MOAT-only" / "MOAT only", "provenance-only" /
# "provenance only", "neither". Each is asserted as a separate OK so a partial
# table fails on the missing state(s) specifically.
for token_re in '[Bb]oth[[:space:]]+present|[Bb]oth[[:space:]]*\|' \
                'MOAT[- ][Oo]nly|[Oo]nly[[:space:]]+MOAT|MOAT[[:space:]]+attestation[[:space:]]+only' \
                '[Pp]rovenance[- ][Oo]nly|[Oo]nly[[:space:]]+npm[[:space:]]+provenance|npm[[:space:]]+provenance[[:space:]]+only' \
                '[Nn]either|[Nn]one[[:space:]]+present'; do
    label=$(echo "$token_re" | head -c 40)
    if echo "$section" | grep -qE "$token_re"; then
        ok "table covers state matching /$label/"
    else
        no "table missing state matching /$token_re/"
    fi
done

# A5 — the orthogonality statement remains in the section. Round 2 keeps the
# Round 1 sentence; Slice 6 only adds the table. Case-insensitive because the
# Round 1 prose capitalizes the word at the start of the bold-label paragraph.
if echo "$section" | grep -qiE 'orthogonal'; then
    ok "section retains the orthogonality statement"
else
    no "section no longer states the orthogonality between npm provenance and MOAT Trust Tier"
fi

# A6 — mirror byte-identity.
diff <(sed '1,/^---$/d' "$mirror") "$spec" > /tmp/slice-6-mirror-diff.txt
if [ "$?" -eq 0 ]; then
    ok "website mirror byte-identical to spec body after stripping front-matter"
else
    no "website mirror diverges from spec (see /tmp/slice-6-mirror-diff.txt)"
fi

if [ "$fail" -eq 0 ]; then
    echo "Slice 6 inline conformance: PASS"
    exit 0
else
    echo "Slice 6 inline conformance: FAIL"
    exit 1
fi
