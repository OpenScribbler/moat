#!/usr/bin/env bash
# Slice 1 conformance: GitHub sub-specs reachable under specs/github/, with
# specs/moat-verify.md preserved at top level as the platform-neutral entry.
# Red before slice-1 impl; green after.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

fail=0

# A1: no references to the old specs/publisher-action.md path outside historical / scratch areas.
# Exclusions: panel/ (review history per .claude/rules/changelog.md:21), .ship/ + .develop/
# (per-feature planning scratch), .handoffs/ (historical handoff records), .beads/ (issue DB),
# .claude/ (tooling per the changelog rule's own tooling-only carve-out), .git/, .wolf/,
# CHANGELOG.md (versioned history is preserved verbatim).
hits1=$(grep -rln 'specs/publisher-action\.md' . \
  --exclude-dir=panel \
  --exclude-dir=.ship \
  --exclude-dir=.develop \
  --exclude-dir=.handoffs \
  --exclude-dir=.beads \
  --exclude-dir=.claude \
  --exclude-dir=.git \
  --exclude-dir=.wolf \
  --exclude=CHANGELOG.md \
  2>/dev/null || true)
if [[ -n "$hits1" ]]; then
  echo "FAIL [A1]: stale references to specs/publisher-action.md:"
  echo "$hits1"
  fail=1
fi

# A2: same for specs/registry-action.md.
hits2=$(grep -rln 'specs/registry-action\.md' . \
  --exclude-dir=panel \
  --exclude-dir=.ship \
  --exclude-dir=.develop \
  --exclude-dir=.handoffs \
  --exclude-dir=.beads \
  --exclude-dir=.claude \
  --exclude-dir=.git \
  --exclude-dir=.wolf \
  --exclude=CHANGELOG.md \
  2>/dev/null || true)
if [[ -n "$hits2" ]]; then
  echo "FAIL [A2]: stale references to specs/registry-action.md:"
  echo "$hits2"
  fail=1
fi

# A3: target files exist at new paths; old paths don't; moat-verify stays at top level.
if [[ ! -f specs/github/publisher-action.md ]]; then
  echo "FAIL [A3]: specs/github/publisher-action.md missing"
  fail=1
fi
if [[ ! -f specs/github/registry-action.md ]]; then
  echo "FAIL [A3]: specs/github/registry-action.md missing"
  fail=1
fi
if [[ ! -f specs/moat-verify.md ]]; then
  echo "FAIL [A3]: specs/moat-verify.md missing"
  fail=1
fi
if [[ -e specs/publisher-action.md ]]; then
  echo "FAIL [A3]: specs/publisher-action.md should not exist (move not complete)"
  fail=1
fi
if [[ -e specs/registry-action.md ]]; then
  echo "FAIL [A3]: specs/registry-action.md should not exist (move not complete)"
  fail=1
fi

# A4: every link in the named files mentioning publisher-action.md / registry-action.md
# resolves under specs/github/ — i.e., no surviving non-github filesystem references.
for f in moat-spec.md lexicon.md README.md RELEASING.md docs/guides/publisher.md; do
  if [[ ! -f "$f" ]]; then continue; fi
  bad=$(grep -nE '(publisher-action|registry-action)\.md' "$f" | grep -v 'github/' || true)
  if [[ -n "$bad" ]]; then
    echo "FAIL [A4]: $f contains non-github cross-references:"
    echo "$bad"
    fail=1
  fi
done

# A5: lexicon.md updated to point at specs/github/.
ngh=$(grep -c 'specs/github' lexicon.md 2>/dev/null)
ngh=${ngh:-0}
if [[ "$ngh" -lt 2 ]]; then
  echo "FAIL [A5]: lexicon.md has $ngh 'specs/github' references (need >= 2)"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "slice-1 conformance: FAIL"
  exit 1
fi
echo "slice-1 conformance: OK"
exit 0
