#!/usr/bin/env bash
# Slice 5 inline conformance assertions.
#
# Slice 5 relocates Publisher signing identity out of `attestations[].bundle`
# into a top-level `publisherSigning` block with REQUIRED `issuer`, REQUIRED
# `subject`, OPTIONAL `rekorLogIndex`. The Registry-role `attestations[]` row
# remains. The sub-spec body cites `moat-spec.md`'s `signing_profile`. A new
# `## Publisher Verification (normative)` subsection enumerates the two
# verification paths (rekorLogIndex present vs absent).
#
# This wrapper exists so the ship-tdd-evidence hook can capture red/green
# metadata via ship-run-test; it does not introduce a new slice-N.sh in the
# spec-conformance series.

set -uo pipefail

repo_root="$(cd "$(dirname "$0")/../../.." && pwd)"
spec="$repo_root/specs/npm-distribution.md"
mirror="$repo_root/website/src/content/docs/spec/npm-distribution.md"

fail=0

ok() { echo "OK  $1"; }
no() { echo "FAIL  $1"; fail=1; }

# A1 — publisherSigning.issuer row is REQUIRED.
if grep -nE '^\|.*`publisherSigning\.issuer`.*\|.*REQUIRED.*\|' "$spec" >/dev/null; then
    ok "field-table row 'publisherSigning.issuer' marked REQUIRED"
else
    no "field-table row 'publisherSigning.issuer' is missing or not REQUIRED"
fi

# A2 — publisherSigning.subject row is REQUIRED.
if grep -nE '^\|.*`publisherSigning\.subject`.*\|.*REQUIRED.*\|' "$spec" >/dev/null; then
    ok "field-table row 'publisherSigning.subject' marked REQUIRED"
else
    no "field-table row 'publisherSigning.subject' is missing or not REQUIRED"
fi

# A3 — publisherSigning.rekorLogIndex row is OPTIONAL.
if grep -nE '^\|.*`publisherSigning\.rekorLogIndex`.*\|.*OPTIONAL.*\|' "$spec" >/dev/null; then
    ok "field-table row 'publisherSigning.rekorLogIndex' marked OPTIONAL"
else
    no "field-table row 'publisherSigning.rekorLogIndex' is missing or not OPTIONAL"
fi

# A4 — Round 1 attestations[].bundle Publisher-role row does NOT appear.
# After Slice 5 the bundle row only carries the Registry role (the Publisher
# role's identity moved to publisherSigning). The most reliable check is that
# no field-table row mentions the Publisher role together with the bundle
# field; instead we assert the Round 1 row description is gone by checking the
# total count of attestations[].bundle rows and that no row description mentions
# 'publisher' alongside the bundle field.
bundle_rows=$(grep -cE '^\|.*`moat\.attestations\[\]\.bundle`.*\|' "$spec" || true)
if [ "$bundle_rows" -le 1 ]; then
    ok "at most one attestations[].bundle field-table row remains (Registry-only)"
else
    no "expected at most 1 attestations[].bundle row, found $bundle_rows"
fi

# A4b — verify the surviving bundle row's description scopes to Registry only,
# not to Publisher. The Round 1 description text covered both roles.
if grep -nE '^\|.*`moat\.attestations\[\]\.bundle`.*\|.*[Pp]ublisher' "$spec" >/dev/null; then
    no "attestations[].bundle field-table row still mentions Publisher (should be Registry-only)"
else
    ok "attestations[].bundle field-table row does not mention Publisher"
fi

# A5 — Registry-role attestations[] row remains (attestations[].role is still defined).
if grep -nE '^\|.*`moat\.attestations\[\]\.role`' "$spec" >/dev/null; then
    ok "Registry-role attestations[].role field-table row remains"
else
    no "attestations[].role field-table row is missing"
fi

# A6 — sub-spec body cites moat-spec.md's signing_profile (anchor or section ref).
if grep -nE 'signing_profile' "$spec" >/dev/null; then
    ok "sub-spec cites 'signing_profile' (moat-spec.md)"
else
    no "sub-spec does not cite 'signing_profile'"
fi

# A7 — Publisher Verification (normative) subsection exists.
if grep -nE '^## .*Publisher Verification.*normative' "$spec" >/dev/null; then
    ok "## Publisher Verification (normative) subsection exists"
else
    no "no '## Publisher Verification (normative)' subsection"
fi

# A8 — Publisher Verification section enumerates BOTH verification paths.
verif_section="$(awk '/^## .*Publisher Verification.*normative/{flag=1; next} flag && /^## /{flag=0} flag' "$spec" || true)"
if [ -z "$verif_section" ]; then
    no "Publisher Verification section is empty / not extractable"
else
    if echo "$verif_section" | grep -qE 'rekorLogIndex.*(present|set|provided|hint)|fetch[[:space:]]+by[[:space:]]+(log[ -]?)?index'; then
        ok "Publisher Verification covers the rekorLogIndex-present path"
    else
        no "Publisher Verification does not cover the rekorLogIndex-present path"
    fi
    if echo "$verif_section" | grep -qE '(rekorLogIndex.*(absent|missing|omit)|query.*Rekor.*content[ _]?hash|Rekor.*query.*content[ _]?hash|search[[:space:]]+Rekor.*Content[[:space:]]+Hash)'; then
        ok "Publisher Verification covers the rekorLogIndex-absent path"
    else
        no "Publisher Verification does not cover the rekorLogIndex-absent path"
    fi
    if echo "$verif_section" | grep -qE 'issuer.*subject|subject.*issuer|\{issuer,[[:space:]]*subject\}|\{subject,[[:space:]]*issuer\}'; then
        ok "Publisher Verification names the {issuer, subject} identity match"
    else
        no "Publisher Verification does not name the {issuer, subject} identity match"
    fi
fi

# A9 — mirror byte-identity.
diff <(sed '1,/^---$/d' "$mirror") "$spec" > /tmp/slice-5-mirror-diff.txt
if [ "$?" -eq 0 ]; then
    ok "website mirror byte-identical to spec body after stripping front-matter"
else
    no "website mirror diverges from spec (see /tmp/slice-5-mirror-diff.txt)"
fi

if [ "$fail" -eq 0 ]; then
    echo "Slice 5 inline conformance: PASS"
    exit 0
else
    echo "Slice 5 inline conformance: FAIL"
    exit 1
fi
