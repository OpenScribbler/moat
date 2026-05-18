#!/usr/bin/env bash
# Slice 2 inline conformance assertions.
#
# Slice 2 introduces no new domain logic; the assertions verify the field-name
# rename moat.contentDirectory -> moat.tarballContentRoot landed atomically
# across the spec, the website mirror, the lexicon cross-reference, and the
# field-table Description column. This script wraps those inline assertions in
# a runnable artifact so the ship-tdd-evidence hook can capture red/green
# metadata via ship-run-test. It does not introduce a new slice-N.sh in the
# spec-conformance series (slice-6.sh, slice-7.sh, slice-8.sh remain the
# domain-logic scripts for Round 2).

set -uo pipefail

repo_root="$(cd "$(dirname "$0")/../../.." && pwd)"
spec="$repo_root/specs/npm-distribution.md"
mirror="$repo_root/website/src/content/docs/spec/npm-distribution.md"
lexicon="$repo_root/lexicon.md"

fail=0

assert_zero() {
    local description="$1"
    local actual="$2"
    if [ "$actual" -eq 0 ]; then
        echo "OK  $description"
    else
        echo "FAIL  $description  (got $actual, expected 0)"
        fail=1
    fi
}

assert_nonzero() {
    local description="$1"
    local actual="$2"
    if [ "$actual" -gt 0 ]; then
        echo "OK  $description"
    else
        echo "FAIL  $description  (got $actual, expected > 0)"
        fail=1
    fi
}

# A1 — spec body has no remaining moat.contentDirectory literal.
spec_legacy=$(grep -c 'moat\.contentDirectory' "$spec" || true)
assert_zero "spec/npm-distribution.md contains zero 'moat.contentDirectory' literals" "$spec_legacy"

# A2 — website mirror has no remaining moat.contentDirectory literal.
mirror_legacy=$(grep -c 'moat\.contentDirectory' "$mirror" || true)
assert_zero "website mirror contains zero 'moat.contentDirectory' literals" "$mirror_legacy"

# A3 — lexicon Content Directory entry references tarballContentRoot AND package.json.
lexicon_cd_entry=$(awk -F'|' '/\| \*\*Content Directory\*\*/{print}' "$lexicon" | head -1)
if echo "$lexicon_cd_entry" | grep -F 'tarballContentRoot' >/dev/null && echo "$lexicon_cd_entry" | grep -F 'package.json' >/dev/null; then
    echo "OK  lexicon Content Directory entry mentions both 'tarballContentRoot' and 'package.json'"
else
    echo "FAIL  lexicon Content Directory entry must reference 'tarballContentRoot' and 'package.json'"
    echo "       got entry: $lexicon_cd_entry"
    fail=1
fi

# A4 — field-table row for moat.tarballContentRoot exists and its Description column
# cross-references the lexicon (does not redefine the Content Directory concept inline).
table_row=$(grep -F '| `moat.tarballContentRoot`' "$spec" | head -1)
if [ -z "$table_row" ]; then
    echo "FAIL  spec field-table is missing a row for 'moat.tarballContentRoot'"
    fail=1
else
    echo "OK  spec field-table contains a row for 'moat.tarballContentRoot'"
    # Cross-reference to the lexicon. Accept either an explicit lexicon link
    # or a #content-directory section anchor referencing the canonical entry.
    if echo "$table_row" | grep -E '(lexicon\.md|#content-directory)' >/dev/null; then
        echo "OK  field-table row cross-references the lexicon Content Directory entry"
    else
        echo "FAIL  field-table row does not cross-reference the lexicon Content Directory entry"
        echo "       got row: $table_row"
        fail=1
    fi
fi

# A5 — mirror byte-identity holds after stripping Starlight front-matter.
diff <(sed '1,/^---$/d' "$mirror") "$spec" >/tmp/slice-2-mirror-diff.txt
diff_exit=$?
if [ "$diff_exit" -eq 0 ]; then
    echo "OK  website mirror byte-identical to spec body after stripping Starlight front-matter"
else
    echo "FAIL  website mirror diverges from spec body (see /tmp/slice-2-mirror-diff.txt)"
    fail=1
fi

if [ "$fail" -eq 0 ]; then
    echo "Slice 2 inline conformance: PASS"
    exit 0
else
    echo "Slice 2 inline conformance: FAIL"
    exit 1
fi
