#!/usr/bin/env python3
"""
MOAT Specification — Test Vector Generator

Implements the content hash algorithms from Sections 7.2, 7.3, 7.4, and 8
of the MOAT spec, then generates the content hash vectors (TV-01 through
TV-16, and the path-reject vectors TV-23 through TV-29) with exact byte inputs
and expected SHA-256 outputs, the ACIF content item vectors (TV-ACIF-01
through TV-ACIF-04) and the author-key profile vectors (TV-AK-01 through
TV-AK-14).

Usage: python3 generate_test_vectors.py
"""

import hashlib
import json
import os
import pathlib
import tempfile
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(__file__))
import moat_author_key as ak
import moat_hash


def sha256_hex(data: bytes) -> str:
    """SHA-256 as 64 lowercase hex chars."""
    return hashlib.sha256(data).hexdigest()


def content_hash_single_file(data: bytes) -> str:
    """Section 7.2: Single file content hash."""
    return f"sha256:{sha256_hex(data)}"


def content_hash_directory(file_map: dict[str, bytes]) -> str:
    """
    Section 7.3: Directory tree content hash.

    file_map: {relative_path: file_bytes} — moat-attestation.json already excluded.
    Paths use forward slashes, no leading ./ or trailing /. A path given as
    bytes is the raw name as the filesystem stores it; a str path is its UTF-8.

    Manifest format: sha256sum — "{hash}  {path}\n" per entry.
    This matches moat_hash.py (the normative reference) and POSIX sha256sum output,
    making individual manifest entries verifiable with standard Unix tools.
    """
    # Path rejects, on the raw bytes and before NFC: every path is checked for
    # valid UTF-8 first, then every path for a C0 control or DEL.
    raw = {(p if isinstance(p, bytes) else p.encode("utf-8")): data for p, data in file_map.items()}
    for path in raw:
        try:
            path.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Path is not valid UTF-8 — content is unpublishable")
    for path in raw:
        if any(b < 0x20 or b == 0x7F for b in path):
            raise ValueError("Path contains a control character — content is unpublishable")

    entries = []
    for path, data in raw.items():
        # Step 3: NFC-normalize paths
        nfc_path = unicodedata.normalize("NFC", path.decode("utf-8"))
        # Step 4: per-file hash
        file_hash = sha256_hex(data)
        entries.append((nfc_path, file_hash))

    # Check for NFC collisions (test case 4)
    nfc_paths = [e[0] for e in entries]
    if len(nfc_paths) != len(set(nfc_paths)):
        raise ValueError("NFC collision detected — content is unpublishable")

    # Step 5: sort by NFC path using raw UTF-8 byte ordering
    entries.sort(key=lambda e: e[0].encode("utf-8"))

    # Step 6: build manifest in sha256sum format: "{hash}  {path}\n"
    manifest = "".join(f"{h}  {p}\n" for p, h in entries).encode("utf-8")

    # Step 7: final hash
    return f"sha256:{sha256_hex(manifest)}"


# ─── Test Vector Definitions ───────────────────────────────────────────────

def vector_01():
    """TV-01: Per-file hash, ASCII content (Section 7.2 sub-procedure)"""
    content = b"Hello, MOAT!\n"
    return {
        "id": 1,
        "title": "Per-file hash, ASCII content",
        "section": "7.2",
        "input_description": 'ASCII bytes: `Hello, MOAT!\\n` (12 bytes)',
        "input_hex": content.hex(),
        "input_display": "Hello, MOAT!\\n",
        "per_file_hash": sha256_hex(content),
        "raw_content": content,
    }


def vector_02():
    """TV-02: Per-file hash, UTF-8 with BOM"""
    bom = b"\xef\xbb\xbf"
    text = "résumé\n".encode("utf-8")
    content = bom + text
    return {
        "id": 2,
        "title": "Per-file hash, UTF-8 content with BOM",
        "section": "7.2",
        "input_description": f"UTF-8 BOM (EF BB BF) followed by `résumé\\n` — {len(content)} bytes total",
        "input_hex": content.hex(),
        "input_display": "<BOM>résumé\\n",
        "per_file_hash": sha256_hex(content),
        "raw_content": content,
    }


def vector_03():
    """TV-03: Directory with 3 ASCII-path files (Section 7.3 baseline)"""
    files = {
        "SKILL.md": b"# Code Review\n",
        "config.yaml": b"timeout: 30\n",
        "lib/helpers.py": b"def greet():\n    return 'hello'\n",
    }
    return {
        "id": 3,
        "title": "Directory with 3 ASCII-path files",
        "section": "7.3",
        "input_description": "Three files: `SKILL.md`, `config.yaml`, `lib/helpers.py`",
        "files": {k: {"hex": v.hex(), "display": v.decode(), "hash": sha256_hex(v)} for k, v in files.items()},
        "content_hash": content_hash_directory(files),
    }


def vector_04():
    """TV-04: NFC/NFD collision — MUST error"""
    # é as single codepoint (NFC) = U+00E9
    nfc_name = "caf\u00e9.md"
    # é as e + combining acute (NFD) = U+0065 U+0301
    nfd_name = "cafe\u0301.md"
    # Both normalize to the same NFC string
    files = {
        nfc_name: b"nfc version\n",
        nfd_name: b"nfd version\n",
    }
    try:
        content_hash_directory(files)
        error = False
    except ValueError:
        error = True
    return {
        "id": 4,
        "title": "NFC/NFD variant filenames that collide after normalization",
        "section": "7.3",
        "input_description": f"Two files: `{nfc_name}` (U+00E9) and `{nfd_name}` (U+0065 U+0301) — both NFC-normalize to `café.md`",
        "content_hash": "ERROR: NFC collision — content MUST be rejected as unpublishable",
        "must_error": error,
    }


def vector_05():
    """TV-05: macOS-style NFD path, no collision"""
    # NFD: e + combining acute accent
    nfd_name = "cafe\u0301.md"
    nfc_name = unicodedata.normalize("NFC", nfd_name)
    content = b"coffee recipes\n"
    files = {nfd_name: content}
    return {
        "id": 5,
        "title": "macOS-style NFD path, no collision",
        "section": "7.3",
        "input_description": f"Single file with NFD path `{nfd_name}` (e + U+0301) — NFC-normalizes to `{nfc_name}` (U+00E9)",
        "files": {nfd_name: {"hex": content.hex(), "display": content.decode(), "hash": sha256_hex(content)}},
        "content_hash": content_hash_directory(files),
        "note": f"Path in hash manifest uses NFC form: `{nfc_name}`",
    }


def vector_06():
    """TV-06: Nested subdirectories"""
    files = {
        "a/b/c.txt": b"deep\n",
        "a/b.txt": b"mid\n",
        "a.txt": b"top\n",
    }
    return {
        "id": 6,
        "title": "Nested subdirectories (a/b/c.txt)",
        "section": "7.3",
        "input_description": "Three files at different depths: `a.txt`, `a/b.txt`, `a/b/c.txt`",
        "files": {k: {"hex": v.hex(), "display": v.decode(), "hash": sha256_hex(v)} for k, v in files.items()},
        "content_hash": content_hash_directory(files),
        "note": "Forward-slash paths, sorted by raw UTF-8 bytes: `a.txt` < `a/b.txt` < `a/b/c.txt`",
    }


def vector_07():
    """TV-07: Directory with hidden file"""
    files = {
        "SKILL.md": b"# My Skill\n",
        ".env.example": b"API_KEY=changeme\n",
    }
    return {
        "id": 7,
        "title": "Directory with hidden file (.env.example)",
        "section": "7.3",
        "input_description": "Two files: `SKILL.md` and `.env.example` — hidden file MUST be included",
        "files": {k: {"hex": v.hex(), "display": v.decode(), "hash": sha256_hex(v)} for k, v in files.items()},
        "content_hash": content_hash_directory(files),
        "note": "`.env.example` sorts before `SKILL.md` (0x2E < 0x53)",
    }


def vector_08():
    """TV-08: Directory with empty subdirectory"""
    # Empty dirs are excluded — only the file matters
    files = {
        "README.md": b"# Hello\n",
        # empty_dir/ has no files — excluded from enumeration
    }
    return {
        "id": 8,
        "title": "Directory with empty subdirectory",
        "section": "7.3",
        "input_description": "One file `README.md` and one empty directory `empty_dir/` — empty dir excluded from hash",
        "files": {"README.md": {"hex": files["README.md"].hex(), "display": files["README.md"].decode(), "hash": sha256_hex(files["README.md"])}},
        "content_hash": content_hash_directory(files),
        "note": "Hash is identical to a directory containing only `README.md` — empty dirs are invisible",
    }


def vector_09():
    """TV-09: Internal symlink — MUST error (reject-all symlink policy)"""
    return {
        "id": 9,
        "title": "Internal symlink — MUST error",
        "section": "7.3",
        "input_description": "`target/link.txt` is a symlink to `real.txt` (internal). ALL symlinks are rejected — content MUST error.",
        "content_hash": "ERROR: Symlink rejected — content MUST be rejected as unpublishable",
        "must_error": True,
        "note": "moat_hash.py raises ValueError('Symlink rejected: target/link.txt') for any symlink, internal or external. No resolution or exclusion — reject-all is the normative behavior.",
    }


def vector_10():
    """TV-10: External symlink — MUST error (reject-all symlink policy)"""
    return {
        "id": 10,
        "title": "External symlink — MUST error",
        "section": "7.3",
        "input_description": "`external.txt` is a symlink to `/etc/passwd` (external target). ALL symlinks are rejected — content MUST error.",
        "content_hash": "ERROR: Symlink rejected — content MUST be rejected as unpublishable",
        "must_error": True,
        "note": "moat_hash.py raises ValueError('Symlink rejected: external.txt') before attempting any target resolution. Reject-all eliminates path-traversal attack surface.",
    }


def vector_11():
    """TV-11: Directory containing .json file"""
    json_content = b'{\n  "rules": ["no-eval"],\n  "severity": "error"\n}\n'
    files = {
        "SKILL.md": b"# Linter\n",
        "config.json": json_content,
    }
    return {
        "id": 11,
        "title": "Directory containing .json file",
        "section": "7.3",
        "input_description": "Two files: `SKILL.md` and `config.json` — JSON hashed as raw bytes, NOT canonicalized",
        "files": {k: {"hex": v.hex(), "display": v.decode(), "hash": sha256_hex(v)} for k, v in files.items()},
        "content_hash": content_hash_directory(files),
        "note": "JSON whitespace and key order are preserved in the hash — raw bytes, no JCS",
    }


def vector_12():
    """TV-12: JSON file in directory — no canonicalization"""
    content = b'{"hooks":{"pre_tool_execute":{"command":"echo guard"}}}\n'
    files = {"hooks.json": content}
    return {
        "id": 12,
        "title": "JSON file in directory — no canonicalization",
        "section": "7.3",
        "input_description": "Directory with single JSON file `hooks.json` — hashed as raw bytes, no JCS",
        "files": {"hooks.json": {"hex": content.hex(), "display": content.decode().rstrip("\n"), "hash": sha256_hex(content)}},
        "content_hash": content_hash_directory(files),
    }


def vector_13():
    """TV-13: Binary file (PNG) in directory"""
    # Minimal valid 1x1 white PNG
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"  # PNG signature
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"  # IHDR
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"  # IDAT
        b"\x00\x00\x00\x00IEND\xaeB`\x82"  # IEND
    )
    files = {"icon.png": png_bytes}
    return {
        "id": 13,
        "title": "Binary file (PNG) in directory",
        "section": "7.3",
        "input_description": f"Directory with single binary file `icon.png` — minimal 1×1 white PNG, {len(png_bytes)} bytes",
        "files": {"icon.png": {"hex": png_bytes.hex(), "display": "<binary>", "hash": sha256_hex(png_bytes)}},
        "content_hash": content_hash_directory(files),
    }


def vector_14():
    """TV-14: Sort edge cases (a-b vs a.b vs a/b)"""
    files = {
        "a-b": b"hyphen\n",
        "a.b": b"dot\n",
        "a/b": b"slash\n",
    }
    # UTF-8 byte values: '-' = 0x2D, '.' = 0x2E, '/' = 0x2F
    # Sort order: a-b < a.b < a/b
    return {
        "id": 14,
        "title": "Sort edge cases: a-b vs a.b vs a/b",
        "section": "7.3",
        "input_description": "Three files: `a-b`, `a.b`, `a/b` — tests raw byte sort (0x2D < 0x2E < 0x2F)",
        "files": {k: {"hex": v.hex(), "display": v.decode(), "hash": sha256_hex(v)} for k, v in files.items()},
        "content_hash": content_hash_directory(files),
        "note": "Sort order by UTF-8 bytes: `a-b` (0x2D) < `a.b` (0x2E) < `a/b` (0x2F)",
    }


def vector_15():
    """TV-15: Per-file hash vs content_hash — domain separation (Informative)"""
    content = b"identical content\n"
    filename = "file.txt"
    per_file = f"sha256:{sha256_hex(content)}"
    dir_hash = content_hash_directory({filename: content})
    return {
        "id": 15,
        "title": "Per-file hash vs content_hash — domain separation (Informative)",
        "section": "7.2 + 7.3",
        "input_description": f"Same bytes `identical content\\n` — per-file hash (7.2) vs content_hash (7.3 with `{filename}`)",
        "input_hex": content.hex(),
        "per_file_hash": per_file,
        "directory_hash": dir_hash,
        "hashes_differ": per_file != dir_hash,
    }


def vector_16():
    """TV-16: Symlink cycle — MUST error"""
    # link-a.txt -> link-b.txt -> link-a.txt (cycle)
    # Cannot be represented as a file_map — this is a structural test.
    return {
        "id": 16,
        "title": "Symlink cycle — MUST error",
        "section": "7.3",
        "input_description": "`real.txt` is a regular file. `link-a.txt` symlinks to `link-b.txt`, `link-b.txt` symlinks to `link-a.txt` — cycle.",
        "content_hash": "ERROR: Symlink cycle detected — content MUST be rejected as unpublishable",
        "must_error": True,
    }


# ─── Path rejects (moat-spec.md §Content Hashing) ──────────────────────────
#
# Paths are given as raw bytes. Not every platform can create every name:
# Windows forbids U+0001-U+001F in a file name (it permits U+007F) and stores
# names as UTF-16, and macOS refuses a name that is not valid UTF-8. A verifier on such a platform never meets
# the input; one that can create it MUST refuse it as the vector says.

PATH_REJECT_KINDS = {
    "not_utf8": "Path is not valid UTF-8",
    "control_char": "Path contains a control character",
    "collision": "NFC collision",
}


def _path_kind(err: ValueError) -> str:
    msg = str(err)
    for kind, keyword in (("not_utf8", "not valid UTF-8"), ("control_char", "control character"),
                          ("collision", "collision")):
        if keyword in msg:
            return kind
    return "other"


def _show_path(p: bytes) -> str:
    """A raw path for display: invalid bytes and C0/DEL/C1 characters as \\xNN."""
    return "".join(f"\\x{ord(c):02x}" if ord(c) < 0x20 or 0x7F <= ord(c) <= 0x9F else c
                   for c in p.decode("utf-8", "backslashreplace"))


def _path_vector(vid: int, title: str, files: dict[bytes, bytes], platforms: str, note: str,
                 reject: str | None) -> dict:
    v = {
        "id": vid,
        "title": title,
        "section": "Content Hashing",
        "input_description": "; ".join(f"`{p.hex()}` ({_show_path(p)})" for p in files),
        "raw_files": files,
        "files": {_show_path(p): {"path_hex": p.hex(), "hex": d.hex(), "display": d.decode(), "hash": sha256_hex(d)}
                  for p, d in files.items()},
        "platforms": platforms,
        "note": note,
    }
    try:
        h = content_hash_directory(files)
        kind = None
    except ValueError as err:
        kind = _path_kind(err)
    assert kind == reject, f"TV-{vid}: expected {reject}, got {kind}"
    if reject is None:
        v["content_hash"] = h
    else:
        v["must_error"] = True
        v["reject"] = reject
        v["content_hash"] = f"ERROR: {PATH_REJECT_KINDS[reject]} — content MUST be rejected as unpublishable"
    return v


_NO_WINDOWS = "Not creatable on Windows, which forbids U+0001-U+001F in file names."
_NO_MACOS = "Not creatable on macOS, which refuses file names that are not valid UTF-8."
_NO_WINDOWS_BYTES = ("Not creatable on Windows, whose file names are UTF-16; there the counterpart is a "
                     "name holding an unpaired surrogate.")


def vector_23():
    return _path_vector(23, "Line feed in a file name — MUST error",
                        {b"SKILL.md": b"# Skill\n", b"notes\n.md": b"x\n"}, _NO_WINDOWS,
                        "A newline in a path would split its sha256sum manifest line in two.",
                        "control_char")


def vector_24():
    return _path_vector(24, "Carriage return in a directory name — MUST error",
                        {b"SKILL.md": b"# Skill\n", b"lib\r/a.py": b"x\n"}, _NO_WINDOWS,
                        "The scan covers every path component, not only the final name.",
                        "control_char")


def vector_25():
    return _path_vector(25, "DEL (U+007F) in a file name — MUST error",
                        {b"SKILL.md": b"# Skill\n", b"a\x7fb.md": b"x\n"},
                        "Creatable on Linux, macOS and Windows.",
                        "U+007F is refused along with U+0000-U+001F.",
                        "control_char")


def vector_26():
    return _path_vector(26, "C1 control (U+0080) in a file name — accepted",
                        {b"SKILL.md": b"# Skill\n", "a\u0080b.md".encode(): b"x\n"},
                        "Creatable on Linux, macOS and Windows.",
                        "U+0080-U+009F are not refused; the path is hashed like any other.",
                        None)


def vector_27():
    return _path_vector(27, "File name that is not valid UTF-8 — MUST error",
                        {b"SKILL.md": b"# Skill\n", b"notes\xff.md": b"x\n"}, f"{_NO_MACOS} {_NO_WINDOWS_BYTES}",
                        "Byte 0xFF never occurs in UTF-8.",
                        "not_utf8")


def vector_28():
    return _path_vector(28, "Control character and NFC collision together — control character reported",
                        {"café.md".encode(): b"nfc\n", "café.md".encode(): b"nfd\n",
                         b"z\x01.md": b"x\n"}, _NO_WINDOWS,
                        "Both path scans finish before collision detection, so the control "
                        "character is the reported reject.",
                        "control_char")


def vector_29():
    return _path_vector(29, "Invalid UTF-8 and control character together — invalid UTF-8 reported",
                        {b"a\nb.md": b"x\n", b"c\xff.md": b"y\n"}, f"{_NO_WINDOWS} {_NO_MACOS}",
                        "Every path is checked for valid UTF-8 before any is checked for control "
                        "characters, so the reported reject does not depend on enumeration order.",
                        "not_utf8")


PATH_REJECT_VECTORS = [vector_23, vector_24, vector_25, vector_26, vector_27, vector_28, vector_29]


# ─── ACIF content items (moat-spec.md §ACIF Content Items) ─────────────────
#
# The Content Hash of an ACIF content item is "sha256:" + the ACIF attestation
# input digest ([ACIF-REGISTRY] §6) over the item's body_hash and metadata_hash.
# body_hash values below are pinned by ACIF's own conformance vectors, so the
# MOAT reference cannot drift from ACIF without this script failing.

ACIF_PINNED_BODY_HASH = {
    "TV-SKILL-g case_1": "sha256:12d3cb2f53305b53fff6ca4ff1166fd1d063b1319642e0a0906a5539c8fa57b7",
    "TV-SKILL-g case_3": "sha256:fef9a3e615ab4d41c1a990908bf9a3e5b47f70a73eaa16fc7e1578c9f4ab60df",
    "TV-SKILL-n":        "sha256:b08c2af8a9d5c2eced158b49a13bacfe3d0a22221b965bd2a46672bc5b8f9648",
}

# [ACIF-CORE] TV-L3-e accepted cases: (body_hash, metadata_hash or None, attestation_hash).
ACIF_ATTESTATION_INPUT_PINNED = [
    ("sha256:916e570331167c16f8112573d1b6020c134cc3d4019e8011693676d019b88ffe", None,
     "27af3dc088e0020d172ad172e73ff6a85f098f1267529ca046133823916b1cdc"),
    ("sha256:916e570331167c16f8112573d1b6020c134cc3d4019e8011693676d019b88ffe",
     "sha256:b68bf2e4cbd6b9123d23de684498157adeaf4915e65435a95a556ac27ec50316",
     "fd47d05d539e9e2034eab62fe5274cf950fd5a271d9d2b9ea9f5b0e0ef8e0f22"),
]


def attestation_input_preimage(body_hash: str, metadata_hash: str | None) -> bytes:
    """[ACIF-REGISTRY] §6, restated independently of moat_hash.py."""
    mh = "null" if metadata_hash is None else metadata_hash
    return b"acif-attestation-input-v1\n" + body_hash.encode() + b"\n" + mh.encode() + b"\n"


def metadata_hash_flat(publisher_section: dict[str, str] | None) -> str | None:
    """[ACIF-PUBLISHER] §6 for a flat object of ASCII strings, where JCS equals sorted compact JSON."""
    if publisher_section is None:
        return None
    jcs = json.dumps(publisher_section, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + sha256_hex(jcs.encode("utf-8") + b"\n")


def canonical_payload(content_hash: str) -> bytes:
    return json.dumps({"_version": 1, "content_hash": content_hash},
                      separators=(",", ":"), sort_keys=True).encode("utf-8")


def _materialize(file_map: dict[str, bytes], root: pathlib.Path) -> None:
    for rel, data in file_map.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def _acif_vector(vid, title, files, entry_file, publisher_section, pinned_label, note):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir)
        _materialize(files, root)
        body_hash = moat_hash.acif_body_hash(root, entry_file)
        directory_hash = moat_hash.content_hash(root)
        reference_content_hash = moat_hash.acif_content_hash(root, entry_file, publisher_section)
    assert body_hash == ACIF_PINNED_BODY_HASH[pinned_label], \
        f"{vid}: body_hash {body_hash} differs from ACIF {pinned_label}"
    metadata_hash = metadata_hash_flat(publisher_section)
    preimage = attestation_input_preimage(body_hash, metadata_hash)
    content_hash = f"sha256:{sha256_hex(preimage)}"
    assert content_hash == reference_content_hash, f"{vid}: moat_hash.acif_content_hash disagrees"
    payload = canonical_payload(content_hash)
    return {
        "id": vid,
        "title": title,
        "files": files,
        "entry_file": entry_file,
        "publisher_section": publisher_section,
        "body_hash": body_hash,
        "body_hash_source": pinned_label,
        "metadata_hash": metadata_hash,
        "preimage": preimage,
        "content_hash": content_hash,
        "payload": payload,
        "payload_sha256": sha256_hex(payload),
        "directory_hash": directory_hash,
        "note": note,
    }


ACIF_SKILL_BODY = b"Use this to demo classification.\n"


def acif_vectors() -> list[dict]:
    v1 = _acif_vector(
        "TV-ACIF-01", "Single-file ACIF skill, no frontmatter, metadata_hash absent",
        {"SKILL.md": ACIF_SKILL_BODY}, "SKILL.md", None, "TV-SKILL-g case_1",
        "MH is the four bytes `null`. The directory hash differs from body_hash: "
        "a single-file body_hash is the entry file's own digest, not a manifest digest.")
    v2 = _acif_vector(
        "TV-ACIF-02", "Single-file ACIF skill, CRLF frontmatter, metadata_hash present",
        {"SKILL.md": b"---\r\ndescription: Demo skill.\r\n---\r\n" + ACIF_SKILL_BODY.replace(b"\n", b"\r\n")},
        "SKILL.md", {"description": "Demo skill."}, "TV-SKILL-g case_1",
        "body_hash equals TV-ACIF-01 (frontmatter stripped, CRLF normalized); the Content "
        "Hash differs from TV-ACIF-01 because metadata_hash is present.")
    v3 = _acif_vector(
        "TV-ACIF-03", "Multi-file ACIF skill, no frontmatter, metadata_hash absent",
        {"SKILL.md": ACIF_SKILL_BODY, "scripts/run.sh": b"#!/bin/sh\necho hi\n"},
        "SKILL.md", None, "TV-SKILL-g case_3",
        "body_hash equals the MOAT directory algorithm output for the same bytes; the Content Hash "
        "still differs, because it is the attestation input digest.")
    v4 = _acif_vector(
        "TV-ACIF-04", "Multi-file ACIF skill, entry-file frontmatter, metadata_hash present",
        {"SKILL.md": b"---\ndescription: one\n---\nProse body.\n", "scripts/run.sh": b"#!/bin/sh\necho hi\n"},
        "SKILL.md", {"description": "one"}, "TV-SKILL-n",
        "body_hash differs from the MOAT directory algorithm output: the entry file's frontmatter "
        "is stripped from the multi-file manifest too.")
    assert v1["body_hash"] == v2["body_hash"] and v1["content_hash"] != v2["content_hash"]
    assert v1["body_hash"] != v1["directory_hash"]
    assert v3["body_hash"] == v3["directory_hash"]
    assert v4["body_hash"] != v4["directory_hash"]
    return [v1, v2, v3, v4]


# ─── Author-key profile (moat-spec.md §Author-Key Profile) ──────────────────
#
# Test keys are derived from fixed seeds and are public; never use them to sign
# real content. Security-key signatures are produced by software emulation of
# a FIDO authenticator.

def _seed(label: str) -> bytes:
    return hashlib.sha256(f"moat-test-key-{label}".encode()).digest()


def _ed_blob(label: str) -> bytes:
    return ak.key_blob_ed25519(ak.ed25519_public(_seed(label)))


def _p256_scalar(label: str) -> int:
    return int.from_bytes(_seed(label), "big") % ak._EN


# The Ed25519 identity point's encoding (y = 1, x = 0).
ED25519_IDENTITY = b"\x01" + b"\x00" * 31


def author_key_fixtures() -> dict:
    keys = {
        "A": _ed_blob("A"),
        "B": _ed_blob("B"),
        "C": _ed_blob("C"),
        "D": ak.key_blob_sk_ed25519(ak.ed25519_public(_seed("D"))),
        "E": ak.key_blob_sk_ecdsa(ak.p256_public(_p256_scalar("E"))),
        # Z is the identity point, a small-order key with no secret behind it.
        "Z": ak.key_blob_ed25519(ED25519_IDENTITY),
    }
    line = {k: ak.allowed_signers_line(b) for k, b in keys.items()}

    def seq(n: int) -> str:
        return f"# moat-sequence: {n}\n"

    lists = {
        "L1": f"# allowed signers for the test source\n{seq(0)}{line['A']}\n".encode(),
        "L2": f"{seq(1)}{line['A']}\n{line['C']}\n".encode(),
        "L1+B": f"{seq(1)}{line['A']}\n{line['B']}\n".encode(),
        "L3": f"{seq(2)}{line['A']}\n".encode(),
        "LD": f"{seq(0)}{line['D']}\n".encode(),
        "LE": f"{seq(0)}{line['E']}\n".encode(),
        "LBAD": f"{seq(0)}{ak.fingerprint(keys['B'])} {line['A'].split(' ', 1)[1]}\n".encode(),
        "LNOSEQ": f"{line['A']}\n".encode(),
        "LZ": f"{seq(0)}{line['Z']}\n".encode(),
    }
    return {"keys": keys, "lines": line, "lists": lists}


AK_SOURCE_URI = "https://github.com/owner/repo"
AK_OTHER_SOURCE_URI = "https://github.com/owner/other-repo"


def author_key_vectors() -> list[dict]:
    fx = author_key_fixtures()
    keys, lists = fx["keys"], fx["lists"]
    item = acif_vectors()[3]
    ch = item["content_hash"]
    msg = ak.item_message(ch)
    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir)
        tampered = dict(item["files"], **{"scripts/run.sh": b"#!/bin/sh\necho bye\n"})
        _materialize(tampered, root)
        tampered_ch = moat_hash.acif_content_hash(root, "SKILL.md", item["publisher_section"])
    assert tampered_ch != ch

    sig_a = ak.sign_ed25519(_seed("A"), msg)
    sig_b = ak.sign_ed25519(_seed("B"), msg)
    sig_c = ak.sign_ed25519(_seed("C"), msg)
    sig_d = ak.sign_sk_ed25519_emulated(_seed("D"), msg)
    sig_e = ak.sign_sk_ecdsa_emulated(_p256_scalar("E"), msg)
    sig_d_noup = ak.sign_sk_ed25519_emulated(_seed("D"), msg, flags=0x00)
    # A = R = identity and S = 0 satisfy [S]B = R + [k]A for every message.
    sig_z = ak._sshsig(keys["Z"], ak._string(ak.KT_ED25519) + ak._string(ED25519_IDENTITY + bytes(32)))
    pad = ak.MAX_ARMOR_BYTES + 1 - len(sig_a.encode())
    sig_a_over_cap = sig_a + "\n" * pad
    src = AK_SOURCE_URI
    chg_b = ak.sign_ed25519(_seed("B"), ak.list_change_message(src, lists["L1"], lists["L1+B"]))
    chg_a = ak.sign_ed25519(_seed("A"), ak.list_change_message(src, lists["L1"], lists["L2"]))
    # A adds B (L1 -> L1+B), then removes B (L1+B -> L3); TV-AK-10 replays the addition.
    chg_a_add_b = ak.sign_ed25519(_seed("A"), ak.list_change_message(src, lists["L1"], lists["L1+B"]))
    chg_a_remove_b = ak.sign_ed25519(_seed("A"), ak.list_change_message(src, lists["L1+B"], lists["L3"]))
    assert ak.verify_list_change(src, lists["L1"], lists["L1+B"], chg_a_add_b) == ak.OK
    assert ak.verify_list_change(src, lists["L1+B"], lists["L3"], chg_a_remove_b) == ak.OK

    def item_vec(vid, title, signer, sig, list_name, content_hash, expected, note=""):
        got = ak.verify_item(content_hash, sig, lists[list_name])
        assert got == expected, f"{vid}: expected {expected}, got {got}"
        return {"id": vid, "kind": "item", "title": title, "signer": signer, "list": list_name,
                "content_hash": content_hash, "message": ak.item_message(content_hash),
                "signature": sig, "expected": expected, "note": note}

    def change_vec(vid, title, signer, sig, old, new, expected, note="", source_uri=src):
        got = ak.verify_list_change(source_uri, lists[old], lists[new], sig)
        assert got == expected, f"{vid}: expected {expected}, got {got}"
        return {"id": vid, "kind": "list_change", "title": title, "signer": signer,
                "source_uri": source_uri, "previous_list": old, "new_list": new,
                "message": ak.list_change_message(source_uri, lists[old], lists[new]),
                "signature": sig, "expected": expected, "note": note}

    vectors = [
        item_vec("TV-AK-01", "Valid item signature, ssh-ed25519", "A", sig_a, "L1", ch, ak.OK),
        item_vec("TV-AK-02", "Item signed by a key not in the list", "B", sig_b, "L1", ch, ak.SIGNER_NOT_ALLOWED,
                 "The signature is valid; the signer is not allowed."),
        item_vec("TV-AK-03", "Tampered body: recomputed Content Hash differs from the signed one", "A", sig_a, "L1",
                 tampered_ch, ak.SIGNATURE_INVALID,
                 "scripts/run.sh installed as `echo bye`; the verifier recomputes body_hash, so the "
                 "message it checks no longer matches TV-AK-01's signature."),
        change_vec("TV-AK-04", "List change signed by a key the recorded list does not allow", "B", chg_b,
                   "L1", "L1+B", ak.SIGNER_NOT_ALLOWED,
                   "B adds itself; the recorded list (L1) allows only A, so the change is refused."),
        change_vec("TV-AK-05", "Valid list rotation", "A", chg_a, "L1", "L2", ak.OK,
                   "After the rotation the client records L2; TV-AK-05b then accepts an item signed by C."),
        item_vec("TV-AK-05b", "Item signed by a key added in the rotation", "C", sig_c, "L2", ch, ak.OK,
                 "Against the previous list L1 the same signature is signer_not_allowed."),
        item_vec("TV-AK-06", "Valid item signature, sk-ssh-ed25519@openssh.com", "D", sig_d, "LD", ch, ak.OK),
        item_vec("TV-AK-07", "Valid item signature, sk-ecdsa-sha2-nistp256@openssh.com", "E", sig_e, "LE", ch, ak.OK),
        item_vec("TV-AK-08", "Security-key signature without the user-presence flag", "D", sig_d_noup, "LD", ch,
                 ak.SIGNATURE_INVALID, "flags byte is 0x00; the user-presence bit (0x01) is required."),
        item_vec("TV-AK-09", "Allowed-signers line whose principal is not the key's fingerprint", "A", sig_a,
                 "LBAD", ch, ak.LIST_MALFORMED,
                 "The line names B's fingerprint beside A's key; the whole list is refused."),
        change_vec("TV-AK-10", "Replay of an earlier list change after the key it added was removed", "A",
                   chg_a_add_b, "L3", "L1+B", ak.SEQUENCE_NOT_GREATER,
                   "A added B (L1 -> L1+B, sequence 1) and later removed it (L1+B -> L3, sequence 2). "
                   "Replaying L1+B and its signed change against the recorded L3 is refused: 1 is not "
                   "greater than 2."),
        change_vec("TV-AK-11", "List change signed for another source_uri", "A", chg_a, "L1", "L2",
                   ak.SIGNATURE_INVALID,
                   f"TV-AK-05's signature binds {src}; checked for {AK_OTHER_SOURCE_URI}, which "
                   "records the same L1, the message differs and the signature does not verify.",
                   source_uri=AK_OTHER_SOURCE_URI),
        item_vec("TV-AK-12", "Allowed-signers list without a sequence line", "A", sig_a, "LNOSEQ", ch,
                 ak.LIST_MALFORMED, "Every list carries exactly one `# moat-sequence: <n>` line."),
        item_vec("TV-AK-13", "Small-order key: identity A and R with S = 0", "Z", sig_z, "LZ", ch,
                 ak.SIGNATURE_INVALID,
                 "Z is the identity point. A = R = identity and S = 0 satisfy the cofactorless equation "
                 "for any message, so a list naming Z would accept anything; A and R of small order "
                 "are refused."),
        item_vec("TV-AK-14", "Armored signature over 16384 bytes", "A", sig_a_over_cap, "L1", ch,
                 ak.SIGNATURE_INVALID,
                 f"TV-AK-01's signature followed by {pad} LF bytes, 16385 bytes in all. Stripped, it "
                 "is TV-AK-01's valid signature; the cap refuses it before any decoding."),
    ]
    assert ak.verify_item(ch, sig_c, lists["L1"]) == ak.SIGNER_NOT_ALLOWED
    return vectors


def _print_acif(v: dict) -> None:
    print(f"{v['id']}: {v['title']}")
    for path, data in sorted(v["files"].items()):
        print(f"    {path}: {data!r}")
    print(f"  entry_file:        {v['entry_file']}")
    ps = None if v["publisher_section"] is None else json.dumps(v["publisher_section"], sort_keys=True, separators=(",", ":"))
    print(f"  publisher_section: {ps}")
    print(f"  body_hash:         {v['body_hash']}  (= ACIF {v['body_hash_source']})")
    print(f"  metadata_hash:     {v['metadata_hash'] or 'absent'}")
    print(f"  preimage:          {v['preimage']!r}")
    print(f"  content_hash:      {v['content_hash']}")
    print(f"  payload:           {v['payload'].decode()}")
    print(f"  payload SHA-256:   {v['payload_sha256']}")
    print(f"  directory algorithm: {v['directory_hash']}  (equals body_hash: {v['directory_hash'] == v['body_hash']})")
    print(f"  Note: {v['note']}")
    print()


def _print_ak_fixtures(fx: dict) -> None:
    print("Author-key test keys (seed = SHA-256(\"moat-test-key-<label>\"); E's P-256 scalar is that seed mod n):")
    for label, line in fx["lines"].items():
        print(f"  {label}: {line}")
    print("Allowed-signers lists (digest over canonical text):")
    for name, data in fx["lists"].items():
        print(f"  {name}: {ak.list_digest(data)}")
        for ln in data.decode().splitlines():
            print(f"      | {ln}")
    print()


def _print_ak(v: dict) -> None:
    print(f"{v['id']}: {v['title']}")
    print(f"  signer: {v['signer']}")
    if v["kind"] == "item":
        print(f"  allowed-signers list: {v['list']}")
        print(f"  verifier's recomputed content_hash: {v['content_hash']}")
    else:
        print(f"  source_uri: {v['source_uri']}")
        print(f"  recorded list: {v['previous_list']}  ->  new list: {v['new_list']}")
    print(f"  message checked: {v['message']!r}")
    for ln in v["signature"].rstrip("\n").splitlines():
        print(f"    {ln}")
    print(f"  Expected: {v['expected']}")
    if v["note"]:
        print(f"  Note: {v['note']}")
    print()


# ─── Output ────────────────────────────────────────────────────────────────

def print_separator():
    print("─" * 72)


def main():
    generators = [
        vector_01, vector_02, vector_03, vector_04, vector_05,
        vector_06, vector_07, vector_08, vector_09, vector_10,
        vector_11, vector_12, vector_13, vector_14, vector_15,
        vector_16, *PATH_REJECT_VECTORS,
    ]

    print("MOAT Test Vectors — Generated Output")
    print("=" * 72)
    print()

    for gen in generators:
        v = gen()
        print(f"TV-{v['id']:02d}: {v['title']}")
        print(f"  Section: {v['section']}")
        print(f"  Input: {v['input_description']}")

        if "files" in v:
            for path, info in sorted(v["files"].items()):
                display = info.get("display", "<binary>").rstrip("\n")
                print(f"    {path}: {info['hash']}")
                if "path_hex" in info:
                    print(f"      path hex: {info['path_hex']}")
                print(f"      content: {display!r}")

        if "input_hex" in v:
            hex_str = v["input_hex"]
            if len(hex_str) > 80:
                print(f"    hex: {hex_str[:80]}...")
            else:
                print(f"    hex: {hex_str}")

        if "must_error" in v:
            print(f"  Expected: ERROR (must_error={v['must_error']})")
            print(f"  Result: {v['content_hash']}")
        elif "per_file_hash" in v and "directory_hash" in v:
            print(f"  Per-file hash:     sha256:{v['per_file_hash']}" if not v['per_file_hash'].startswith('sha256:') else f"  Per-file hash:     {v['per_file_hash']}")
            print(f"  Directory hash:    {v['directory_hash']}")
            print(f"  Hashes differ:     {v['hashes_differ']}")
        elif "per_file_hash" in v:
            print(f"  per_file_hash: {v['per_file_hash']}")
        elif "content_hash" in v:
            print(f"  content_hash: {v['content_hash']}")

        if "note" in v:
            print(f"  Note: {v['note']}")
        if "platforms" in v:
            print(f"  Platforms: {v['platforms']}")
        print()

    print_separator()
    print("ACIF content items (moat-spec.md §ACIF Content Items)")
    print()
    for v in acif_vectors():
        _print_acif(v)

    print_separator()
    print("Author-key profile (moat-spec.md §Author-Key Profile)")
    print()
    _print_ak_fixtures(author_key_fixtures())
    for v in author_key_vectors():
        _print_ak(v)

    # Verify determinism — run twice and compare
    print_separator()
    print("Determinism check: regenerating all hashes...")
    for gen in generators:
        v1 = gen()
        v2 = gen()
        for key in ("content_hash", "per_file_hash", "directory_hash"):
            if key in v1 and key in v2:
                assert v1[key] == v2[key], f"TV-{v1['id']} non-deterministic on {key}!"
    print(f"  All {len(generators)} content hash vectors are deterministic. ✓")
    assert acif_vectors() == acif_vectors(), "ACIF vectors non-deterministic"
    assert author_key_vectors() == author_key_vectors(), "author-key vectors non-deterministic"
    print("  ACIF and author-key vectors are deterministic. ✓")

    print_separator()
    print("Cross-validation: generate_test_vectors vs moat_hash.py...")

    _xv_cases: list[tuple[str, dict[str, bytes]]] = [
        ("TV-03 (3 ASCII-path files)", {
            "SKILL.md": b"# Code Review\n",
            "config.yaml": b"timeout: 30\n",
            "lib/helpers.py": b"def greet():\n    return 'hello'\n",
        }),
        ("TV-07 (hidden file)", {
            "SKILL.md": b"# My Skill\n",
            ".env.example": b"API_KEY=changeme\n",
        }),
        ("TV-14 (sort edge cases)", {
            "a-b": b"hyphen\n",
            "a.b": b"dot\n",
            "a/b": b"slash\n",
        }),
    ]

    all_ok = True
    for label, file_map in _xv_cases:
        expected = content_hash_directory(file_map)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            for rel, data in file_map.items():
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
            got = moat_hash.content_hash(root)
        if expected == got:
            print(f"  {label}: OK ({expected})")
        else:
            print(f"  {label}: MISMATCH")
            print(f"    generate_test_vectors: {expected}")
            print(f"    moat_hash.py:          {got}")
            all_ok = False

    for gen in PATH_REJECT_VECTORS:
        v = gen()
        label = f"TV-{v['id']} ({v['title']})"
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            try:
                for rel, data in v["raw_files"].items():
                    p = root / os.fsdecode(rel)
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(data)
            except (OSError, UnicodeError) as err:
                print(f"  {label}: SKIPPED, this platform cannot create the input ({err.__class__.__name__})")
                continue
            try:
                got, got_kind = moat_hash.content_hash(root), None
            except ValueError as err:
                got, got_kind = None, _path_kind(err)
        want_kind = v.get("reject")
        if got_kind == want_kind and (want_kind is not None or got == v["content_hash"]):
            print(f"  {label}: OK ({want_kind or got})")
        else:
            print(f"  {label}: MISMATCH (expected {want_kind or v['content_hash']}, "
                  f"moat_hash {got_kind or got})")
            all_ok = False

    for body_hash, metadata_hash, expected in ACIF_ATTESTATION_INPUT_PINNED:
        got = sha256_hex(moat_hash.acif_attestation_input_preimage(body_hash, metadata_hash))
        mine = sha256_hex(attestation_input_preimage(body_hash, metadata_hash))
        label = f"ACIF TV-L3-e (metadata_hash {'present' if metadata_hash else 'absent'})"
        if got == mine == expected:
            print(f"  {label}: OK ({expected})")
        else:
            print(f"  {label}: MISMATCH (expected {expected}, moat_hash {got}, generator {mine})")
            all_ok = False

    if all_ok:
        print("  Cross-validation passed. ✓")
    else:
        raise AssertionError("Cross-validation FAILED — generate_test_vectors and moat_hash.py disagree")


if __name__ == "__main__":
    main()
