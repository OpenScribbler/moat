#!/usr/bin/env bash
# Slice 5 conformance: website spec mirror, Astro sidebar entry, and
# CHANGELOG [Unreleased] entries (Added bullet citing the new sub-spec,
# Changed bullets for the GitHub reorg with 'no normative change' phrasing).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

fail=0

# A1: Astro sidebar config references the new npm-distribution spec at
# least once (slug, label, or import path — any of those is a sufficient
# observation that the sidebar was updated).
n_astro=$(grep -c 'npm-distribution' website/astro.config.mjs 2>/dev/null)
n_astro=${n_astro:-0}
if [[ "$n_astro" -lt 1 ]]; then
  echo "FAIL [A1]: website/astro.config.mjs has no 'npm-distribution' reference"
  fail=1
fi

# A2: website mirror exists; its first H1 line is byte-identical to the
# canonical sub-spec's first H1 line. The mirror is allowed to diverge in
# YAML frontmatter (Starlight metadata), but the H1 must agree so the spec
# title shown in the rendered site matches the title shown in the repo.
mirror=website/src/content/docs/spec/npm-distribution.md
canonical=specs/npm-distribution.md
if [[ ! -f "$mirror" ]]; then
  echo "FAIL [A2]: $mirror does not exist"
  fail=1
elif [[ ! -f "$canonical" ]]; then
  echo "FAIL [A2]: $canonical does not exist (slice-2..4 should have produced it)"
  fail=1
else
  mirror_h1=$(grep -m1 '^# ' "$mirror" || true)
  canon_h1=$(grep -m1 '^# ' "$canonical" || true)
  if [[ -z "$mirror_h1" || -z "$canon_h1" ]]; then
    echo "FAIL [A2]: missing H1 in mirror or canonical"
    echo "  mirror H1:    '${mirror_h1}'"
    echo "  canonical H1: '${canon_h1}'"
    fail=1
  elif [[ "$mirror_h1" != "$canon_h1" ]]; then
    echo "FAIL [A2]: mirror first H1 does not match canonical:"
    echo "  mirror:    $mirror_h1"
    echo "  canonical: $canon_h1"
    fail=1
  fi
fi

# A3: '## [Unreleased]' appears exactly once in the first 40 lines of CHANGELOG.md.
n_unreleased=$(head -40 CHANGELOG.md | grep -cE '^## \[Unreleased\]' 2>/dev/null)
n_unreleased=${n_unreleased:-0}
if [[ "$n_unreleased" -ne 1 ]]; then
  echo "FAIL [A3]: expected exactly 1 '## [Unreleased]' heading in head -40 of CHANGELOG.md, found $n_unreleased"
  fail=1
fi

# A3 continued: extract the [Unreleased] block (lines after the heading,
# up to the next versioned heading), and assert both ### Added and
# ### Changed sub-headings appear within it.
unreleased_block=$(awk '/^## \[Unreleased\]/{flag=1; next} /^## \[[0-9]/{flag=0} flag' CHANGELOG.md)
if ! echo "$unreleased_block" | grep -qE '^### Added[[:space:]]*$'; then
  echo "FAIL [A3]: '### Added' missing from [Unreleased] block"
  fail=1
fi
if ! echo "$unreleased_block" | grep -qE '^### Changed[[:space:]]*$'; then
  echo "FAIL [A3]: '### Changed' missing from [Unreleased] block"
  fail=1
fi

# A4: bold-label '**specs/npm-distribution.md**' appears at least once in
# the [Unreleased] block — a reader scanning the changelog can see that the
# new sub-spec is the headline content of this release.
n_npm=$(echo "$unreleased_block" | grep -cE '\*\*specs/npm-distribution\.md\*\*' 2>/dev/null)
n_npm=${n_npm:-0}
if [[ "$n_npm" -lt 1 ]]; then
  echo "FAIL [A4]: '**specs/npm-distribution.md**' missing from [Unreleased] block"
  fail=1
fi

# A5: bold-label '**specs/github/<publisher|registry>-action.md**' appears
# at least twice in the [Unreleased] block (one for each sub-spec moved),
# and every such line contains the literal phrase 'no normative change'
# per .claude/rules/changelog.md (path-only moves are PATCH-level).
github_lines=$(echo "$unreleased_block" | grep -nE '\*\*specs/github/(publisher|registry)-action\.md\*\*' || true)
n_github=0
if [[ -n "$github_lines" ]]; then
  n_github=$(echo "$github_lines" | wc -l)
fi
if [[ "$n_github" -lt 2 ]]; then
  echo "FAIL [A5]: expected ≥2 '**specs/github/{publisher|registry}-action.md**' bullets in [Unreleased], found $n_github"
  fail=1
fi
if [[ -n "$github_lines" ]]; then
  github_bad=$(echo "$github_lines" | grep -vE 'no normative change' || true)
  if [[ -n "$github_bad" ]]; then
    echo "FAIL [A5]: github reorg bullets missing 'no normative change' phrase:"
    echo "$github_bad"
    fail=1
  fi
fi

# A6: changelog convention lint — no panel/persona/finding-ID markers in
# the [Unreleased] section per .claude/rules/changelog.md.
forbidden=$(echo "$unreleased_block" | grep -niE '(panel|persona|five-persona|adversarial|reviewer feedback|agent consensus|SC-[0-9]|DQ-[0-9]|SB-[0-9])' || true)
if [[ -n "$forbidden" ]]; then
  echo "FAIL [A6]: forbidden process-metadata phrases found in [Unreleased] block:"
  echo "$forbidden"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "slice-5 conformance: FAIL"
  exit 1
fi
echo "slice-5 conformance: OK"
exit 0
