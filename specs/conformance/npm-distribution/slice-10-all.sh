#!/usr/bin/env bash
# Slice 10 composite runner — invokes slice-11/12/13 in sequence and
# exits with combined non-zero on any failure. Used by ship-run-test
# to record the TDD red/green phase for the single moat-cab/moat-5ba
# bead pair that owns the three slice-10 sub-scripts.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fail=0
for s in slice-11-changelog.sh slice-12-mirror.sh slice-13-rule.sh; do
  echo "=== $s ==="
  bash "$SCRIPT_DIR/$s"
  rc=$?
  [[ $rc -ne 0 ]] && fail=1
done
exit $fail
