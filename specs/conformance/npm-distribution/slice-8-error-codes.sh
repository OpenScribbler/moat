#!/usr/bin/env bash
# Slice 8 conformance (Round 3): Conformance error-code surface.
#
# Asserts that specs/npm-distribution.md carries a `## Conformance (normative)`
# section whose body is a pipe table of error codes mapping the spec's
# normative MUSTs and MUST NOTs to refusal labels. The surface is what a
# Conforming Client emits on a refusal so an End User (or operator reading
# logs) can route from refusal text back to the section of the spec that
# defines the rule.
#
# A1: §Conformance (normative) section exists.
# A2: error-code table has ≥ 30 rows.
# A3: every code matches NPM-<SECTION>-<NN> pattern.
# A4: no duplicate codes within the table.
# A5: at least one sibling slice-*.sh script cites at least one code.
# A6: every spec-internal file:line citation in the table points at a line
#     that actually carries a MUST or MUST NOT — the codes can't decorate
#     non-normative prose.
# A7: no two codes in the table cite the same file:line — citation uniqueness
#     keeps the one-MUST-per-code stability guarantee from ADR-0015 honest.
# A8: website mirror parity (regression guard).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
fail=0

if [[ ! -f "$spec" ]]; then
  echo "FAIL [pre]: $spec missing"
  echo "slice-8 (error codes) conformance: FAIL"
  exit 1
fi

# A1: §Conformance (normative) heading present exactly once.
n_conf="$(grep -cE '^## Conformance \(normative\)' "$spec")"
n_conf="${n_conf:-0}"
if [[ "$n_conf" -ne 1 ]]; then
  echo "FAIL [A1]: expected exactly 1 '## Conformance (normative)' heading, found $n_conf"
  fail=1
else
  echo "OK  [A1] §Conformance (normative) section heading present"
fi

# Capture the §Conformance section body. Flag-toggle awk: skip the start
# heading line, clear on any subsequent `## ` heading.
conf_block="$(awk '/^## Conformance \(normative\)/{flag=1; next} flag && /^## /{flag=0} flag' "$spec")"

# A2: the table inside §Conformance has ≥ 30 data rows. Data rows are
# pipe-rows that are NOT the separator `|---|` AND NOT the header row.
# We count every pipe-row, subtract 1 (header) and 1 (separator).
if [[ -z "$conf_block" ]]; then
  echo "FAIL [A2]: §Conformance body empty (cannot count rows)"
  fail=1
else
  n_pipe_rows="$(echo "$conf_block" | grep -cE '^\|' || true)"
  n_pipe_rows="${n_pipe_rows:-0}"
  if [[ "$n_pipe_rows" -lt 32 ]]; then
    echo "FAIL [A2]: §Conformance has $n_pipe_rows pipe-rows (need ≥ 32 = 30 data + header + separator)"
    fail=1
  else
    n_data=$((n_pipe_rows - 2))
    echo "OK  [A2] §Conformance has $n_data data rows (≥ 30)"
  fi
fi

# A3: every code in the table matches NPM-<SECTION>-<NN> pattern, where
# SECTION is one or more uppercase letters and NN is at least two digits.
# Codes appear in the first cell of each data row. We extract them and
# reject any that don't match the pattern.
if [[ -n "$conf_block" ]]; then
  codes="$(echo "$conf_block" \
    | grep -E '^\| *`?NPM-' \
    | sed -E 's/^\| *`?([A-Z0-9-]+)`?.*/\1/' \
    | sort)"
  if [[ -z "$codes" ]]; then
    echo "FAIL [A3]: no NPM-... codes found in §Conformance table"
    fail=1
  else
    bad="$(echo "$codes" | grep -vE '^NPM-[A-Z]+-[0-9]{2,}$' || true)"
    if [[ -n "$bad" ]]; then
      echo "FAIL [A3]: codes do not match NPM-<SECTION>-<NN> pattern:"
      echo "$bad"
      fail=1
    else
      n_codes="$(echo "$codes" | wc -l)"
      echo "OK  [A3] all $n_codes codes match NPM-<SECTION>-<NN> pattern"
    fi
  fi
fi

# A4: no duplicate codes within the table.
if [[ -n "$conf_block" ]]; then
  codes="$(echo "$conf_block" \
    | grep -E '^\| *`?NPM-' \
    | sed -E 's/^\| *`?([A-Z0-9-]+)`?.*/\1/')"
  if [[ -n "$codes" ]]; then
    dups="$(echo "$codes" | sort | uniq -d || true)"
    if [[ -n "$dups" ]]; then
      echo "FAIL [A4]: duplicate codes in §Conformance table:"
      echo "$dups"
      fail=1
    else
      echo "OK  [A4] no duplicate codes in §Conformance table"
    fi
  fi
fi

# A5: at least one sibling slice script cites at least one NPM-... code.
# A code-citation must appear in a comment or string within a slice-*.sh
# script — the codes are how a refusal in the field is routed back to the
# spec, so the slice scripts themselves should reference codes when they
# assert the underlying MUST.
sibling_cites="$(grep -lE 'NPM-[A-Z]+-[0-9]{2,}' specs/conformance/npm-distribution/slice-*.sh 2>/dev/null || true)"
# Exclude this script itself (which mentions the pattern in its own header).
sibling_cites="$(echo "$sibling_cites" | grep -v 'slice-8-error-codes\.sh' || true)"
if [[ -z "$sibling_cites" ]]; then
  echo "FAIL [A5]: no sibling slice-*.sh script cites any NPM-... code"
  fail=1
else
  n_files="$(echo "$sibling_cites" | wc -l)"
  echo "OK  [A5] $n_files sibling slice script(s) cite at least one NPM-... code"
fi

# A6: every spec-internal file:line citation in the table points at a line
# that carries MUST or MUST NOT. The plan's `specs/npm-distribution.md:NNN`
# pattern is the canonical citation form. We extract each citation, read
# the cited line, and assert it matches `MUST` or `MUST NOT`. A miss means
# a code was hooked to a non-normative line (a heading, an example, or
# editorial prose), which would defeat the surface.
if [[ -n "$conf_block" ]]; then
  citations="$(echo "$conf_block" \
    | grep -oE 'specs/npm-distribution\.md:[0-9]+' \
    | sort -u || true)"
  if [[ -z "$citations" ]]; then
    echo "FAIL [A6]: no spec-internal file:line citations found in §Conformance table"
    fail=1
  else
    bad_citations=""
    while IFS= read -r cite; do
      [[ -z "$cite" ]] && continue
      lineno="${cite##*:}"
      cited_line="$(sed -n "${lineno}p" "$spec" || true)"
      if ! echo "$cited_line" | grep -qE '\b(MUST|MUST NOT)\b'; then
        bad_citations="${bad_citations}${cite} → '${cited_line}'\n"
      fi
    done <<< "$citations"
    if [[ -n "$bad_citations" ]]; then
      echo "FAIL [A6]: citations point at lines without MUST / MUST NOT:"
      printf '%b' "$bad_citations"
      fail=1
    else
      n_cites="$(echo "$citations" | wc -l)"
      echo "OK  [A6] all $n_cites spec citations point at lines carrying MUST / MUST NOT"
    fi
  fi
fi

# A7: citation uniqueness. Round 4 strengthens the one-MUST-per-code
# stability guarantee from ADR-0015: every NPM-<SECTION>-<NN> row in the
# §Conformance table MUST cite a distinct `specs/npm-distribution.md:<line>`
# anchor. Two codes citing the same source line implies the line packs
# more than one normative obligation, which makes any future edit to that
# line ambiguous as to which code's MUST changed. A6 catches anchors that
# drift off MUST lines; A7 catches anchors that share a MUST line.
if [[ -n "$conf_block" ]]; then
  all_citations="$(echo "$conf_block" \
    | grep -oE 'specs/npm-distribution\.md:[0-9]+' || true)"
  if [[ -z "$all_citations" ]]; then
    echo "FAIL [A7]: no spec-internal file:line citations found in §Conformance table"
    fail=1
  else
    dup_citations="$(echo "$all_citations" | sort | uniq -d || true)"
    if [[ -n "$dup_citations" ]]; then
      echo "FAIL [A7]: duplicate citations in §Conformance table (one MUST per code):"
      echo "$dup_citations" | sed 's/^/  /'
      fail=1
    else
      n_unique="$(echo "$all_citations" | sort -u | wc -l)"
      echo "OK  [A7] all $n_unique citations are unique (one MUST per code)"
    fi
  fi
fi

# A8: website mirror parity (regression guard).
mirror=website/src/content/docs/spec/npm-distribution.md
if [[ ! -f "$mirror" ]]; then
  echo "FAIL [A8]: $mirror does not exist"
  fail=1
else
  mirror_h1="$(grep -m1 '^# ' "$mirror" || true)"
  canon_h1="$(grep -m1 '^# ' "$spec" || true)"
  if [[ "$mirror_h1" == "$canon_h1" && -n "$mirror_h1" ]]; then
    echo "OK  [A8] mirror first H1 matches canonical"
  else
    echo "FAIL [A8]: mirror H1 mismatch (mirror='$mirror_h1' canon='$canon_h1')"
    fail=1
  fi
fi

if [[ "$fail" -ne 0 ]]; then
  echo "slice-8 (error codes) conformance: FAIL"
  exit 1
fi
echo "slice-8 (error codes) conformance: OK"
exit 0
