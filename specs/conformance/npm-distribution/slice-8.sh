#!/usr/bin/env bash
# Slice 7 conformance: end-to-end npm Publisher reference workflow + cross-spec
# rider edits.
#
# This is the eighth conformance script in the spec-conformance series; the
# numbering is 1-indexed by ship plan position, not by slice number, because
# Slice 1 already shipped slice-1.sh and the lockstep updates in Slices 2/4/5/6
# used `-inline.sh` wrappers without consuming a slice-N.sh slot. Slice 7
# introduces a new spec-conformance script, so it takes the next free slot.
#
# Asserts:
# A1 — `reference/moat-npm-publisher.yml` exists.
# A2 — workflow declares the 7 canonical work-steps in order:
#       npm pack v1 → compute canonical hash → Sigstore sign →
#       push to Rekor → write log index back to package.json →
#       npm pack v2 → npm publish
# A3 — permissions: id-token: write AND contents: write.
# A4 — workflow uses sigstore/cosign-installer@<sha-or-tag>.
# A5 — on: covers release-tag push AND workflow_dispatch.
# A6 — moat-spec.md:9 contains literal `specs/npm-distribution.md`.
# A7 — .claude/rules/changelog.md:40 cites `specs/github/publisher-action.md`
#       and does NOT cite the pre-reorg path `specs/publisher-action.md`.
# A8 — two-pack canonical-hash stability: given a small fixture, npm pack v1
#       and npm pack v2 (after editing package.json with a publisherSigning
#       hint) produce tarballs whose unpacked Content Directories — minus the
#       root `package.json` per Slice 1's default rule — produce the same
#       canonical MOAT content hash.
# A9 — website mirror byte-identity diff exits 0.

set -uo pipefail

repo_root="$(cd "$(dirname "$0")/../../.." && pwd)"
yaml="$repo_root/reference/moat-npm-publisher.yml"
moat_spec="$repo_root/moat-spec.md"
changelog_rule="$repo_root/.claude/rules/changelog.md"
spec="$repo_root/specs/npm-distribution.md"
mirror="$repo_root/website/src/content/docs/spec/npm-distribution.md"

fail=0
ok() { echo "OK  $1"; }
no() { echo "FAIL  $1"; fail=1; }

# A1 — workflow file exists.
if [ -f "$yaml" ]; then
    ok "reference/moat-npm-publisher.yml exists"
else
    no "reference/moat-npm-publisher.yml is missing"
fi

# A2 — seven canonical work-steps appear in order. Each step is identified by
# a discriminating regex against `name:` lines under `steps:`. We collect the
# line number of the first match for each pattern, then verify the seven
# numbers are strictly increasing.
if [ ! -f "$yaml" ]; then
    no "cannot evaluate step ordering — workflow file missing"
else
    declare -a step_patterns=(
        'name:[[:space:]]+.*npm[[:space:]]+pack.*v1|name:[[:space:]]+.*npm[[:space:]]+pack[[:space:]]+\(v1'
        'name:[[:space:]]+.*[Cc]ompute.*[Cc]anonical.*hash|name:[[:space:]]+.*[Cc]ompute.*MOAT.*hash'
        'name:[[:space:]]+.*[Ss]ign.*[Cc]anonical.*[Pp]ayload|name:[[:space:]]+.*[Ss]igstore.*sign|name:[[:space:]]+.*cosign[[:space:]]+sign'
        'name:[[:space:]]+.*[Pp]ush.*Rekor|name:[[:space:]]+.*Rekor.*log[[:space:]]+index|name:[[:space:]]+.*[Cc]apture.*Rekor'
        'name:[[:space:]]+.*[Ww]rite.*rekorLogIndex|name:[[:space:]]+.*[Ww]rite.*log[[:space:]]+index.*package\.json|name:[[:space:]]+.*[Ww]rite.*log[[:space:]]+index[[:space:]]+back'
        'name:[[:space:]]+.*npm[[:space:]]+pack.*v2|name:[[:space:]]+.*npm[[:space:]]+pack[[:space:]]+\(v2'
        'name:[[:space:]]+.*npm[[:space:]]+publish'
    )
    declare -a step_labels=(
        "step 1 (npm pack v1)"
        "step 2 (compute canonical hash)"
        "step 3 (Sigstore sign)"
        "step 4 (push to Rekor)"
        "step 5 (write log index back)"
        "step 6 (npm pack v2)"
        "step 7 (npm publish)"
    )
    declare -a line_nums=()
    last_line=0
    ordering_ok=1
    for i in "${!step_patterns[@]}"; do
        pat="${step_patterns[$i]}"
        label="${step_labels[$i]}"
        line_no=$(grep -nE "$pat" "$yaml" | awk -F: '$1 > '"$last_line"' { print $1; exit }')
        if [ -z "$line_no" ]; then
            no "$label not found (or out of order) in $yaml"
            ordering_ok=0
        else
            line_nums+=("$line_no")
            last_line="$line_no"
        fi
    done
    if [ "$ordering_ok" -eq 1 ] && [ "${#line_nums[@]}" -eq 7 ]; then
        ok "all 7 canonical work-steps appear in order (lines ${line_nums[*]})"
    fi
fi

# A3 — permissions: id-token: write AND contents: write.
if [ -f "$yaml" ]; then
    if grep -qE '^\s*id-token:\s*write' "$yaml"; then
        ok "permissions: id-token: write"
    else
        no "permissions: missing 'id-token: write'"
    fi
    if grep -qE '^\s*contents:\s*write' "$yaml"; then
        ok "permissions: contents: write"
    else
        no "permissions: missing 'contents: write'"
    fi
fi

# A4 — workflow uses sigstore/cosign-installer.
if [ -f "$yaml" ]; then
    if grep -qE 'uses:[[:space:]]+sigstore/cosign-installer@' "$yaml"; then
        ok "workflow uses sigstore/cosign-installer@<ref>"
    else
        no "workflow does not use sigstore/cosign-installer@<ref>"
    fi
fi

# A5 — on: covers release-tag push AND workflow_dispatch.
if [ -f "$yaml" ]; then
    on_block=$(awk '/^on:/{flag=1; next} flag && /^[a-zA-Z]/{flag=0} flag' "$yaml")
    if echo "$on_block" | grep -qE 'tags:'; then
        ok "on: covers release-tag push (tags: present)"
    else
        no "on: missing 'tags:' (release-tag push)"
    fi
    if echo "$on_block" | grep -qE 'workflow_dispatch'; then
        ok "on: covers workflow_dispatch"
    else
        no "on: missing 'workflow_dispatch'"
    fi
fi

# A6 — moat-spec.md:9 cites specs/npm-distribution.md.
line9="$(sed -n '9p' "$moat_spec")"
if echo "$line9" | grep -qF 'specs/npm-distribution.md'; then
    ok "moat-spec.md:9 cites specs/npm-distribution.md"
else
    no "moat-spec.md:9 does not cite specs/npm-distribution.md (line 9: $line9)"
fi

# A7 — .claude/rules/changelog.md:40 cites the post-reorg path and not the
# pre-reorg path.
line40="$(sed -n '40p' "$changelog_rule")"
if echo "$line40" | grep -qF 'specs/github/publisher-action.md'; then
    ok ".claude/rules/changelog.md:40 cites specs/github/publisher-action.md"
else
    no ".claude/rules/changelog.md:40 does not cite specs/github/publisher-action.md (line 40: $line40)"
fi
if echo "$line40" | grep -qE '(^|[^/])specs/publisher-action\.md'; then
    no ".claude/rules/changelog.md:40 still cites pre-reorg path 'specs/publisher-action.md'"
else
    ok ".claude/rules/changelog.md:40 does not cite pre-reorg path"
fi

# A8 — two-pack canonical-hash stability.
two_pack_check() {
    if ! command -v npm >/dev/null 2>&1; then
        no "npm not on PATH — cannot run two-pack stability check"
        return
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        no "python3 not on PATH — cannot run two-pack stability check"
        return
    fi
    local fixture
    fixture=$(mktemp -d -t moat-slice7-fixture.XXXXXXXX)
    trap 'rm -rf "$fixture"' RETURN

    # Build a minimal Content Item: a package.json and a small skill/ tree.
    cat > "$fixture/package.json" <<EOF
{
  "name": "@example/slice7-fixture",
  "version": "0.1.0",
  "files": ["skill"]
}
EOF
    mkdir -p "$fixture/skill"
    cat > "$fixture/skill/SKILL.md" <<'EOF'
# Slice 7 fixture

Two-pack stability test fixture.
EOF
    cat > "$fixture/skill/notes.md" <<'EOF'
Stable bytes that should produce the same canonical hash across both packs.
EOF

    # Pack v1.
    local pack_dir_v1
    pack_dir_v1=$(mktemp -d -t moat-slice7-v1.XXXXXXXX)
    ( cd "$fixture" && npm pack --pack-destination "$pack_dir_v1" --silent >/dev/null 2>&1 )
    local tarball_v1
    tarball_v1=$(ls -1 "$pack_dir_v1"/*.tgz 2>/dev/null | head -1)
    if [ -z "$tarball_v1" ] || [ ! -f "$tarball_v1" ]; then
        no "two-pack: npm pack v1 produced no tarball"
        rm -rf "$pack_dir_v1"
        return
    fi

    # Edit package.json to add the publisherSigning rekorLogIndex hint.
    cat > "$fixture/package.json" <<EOF
{
  "name": "@example/slice7-fixture",
  "version": "0.1.0",
  "files": ["skill"],
  "moat": {
    "publisherSigning": {
      "issuer": "https://token.actions.githubusercontent.com",
      "subject": "https://github.com/example/slice7-fixture/.github/workflows/moat-npm-publisher.yml@refs/heads/main",
      "rekorLogIndex": 12345678
    }
  }
}
EOF

    # Pack v2.
    local pack_dir_v2
    pack_dir_v2=$(mktemp -d -t moat-slice7-v2.XXXXXXXX)
    ( cd "$fixture" && npm pack --pack-destination "$pack_dir_v2" --silent >/dev/null 2>&1 )
    local tarball_v2
    tarball_v2=$(ls -1 "$pack_dir_v2"/*.tgz 2>/dev/null | head -1)
    if [ -z "$tarball_v2" ] || [ ! -f "$tarball_v2" ]; then
        no "two-pack: npm pack v2 produced no tarball"
        rm -rf "$pack_dir_v1" "$pack_dir_v2"
        return
    fi

    # Extract each tarball and apply Slice 1's default Content Directory rule
    # (root package.json excluded) before computing the canonical hash.
    compute_hash() {
        local tarball="$1"
        local extract
        extract=$(mktemp -d -t moat-slice7-ext.XXXXXXXX)
        tar -xzf "$tarball" -C "$extract"
        # npm pack convention: tarball contents live under package/.
        local content_dir="$extract/package"
        if [ ! -d "$content_dir" ]; then
            echo "EXTRACTION_FAILED"
            rm -rf "$extract"
            return
        fi
        rm -f "$content_dir/package.json"
        python3 "$repo_root/reference/moat_hash.py" "$content_dir" 2>/dev/null
        rm -rf "$extract"
    }
    local hash_v1 hash_v2
    hash_v1=$(compute_hash "$tarball_v1")
    hash_v2=$(compute_hash "$tarball_v2")
    rm -rf "$pack_dir_v1" "$pack_dir_v2"

    if [ -z "$hash_v1" ] || [ -z "$hash_v2" ] || [ "$hash_v1" = "EXTRACTION_FAILED" ] || [ "$hash_v2" = "EXTRACTION_FAILED" ]; then
        no "two-pack: hash computation failed (v1=$hash_v1, v2=$hash_v2)"
        return
    fi

    if [ "$hash_v1" = "$hash_v2" ]; then
        ok "two-pack canonical-hash stability: v1 == v2 ($hash_v1)"
    else
        no "two-pack canonical-hash stability: v1 != v2 (v1=$hash_v1, v2=$hash_v2)"
    fi
}
two_pack_check

# A9 — website mirror byte-identity.
diff <(sed '1,/^---$/d' "$mirror") "$spec" > /tmp/slice-8-mirror-diff.txt
if [ "$?" -eq 0 ]; then
    ok "website mirror byte-identical to spec body after stripping front-matter"
else
    no "website mirror diverges from spec (see /tmp/slice-8-mirror-diff.txt)"
fi

if [ "$fail" -eq 0 ]; then
    echo "Slice 7 (slice-8.sh) conformance: PASS"
    exit 0
else
    echo "Slice 7 (slice-8.sh) conformance: FAIL"
    exit 1
fi
