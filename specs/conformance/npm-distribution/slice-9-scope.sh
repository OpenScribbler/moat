#!/usr/bin/env bash
# Slice 8 conformance (D10 — Round 3): private-registry backfill scope clause.
#
# Asserts that specs/npm-distribution.md carries an Out-of-Scope clause naming
# private-registry backfill as explicitly out of scope for this sub-spec, and
# that ROADMAP.md references a planned `private-registry` backfill effort. D10
# resolves the question "does this sub-spec cover backfill against a private
# npm registry?" with a clear NO at the spec layer plus a non-binding ROADMAP
# entry so a reader who wants the capability can see it's a known future
# direction, not an oversight.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
fail=0

if [[ ! -f "$spec" ]]; then
  echo "FAIL [pre]: $spec missing"
  echo "slice-8 (scope) conformance: FAIL"
  exit 1
fi

# A1: an Out-of-Scope clause exists in the spec. We accept any heading that
# contains 'Out of Scope' (case-insensitive) — typically '## Out of Scope'
# or '### Out of Scope' under §Scope. The clause is a normative scope
# boundary, not a tier label, so we anchor on the heading text rather than
# requiring '(normative)'.
if ! grep -qiE '^#{1,6}\s+Out of Scope' "$spec"; then
  echo "FAIL [A1]: spec has no 'Out of Scope' heading"
  fail=1
else
  echo "OK  [A1] spec carries an 'Out of Scope' heading"
fi

# A2: the Out-of-Scope clause names private-registry backfill. We accept
# any of: 'private registry' (with space), 'private-registry' (hyphenated),
# or 'private npm registry' — all case-insensitive — co-occurring with
# 'backfill' anywhere in the Out-of-Scope clause body. The flag-toggle awk
# pattern scopes the search to the body between 'Out of Scope' and the
# next heading.
oos_block="$(awk '
  tolower($0) ~ /^#{1,6}[[:space:]]+out of scope/ {flag=1; next}
  flag && /^#{1,6}[[:space:]]/ {flag=0}
  flag
' "$spec")"
if [[ -z "$oos_block" ]]; then
  echo "FAIL [A2]: Out-of-Scope body not captured"
  fail=1
elif echo "$oos_block" | grep -iqE 'private[- ]?(npm[- ]?)?registry' \
     && echo "$oos_block" | grep -iqE 'backfill'; then
  echo "OK  [A2] Out-of-Scope clause names private-registry backfill"
else
  echo "FAIL [A2]: Out-of-Scope clause does not name private-registry AND backfill together:"
  echo "$oos_block" | head -10
  fail=1
fi

# A3: ROADMAP.md references private-registry backfill. The entry can be
# brief — a heading, a bullet, or a sentence — as long as 'private' and
# 'registry' (or 'private-registry') co-occur with 'backfill' nearby. We
# accept the co-occurrence anywhere in the file because ROADMAP.md is a
# free-form planning document, not a normative artifact.
if [[ ! -f ROADMAP.md ]]; then
  echo "FAIL [A3]: ROADMAP.md missing"
  fail=1
else
  if grep -iqE 'private[- ]?registry.*backfill|backfill.*private[- ]?registry' ROADMAP.md; then
    echo "OK  [A3] ROADMAP.md references private-registry backfill"
  else
    echo "FAIL [A3]: ROADMAP.md does not co-locate 'private-registry' with 'backfill'"
    fail=1
  fi
fi

# A4: website mirror parity — regression guard against forgotten mirror sync.
mirror=website/src/content/docs/spec/npm-distribution.md
if [[ ! -f "$mirror" ]]; then
  echo "FAIL [A4]: $mirror does not exist"
  fail=1
else
  mirror_h1="$(grep -m1 '^# ' "$mirror" || true)"
  canon_h1="$(grep -m1 '^# ' "$spec" || true)"
  if [[ "$mirror_h1" == "$canon_h1" && -n "$mirror_h1" ]]; then
    echo "OK  [A4] mirror first H1 matches canonical"
  else
    echo "FAIL [A4]: mirror H1 mismatch (mirror='$mirror_h1' canon='$canon_h1')"
    fail=1
  fi
fi

if [[ "$fail" -ne 0 ]]; then
  echo "slice-8 (scope) conformance: FAIL"
  exit 1
fi
echo "slice-8 (scope) conformance: OK"
exit 0
