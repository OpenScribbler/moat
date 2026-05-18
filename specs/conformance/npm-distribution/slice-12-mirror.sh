#!/usr/bin/env bash
# Slice 10 conformance (Round 3, part B): website-mirror parity guard.
#
# Asserts that `website/src/content/docs/spec/npm-distribution.md` is
# byte-identical to `specs/npm-distribution.md` after stripping the
# mirror's Starlight frontmatter (the YAML block delimited by `---` at
# the top of the mirror). The mirror diverges from canonical ONLY in
# that frontmatter — every Round-3 spec edit MUST land in both files
# in the same commit, and this slice is the regression guard that
# catches a forgotten mirror sync.
#
# A1: mirror file exists.
# A2: canonical spec exists.
# A3: stripping mirror frontmatter (lines from first `---` through
#     second `---` inclusive) yields a body byte-identical to the
#     canonical spec.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
mirror=website/src/content/docs/spec/npm-distribution.md
fail=0

if [[ ! -f "$mirror" ]]; then
  echo "FAIL [A1]: mirror $mirror does not exist"
  fail=1
fi
if [[ ! -f "$spec" ]]; then
  echo "FAIL [A2]: canonical $spec does not exist"
  fail=1
fi

if [[ -f "$mirror" && -f "$spec" ]]; then
  # Strip Starlight frontmatter: delete from the first '---' line to the
  # second '---' line inclusive. The mirror is expected to start with
  # `---`, so this is a clean strip.
  diff <(sed '1,/^---$/d' "$mirror") "$spec" > /tmp/slice-12-mirror-diff.txt
  if [[ $? -eq 0 ]]; then
    echo "OK  [A3] mirror body byte-identical to canonical after frontmatter strip"
  else
    diff_lines="$(wc -l < /tmp/slice-12-mirror-diff.txt)"
    echo "FAIL [A3]: mirror diverges from canonical ($diff_lines diff lines, see /tmp/slice-12-mirror-diff.txt):"
    head -20 /tmp/slice-12-mirror-diff.txt | sed 's/^/    /'
    fail=1
  fi
fi

if [[ "$fail" -eq 0 ]]; then
  echo "slice-10 (mirror) conformance: OK"
  exit 0
else
  echo "slice-10 (mirror) conformance: FAIL"
  exit 1
fi
