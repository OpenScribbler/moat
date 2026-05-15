#!/usr/bin/env bash
# Slice 4 conformance: Backfill (normative) section, npm Provenance
# (informative) section, Trust Tier labels consistent with moat-spec.md
# (no fourth tier invented), no registry_backfill_signing_profile field,
# closing ## Scope section with Current/Planned-future bold-label one-liners.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
fail=0

if [[ ! -f "$spec" ]]; then
  echo "FAIL [pre]: $spec missing"
  echo "slice-4 conformance: FAIL"
  exit 1
fi

# A1: ## Backfill ... (normative...) section heading exists, exactly one match.
n_back=$(grep -cE '^## Backfill.+\(normative' "$spec")
n_back=${n_back:-0}
if [[ "$n_back" -ne 1 ]]; then
  echo "FAIL [A1]: expected exactly 1 '## Backfill ... (normative...)' heading, found $n_back"
  fail=1
fi

# A2: ## npm Provenance (informative) section heading exists, exactly one match.
n_prov=$(grep -cE '^## npm Provenance \(informative\)' "$spec")
n_prov=${n_prov:-0}
if [[ "$n_prov" -ne 1 ]]; then
  echo "FAIL [A2]: expected exactly 1 '## npm Provenance (informative)' heading, found $n_prov"
  fail=1
fi

# A3: each canonical Trust Tier label from moat-spec.md (Dual-Attested, Signed,
# Unsigned) MUST appear at least once in the npm-distribution sub-spec — the
# slice has to anchor itself in the existing tier vocabulary rather than in
# prose alone. The "Verified" verb form is also accepted (moat-spec.md uses it
# as verification-status terminology). Additionally, no novel "X-Attested"
# Trust-Tier name MAY be invented.
for tier in 'Dual-Attested' 'Signed' 'Unsigned'; do
  if ! grep -qE "\\b${tier}\\b" "$spec"; then
    echo "FAIL [A3]: canonical Trust Tier label '${tier}' missing from $spec"
    fail=1
  fi
done
# Catch invented tiers: any capitalized "X-Attested" other than Dual-Attested.
invented=$(grep -oE '\b[A-Z][A-Za-z]+-Attested\b' "$spec" | grep -vE '^Dual-Attested$' || true)
if [[ -n "$invented" ]]; then
  echo "FAIL [A3]: invented Trust Tier label found:"
  echo "$invented"
  fail=1
fi

# A4: no registry_backfill_signing_profile field — backfill uses the same
# registry_signing_profile as a normal Registry attestation.
if grep -qE 'registry_backfill_signing_profile' "$spec"; then
  echo "FAIL [A4]: spec contains forbidden registry_backfill_signing_profile field"
  fail=1
fi

# A5: closing ## Scope section with Current / Planned-future bold labels.
if ! grep -qE '^## Scope$' "$spec"; then
  echo "FAIL [A5]: missing closing '## Scope' section"
  fail=1
fi
if ! grep -qE '^\*\*Current version:\*\*' "$spec"; then
  echo "FAIL [A5]: missing '**Current version:**' bold-label line"
  fail=1
fi
if ! grep -qE '^\*\*Planned future version:\*\*' "$spec"; then
  echo "FAIL [A5]: missing '**Planned future version:**' bold-label line"
  fail=1
fi

# A6 (D4 Round 3): the project-scoped npm lockfile filename `.moat/npm-lockfile.json`
# is pinned in the §Revocation MUST block (anchored to the Pre-materialization hard
# block + neighbouring Persistence/Resolve-time MUSTs). The plan ties the anchor to
# the `:47`–`:51` range.
rev_block="$(awk '/^## Revocation at the Materialization Boundary/{flag=1; next} flag && /^## /{flag=0} flag' "$spec")"
if [[ -z "$rev_block" ]]; then
  echo "FAIL [A6]: §Revocation at the Materialization Boundary section not found"
  fail=1
elif echo "$rev_block" | grep -F '.moat/npm-lockfile.json' >/dev/null; then
  echo "OK  [A6] .moat/npm-lockfile.json named in §Revocation block"
else
  echo "FAIL [A6]: .moat/npm-lockfile.json not named in §Revocation block"
  fail=1
fi

# A7 (D4 Round 3): lexicon.md disambiguates `.moat/npm-lockfile.json` from npm's
# `package-lock.json`. The two filenames MUST co-occur within the lexicon row for
# the **Lockfile** term so a reader cannot confuse the MOAT artifact with npm's
# resolver-cache artifact.
if [[ -f lexicon.md ]]; then
  lock_row="$(grep -nE '^\| \*\*Lockfile\*\* \|' lexicon.md || true)"
  if [[ -z "$lock_row" ]]; then
    echo "FAIL [A7]: **Lockfile** row not found in lexicon.md"
    fail=1
  elif echo "$lock_row" | grep -F '.moat/npm-lockfile.json' >/dev/null \
     && echo "$lock_row" | grep -F 'package-lock.json' >/dev/null; then
    echo "OK  [A7] lexicon **Lockfile** row disambiguates .moat/npm-lockfile.json from package-lock.json"
  else
    echo "FAIL [A7]: lexicon **Lockfile** row does not disambiguate .moat/npm-lockfile.json from package-lock.json"
    fail=1
  fi
else
  echo "FAIL [A7]: lexicon.md missing"
  fail=1
fi

# A8 (D4 Round 3): the channel-agnostic moat-spec.md §Lockfile section is NOT
# touched by this slice — the `.moat/npm-lockfile.json` filename pin lives in the
# npm sub-spec only. The §Lockfile heading still exists in moat-spec.md and the
# section MUST NOT name `.moat/npm-lockfile.json` (it is npm-specific).
if [[ -f moat-spec.md ]]; then
  if grep -nE '^### Lockfile$' moat-spec.md >/dev/null; then
    lock_section="$(awk '/^### Lockfile$/{flag=1; next} flag && /^### /{flag=0} flag' moat-spec.md)"
    if echo "$lock_section" | grep -F '.moat/npm-lockfile.json' >/dev/null; then
      echo "FAIL [A8]: moat-spec.md §Lockfile names the npm-specific .moat/npm-lockfile.json (must stay channel-agnostic)"
      fail=1
    else
      echo "OK  [A8] moat-spec.md §Lockfile remains channel-agnostic (no .moat/npm-lockfile.json mention)"
    fi
  else
    echo "FAIL [A8]: moat-spec.md §Lockfile heading not found"
    fail=1
  fi
else
  echo "FAIL [A8]: moat-spec.md missing"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "slice-4 conformance: FAIL"
  exit 1
fi
echo "slice-4 conformance: OK"
exit 0
