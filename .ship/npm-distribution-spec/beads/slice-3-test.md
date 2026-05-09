Slice 3 test bead — TDD red phase.

Write `.ship/npm-distribution-spec/conformance/slice-3.sh`.

Asserts:
- The new section contains exactly one Markdown table whose columns are Field | Required | Description, with rows for moat.contentDirectory, moat.attestations, moat.attestations[].role, moat.attestations[].bundle, moat.attestations[].rekor_log_index. Each Required cell carries an RFC 2119 keyword.
- A fenced ```json block follows the table; contains "moat": {, "contentDirectory":, "attestations": [; contains at least two array entries — one with "role": "publisher" and one with "role": "registry".
- `grep -n '_version' specs/npm-distribution.md` finds the canonical {"_version":1,"content_hash":"sha256:..."} payload form (not a variant).
- `grep -nE '\*\*Role uniqueness \(normative — MUST\):\*\*' specs/npm-distribution.md` returns exactly one match.

Red phase required before close.
