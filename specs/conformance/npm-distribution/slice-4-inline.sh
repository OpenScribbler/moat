#!/usr/bin/env bash
# Slice 4 inline conformance assertions.
#
# Slice 4 introduces no new domain logic; it rephrases the materialization-
# boundary intro prose to anchor the MUST at a precise point ("before any byte
# of the tarball is written outside the package manager's content cache") and
# names resolve / fetch / unpack as the operations a Conforming Client may
# refuse at. The inline assertions verify the new anchor language landed and
# the Round-1-specific phrasing it replaces is gone. This wrapper script
# exists so the ship-tdd-evidence hook can capture red/green metadata via
# ship-run-test; it does not introduce a new slice-N.sh in the spec-
# conformance series.

set -uo pipefail

repo_root="$(cd "$(dirname "$0")/../../.." && pwd)"
spec="$repo_root/specs/npm-distribution.md"
mirror="$repo_root/website/src/content/docs/spec/npm-distribution.md"

fail=0

assert_grep_zero() {
    local description="$1"
    local pattern="$2"
    local count
    count=$(grep -cF "$pattern" "$spec" || true)
    if [ "$count" -eq 0 ]; then
        echo "OK  $description"
    else
        echo "FAIL  $description (found $count occurrence(s))"
        fail=1
    fi
}

assert_grep_at_least_one() {
    local description="$1"
    local pattern="$2"
    if grep -F -q "$pattern" "$spec"; then
        echo "OK  $description"
    else
        echo "FAIL  $description (pattern: '$pattern')"
        fail=1
    fi
}

# A1 — cache-boundary anchor verbatim.
assert_grep_at_least_one \
    "spec contains the cache-boundary anchor verbatim" \
    "before any byte of the tarball is written outside the package manager's content cache"

# A2 — section names resolve, fetch, unpack as the operations a Conforming Client may refuse at.
section_re='## .*Materialization Boundary.*normative'
section="$(awk "/$section_re/{flag=1; next} flag && /^## /{flag=0} flag" "$spec" || true)"
if [ -z "$section" ]; then
    echo "FAIL  cannot locate '## ... Materialization Boundary ... (normative)' section to extract"
    fail=1
else
    for op in resolve fetch unpack; do
        if echo "$section" | grep -qE "\b$op\b"; then
            echo "OK  materialization-boundary section names operation '$op'"
        else
            echo "FAIL  materialization-boundary section does not name operation '$op'"
            fail=1
        fi
    done

    # A3 — section states that whichever sub-operation the Client refuses at,
    # no extracted bytes may land outside the cache.
    if echo "$section" | grep -qE 'no[[:space:]]+(extracted[[:space:]]+)?bytes.*(outside|land|written)|no[[:space:]]+bytes[[:space:]]+(escape|leave|land[[:space:]]+outside)'; then
        echo "OK  section states no extracted bytes may land outside the cache"
    else
        echo "FAIL  section does not state the no-bytes-outside-cache rule"
        fail=1
    fi
fi

# A4 — Round-1-specific phrasing 'into the install target' is superseded.
assert_grep_zero \
    "Round 1 phrasing 'into the install target' is gone" \
    "into the install target"

# A5 — mirror byte-identity.
diff <(sed '1,/^---$/d' "$mirror") "$spec" > /tmp/slice-4-mirror-diff.txt
diff_exit=$?
if [ "$diff_exit" -eq 0 ]; then
    echo "OK  website mirror byte-identical to spec body after stripping front-matter"
else
    echo "FAIL  website mirror diverges from spec (see /tmp/slice-4-mirror-diff.txt)"
    fail=1
fi

if [ "$fail" -eq 0 ]; then
    echo "Slice 4 inline conformance: PASS"
    exit 0
else
    echo "Slice 4 inline conformance: FAIL"
    exit 1
fi
