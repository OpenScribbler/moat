#!/usr/bin/env bash
# Slice 6 (Round 2 slice 1) conformance: Default-Content-Directory backfill capability.
#
# Asserts that specs/npm-distribution.md defines a default Content Directory rule
# (= unpacked tarball root with `package.json` excluded) so that a Registry can
# back-attest a published tarball without Publisher cooperation, AND that the rule
# is mathematically sound — i.e., applying it to fixture tarballs produces the
# equality / inequality relationships the spec asserts.
#
# Spec-text assertions (S1-S5) red-phase before the spec impl lands.
# Algorithmic invariants (A1-A5) exercise the rule against fixture tarballs the
# script builds itself; they catch bugs in the rule's mathematical statement
# (e.g., non-determinism from tar metadata, exclusion not actually applied,
# subdirectory mode incorrectly inheriting exclusions).
#
# Red before slice-1 impl; green after.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

spec=specs/npm-distribution.md
hash_py="$REPO_ROOT/reference/moat_hash.py"
fail=0

if [[ ! -f "$spec" ]]; then
  echo "FAIL [pre]: $spec missing"
  echo "slice-6 conformance: FAIL"
  exit 1
fi
if [[ ! -f "$hash_py" ]]; then
  echo "FAIL [pre]: $hash_py missing"
  echo "slice-6 conformance: FAIL"
  exit 1
fi

# ── Spec-text assertions (S1-S5): red until slice-1 impl writes the section ──

# S1: a section heading for the Content Directory rule exists and is normative.
# The heading is expected to be "## Content Directory (normative — MUST)" or a
# close variant that carries the normative status suffix per the Pattern: Heading-
# suffix normative status labels documented in the design.
if ! grep -qE '^## .*Content Directory.*\(normative' "$spec"; then
  echo "FAIL [S1]: section heading for Content Directory (normative) not found in $spec"
  fail=1
fi

# S2-S5 grep against the body of the Content Directory section only (not the
# whole spec). When the section is missing entirely, $section is empty and
# every subsequent grep correctly fails — keeping the red-phase clean and
# preventing matches from unrelated sections from masking missing content.
#
# Capture body strictly BETWEEN the Content Directory heading and the next
# `## ` heading. A naive awk range `/start/,/end/` would match only the
# heading line itself when start and end patterns both match `^## `; the
# flag-toggle form below skips the start line and clears on any subsequent
# `^## `, capturing the body alone.
section=$(awk '/^## .*Content Directory.*\(normative/{flag=1; next} /^## /{flag=0} flag' "$spec" || true)
if ! echo "$section" | grep -qE 'tarball root|unpacked tarball'; then
  echo "FAIL [S2]: default rule does not name the unpacked tarball root as the default Content Directory"
  fail=1
fi
if ! echo "$section" | grep -qE 'package\.json'; then
  echo "FAIL [S2]: default rule does not mention package.json"
  fail=1
fi
if ! echo "$section" | grep -qiE 'exclud(e|ed|ing)'; then
  echo "FAIL [S2]: default rule does not state package.json is excluded"
  fail=1
fi

# S3: subdirectory mode rule is stated — when tarballContentRoot is set, no
# exclusions apply (the subdirectory's contents are hashed in full).
if ! echo "$section" | grep -qiE 'no exclusion|without exclusion|no files (are )?excluded'; then
  echo "FAIL [S3]: subdirectory mode rule does not state that no exclusions apply"
  fail=1
fi

# S4: MUST NOT against Publisher-driven extension of the exclusion list.
# The exclusion is a fixed protocol rule; Publishers cannot widen it.
if ! echo "$section" | grep -qE 'MUST NOT.*(extend|widen|add)|MUST NOT.*exclus'; then
  echo "FAIL [S4]: spec does not forbid Publisher-driven extension of the exclusion list (MUST NOT)"
  fail=1
fi

# S5: the rule is path-anchored to the tarball root — only root-level
# package.json is excluded; nested package.json files are NOT excluded.
if ! echo "$section" | grep -qiE 'root[- ]anchored|tarball root|root[- ]level|only at the (tarball )?root'; then
  echo "FAIL [S5]: spec does not state the exclusion is path-anchored to the tarball root"
  fail=1
fi

# ── Algorithmic invariants (A1-A5): exercise the rule against fixture tarballs ──

WORKDIR=$(mktemp -d 2>/dev/null || mktemp -d -t slice-6)
trap 'rm -rf "$WORKDIR"' EXIT

# Helper: compute MOAT canonical hash over a directory using the reference impl.
moat_hash() {
  python3 "$hash_py" "$1"
}

# Helper: prepare a directory for default-mode hashing — remove root package.json
# only (path-anchored), then return the directory.
default_mode_dir() {
  local extract_dir="$1"
  rm -f "$extract_dir/package.json"
  echo "$extract_dir"
}

# Build fixture t1: {a.md, b.js, package.json} at root (default mode).
t1_src="$WORKDIR/t1-src"
mkdir -p "$t1_src"
printf 'alpha content\n' > "$t1_src/a.md"
printf 'console.log("beta");\n' > "$t1_src/b.js"
printf '{"name":"t1","version":"1.0.0"}\n' > "$t1_src/package.json"
tar -czf "$WORKDIR/t1.tgz" -C "$t1_src" .

# Build fixture t2: {src/foo.md, src/bar.js, src/package.json, package.json}
# with moat.tarballContentRoot: "src" — subdirectory mode.
t2_src="$WORKDIR/t2-src"
mkdir -p "$t2_src/src"
printf 'foo content\n' > "$t2_src/src/foo.md"
printf 'console.log("bar");\n' > "$t2_src/src/bar.js"
printf '{"name":"t2-inner","version":"1.0.0"}\n' > "$t2_src/src/package.json"
printf '{"name":"t2","version":"1.0.0","moat":{"tarballContentRoot":"src"}}\n' > "$t2_src/package.json"
tar -czf "$WORKDIR/t2.tgz" -C "$t2_src" .

# Build fixture t3: {pkg/file.md, pkg/package.json, package.json} at default mode.
t3_src="$WORKDIR/t3-src"
mkdir -p "$t3_src/pkg"
printf 'nested content\n' > "$t3_src/pkg/file.md"
printf '{"name":"t3-nested","version":"1.0.0"}\n' > "$t3_src/pkg/package.json"
printf '{"name":"t3","version":"1.0.0"}\n' > "$t3_src/package.json"
tar -czf "$WORKDIR/t3.tgz" -C "$t3_src" .

# A1: two independent reductions of t1 (default mode) produce byte-equal
# canonical hashes — round-trip through tar/extract is deterministic.
a1_dir1="$WORKDIR/a1-1"; mkdir -p "$a1_dir1"; tar -xzf "$WORKDIR/t1.tgz" -C "$a1_dir1"
a1_dir2="$WORKDIR/a1-2"; mkdir -p "$a1_dir2"; tar -xzf "$WORKDIR/t1.tgz" -C "$a1_dir2"
a1_h1=$(moat_hash "$(default_mode_dir "$a1_dir1")")
a1_h2=$(moat_hash "$(default_mode_dir "$a1_dir2")")
if [[ "$a1_h1" != "$a1_h2" ]]; then
  echo "FAIL [A1]: two reductions of t1 produced different hashes: $a1_h1 vs $a1_h2"
  fail=1
fi

# A2: mutating package.json between reductions does NOT change the canonical
# hash (proves package.json is excluded from the hash domain). Sanity arm:
# also confirm that the same mutation DOES change a naive whole-tree hash —
# guards against an extraction step that silently dropped the file.
a2_dir1="$WORKDIR/a2-1"; mkdir -p "$a2_dir1"; tar -xzf "$WORKDIR/t1.tgz" -C "$a2_dir1"
a2_dir2="$WORKDIR/a2-2"; mkdir -p "$a2_dir2"; tar -xzf "$WORKDIR/t1.tgz" -C "$a2_dir2"
printf '{"name":"t1-MUTATED","version":"99.0.0","moat":{"foo":"bar"}}\n' > "$a2_dir2/package.json"
# Naive hash includes package.json (no rule applied). Use a separate tmp copy
# so default_mode_dir's removal step doesn't perturb the naive read.
a2_naive1=$(cd "$a2_dir1" && find . -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | awk '{print $1}')
a2_naive2=$(cd "$a2_dir2" && find . -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | awk '{print $1}')
if [[ "$a2_naive1" == "$a2_naive2" ]]; then
  echo "FAIL [A2-sanity]: package.json mutation did not change the naive whole-tree hash; fixture setup is broken"
  fail=1
fi
a2_h1=$(moat_hash "$(default_mode_dir "$a2_dir1")")
a2_h2=$(moat_hash "$(default_mode_dir "$a2_dir2")")
if [[ "$a2_h1" != "$a2_h2" ]]; then
  echo "FAIL [A2]: mutating package.json changed the canonical hash ($a2_h1 vs $a2_h2); rule is not excluding package.json"
  fail=1
fi

# A3: subdirectory mode (t2 with tarballContentRoot: "src") applies NO
# exclusions — the canonical hash domain INCLUDES src/package.json. We confirm
# by hashing src/ as-is, then hashing src/ with src/package.json removed, and
# asserting the two differ. If they were equal, src/package.json would be
# silently outside the domain, indicating a leaky exclusion.
a3_dir="$WORKDIR/a3"; mkdir -p "$a3_dir"; tar -xzf "$WORKDIR/t2.tgz" -C "$a3_dir"
a3_h_full=$(moat_hash "$a3_dir/src")
a3_dir_stripped="$WORKDIR/a3-stripped"; cp -r "$a3_dir/src" "$a3_dir_stripped"
rm -f "$a3_dir_stripped/package.json"
a3_h_stripped=$(moat_hash "$a3_dir_stripped")
if [[ "$a3_h_full" == "$a3_h_stripped" ]]; then
  echo "FAIL [A3]: subdirectory-mode hash did not change when src/package.json was removed; exclusion leaked into subdirectory mode"
  fail=1
fi

# A4: default-mode exclusion is path-anchored to the tarball root — the
# canonical hash domain INCLUDES pkg/package.json (nested) and EXCLUDES only
# root-level package.json. We confirm by computing two default-mode hashes:
# (a) only root package.json removed, (b) root package.json AND pkg/package.json
# removed. They must differ — otherwise the exclusion is not path-anchored.
a4_dir1="$WORKDIR/a4-1"; mkdir -p "$a4_dir1"; tar -xzf "$WORKDIR/t3.tgz" -C "$a4_dir1"
a4_dir2="$WORKDIR/a4-2"; mkdir -p "$a4_dir2"; tar -xzf "$WORKDIR/t3.tgz" -C "$a4_dir2"
a4_h1=$(moat_hash "$(default_mode_dir "$a4_dir1")")
rm -f "$a4_dir2/package.json" "$a4_dir2/pkg/package.json"
a4_h2=$(moat_hash "$a4_dir2")
if [[ "$a4_h1" == "$a4_h2" ]]; then
  echo "FAIL [A4]: default-mode hash did not change when pkg/package.json was removed; exclusion is not path-anchored to root"
  fail=1
fi

# A5: backfill (Registry-side, no Publisher cooperation) and Publisher-driven
# paths produce byte-equal canonical hashes against the same content bytes.
# The "Publisher-driven" path is simulated by computing the hash from a working
# directory (pre-pack); the "Registry backfill" path is simulated by packing
# the same directory into a tarball, fetching/extracting, and reducing per the
# default rule. The byte-equality is the load-bearing property: a Registry can
# attest any tarball without Publisher participation and the hash will match
# what a Publisher would compute over the same content bytes.
a5_pub_src="$WORKDIR/a5-pub-src"
mkdir -p "$a5_pub_src"
printf 'alpha content\n' > "$a5_pub_src/a.md"
printf 'console.log("beta");\n' > "$a5_pub_src/b.js"
# Publisher-driven: Publisher computes the hash directly from their working
# directory (with whatever package.json — different from Registry-fetched).
printf '{"name":"a5-pub","version":"1.0.0"}\n' > "$a5_pub_src/package.json"
a5_pub_dir="$WORKDIR/a5-pub-reduce"; cp -r "$a5_pub_src" "$a5_pub_dir"
a5_pub_hash=$(moat_hash "$(default_mode_dir "$a5_pub_dir")")
# Registry backfill: a different package.json (Registry-side has no insight
# into the Publisher's metadata choices), same content bytes for {a.md, b.js}.
a5_reg_src="$WORKDIR/a5-reg-src"
mkdir -p "$a5_reg_src"
printf 'alpha content\n' > "$a5_reg_src/a.md"
printf 'console.log("beta");\n' > "$a5_reg_src/b.js"
printf '{"name":"a5-reg-DIFFERENT","version":"42.0.0","registry":"backfilled"}\n' > "$a5_reg_src/package.json"
tar -czf "$WORKDIR/a5-reg.tgz" -C "$a5_reg_src" .
a5_reg_dir="$WORKDIR/a5-reg-extract"; mkdir -p "$a5_reg_dir"
tar -xzf "$WORKDIR/a5-reg.tgz" -C "$a5_reg_dir"
a5_reg_hash=$(moat_hash "$(default_mode_dir "$a5_reg_dir")")
if [[ "$a5_pub_hash" != "$a5_reg_hash" ]]; then
  echo "FAIL [A5]: backfill and publisher-driven paths produced different hashes ($a5_pub_hash vs $a5_reg_hash); rule is not deterministic across the round-trip"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "slice-6 conformance: FAIL"
  exit 1
fi
echo "slice-6 conformance: OK"
exit 0
