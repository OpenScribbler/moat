#!/usr/bin/env bash
# Slice 10 conformance (Round 3, part C): spec-citations.md rule exists.
#
# Asserts that `.claude/rules/spec-citations.md` exists and names the
# `path:NN` citation form that the §Conformance error-code table relies
# on. The rule's job is to make future contributors anchor normative
# claims on line-number citations the way Round 3's §Conformance table
# does — without a written rule, the convention rots as contributors
# come and go.
#
# A1: file exists.
# A2: file mentions the `<path>:<line>` citation form (literal example
#     with at least one colon-separated path-to-line reference).
# A3: file mentions the §Conformance table or its error-code surface
#     (NPM-<SECTION>-<NN>) as the canonical example of where the form
#     is used.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

rule=.claude/rules/spec-citations.md
fail=0

# A1: file exists.
if [[ ! -f "$rule" ]]; then
  echo "FAIL [A1]: $rule does not exist"
  echo "slice-10 (rule) conformance: FAIL"
  exit 1
fi
echo "OK  [A1] $rule exists"

# A2: file names the `path:NN` citation form. We accept any example of a
# `<word-or-slash>:<digits>` token (e.g., `specs/npm-distribution.md:117`)
# OR a literal mention of the form ('file:line', 'file:NN', 'path:line').
if grep -qE '\b[a-zA-Z0-9_./-]+\.md:[0-9]+\b' "$rule" \
   || grep -qiE '\bfile:(line|NN|N+)\b|\bpath:(line|NN|N+)\b' "$rule"; then
  echo "OK  [A2] $rule names the path:NN citation form"
else
  echo "FAIL [A2]: $rule does not name the path:NN citation form"
  fail=1
fi

# A3: file mentions the §Conformance table or NPM-<SECTION>-<NN> error
# codes as the canonical user of the citation form.
if grep -qiE 'Conformance|NPM-[A-Z]+-[0-9]' "$rule"; then
  echo "OK  [A3] $rule references §Conformance table or NPM-<SECTION>-<NN> error codes"
else
  echo "FAIL [A3]: $rule does not reference the §Conformance error-code surface"
  fail=1
fi

if [[ "$fail" -eq 0 ]]; then
  echo "slice-10 (rule) conformance: OK"
  exit 0
else
  echo "slice-10 (rule) conformance: FAIL"
  exit 1
fi
