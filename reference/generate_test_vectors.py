#!/usr/bin/env python3
"""
MOAT Specification — Test Vector Generator

Implements the content hash algorithms from Sections 7.2, 7.3, 7.4, and 8
of the MOAT spec, then generates all 15 test vectors with exact byte inputs
and expected SHA-256 outputs.

Usage: python3 generate_test_vectors.py
"""

import hashlib
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(__file__))
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
    Paths use forward slashes, no leading ./ or trailing /.

    Manifest format: sha256sum — "{hash}  {path}\n" per entry.
    This matches moat_hash.py (the normative reference) and POSIX sha256sum output,
    making individual manifest entries verifiable with standard Unix tools.
    """
    entries = []
    for path, data in file_map.items():
        # Step 3: NFC-normalize paths
        nfc_path = unicodedata.normalize("NFC", path)
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


# ─── Output ────────────────────────────────────────────────────────────────

def print_separator():
    print("─" * 72)


def main():
    generators = [
        vector_01, vector_02, vector_03, vector_04, vector_05,
        vector_06, vector_07, vector_08, vector_09, vector_10,
        vector_11, vector_12, vector_13, vector_14, vector_15,
        vector_16,
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
        print()

    # Verify determinism — run twice and compare
    print_separator()
    print("Determinism check: regenerating all hashes...")
    for gen in generators:
        v1 = gen()
        v2 = gen()
        for key in ("content_hash", "per_file_hash", "directory_hash"):
            if key in v1 and key in v2:
                assert v1[key] == v2[key], f"TV-{v1['id']} non-deterministic on {key}!"
    print("  All 16 vectors are deterministic. ✓")

    print_separator()
    print("Cross-validation: generate_test_vectors vs moat_hash.py...")
    import tempfile, pathlib

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

    if all_ok:
        print("  Cross-validation passed. ✓")
    else:
        raise AssertionError("Cross-validation FAILED — generate_test_vectors and moat_hash.py disagree")


if __name__ == "__main__":
    main()
