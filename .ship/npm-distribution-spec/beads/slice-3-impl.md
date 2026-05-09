Slice 3 impl bead — TDD green phase.

Append `## package.json moat Block (normative)` to `specs/npm-distribution.md`.

Section content:
- Field-definition table (Field | Required | Description) covering: moat.contentDirectory (REQUIRED, string, names the tarball-relative path of the Content Directory), moat.attestations (REQUIRED, array), moat.attestations[].role (REQUIRED, enum publisher | registry), moat.attestations[].bundle (REQUIRED, base64 Sigstore protobuf bundle v0.3), moat.attestations[].rekor_log_index (REQUIRED, integer).
- Bold-label inline qualifier: **Role uniqueness (normative — MUST):** an attestations array MUST NOT contain two entries with the same role value.
- Worked-example fenced JSON block showing a populated moat block with one publisher and one registry attestation entry. Each entry signs the canonical {"_version":1,"content_hash":"sha256:<hex>"} payload.
- One-sentence prose lead-in introducing the example per the introduce-then-fence pattern.

Green phase: `.ship/npm-distribution-spec/conformance/slice-3.sh` exits 0.

Checkpoint: a Publisher copy-pastes the worked example into a real package.json, fills in real content_hash and bundle values, and `python -c 'import json; json.load(open("package.json"))'` parses it cleanly.
