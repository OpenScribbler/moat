#!/usr/bin/env python3
"""
MOAT — Text Normalization Integration Tests (TV-17 through TV-22)

Tests the full file I/O pipeline of moat_hash.py against real filesystem fixtures.
Unlike generate_test_vectors.py (which tests the manifest format using dict[str, bytes]),
this script tests BOM stripping, CRLF normalization, and binary classification
by writing real files to a temp directory and calling moat_hash.content_hash().

Each test includes the intermediate normalized byte sequence so implementers can
pinpoint exactly where their normalization diverges from the spec.

Usage: python3 test_normalization.py
"""

import hashlib
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import moat_hash


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_single_file_hash(filename: str, content: bytes) -> str:
    """Write one file to a temp dir and return moat_hash.content_hash()."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir)
        p = root / filename
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return moat_hash.content_hash(root)


def content_hash_from_manifest_entries(entries: list[tuple[str, str]]) -> str:
    """
    Build a content_hash from (path, file_hash) pairs using sha256sum format.
    Used to compute expected values independently of moat_hash.py internals.
    """
    manifest = "".join(f"{h}  {p}\n" for p, h in entries).encode("utf-8")
    return "sha256:" + sha256_hex(manifest)


# -- TV-17: CRLF normalization ------------------------------------------------

def test_tv17():
    """
    TV-17: .md file with CRLF line endings hashes identically to LF-only version.

    Intermediate normalized bytes: CRLF sequences are replaced with LF.
    The file content '# Title\\r\\nSome text\\r\\nAnother line\\r\\n' normalizes to
    '# Title\\nSome text\\nAnother line\\n' before SHA-256 is computed.
    """
    crlf_content = b"# Title\r\nSome text\r\nAnother line\r\n"
    lf_content   = b"# Title\nSome text\nAnother line\n"

    intermediate = lf_content
    intermediate_hash = sha256_hex(intermediate)

    expected_hash = content_hash_from_manifest_entries([("title.md", intermediate_hash)])
    lf_hash       = content_hash_from_manifest_entries([("title.md", sha256_hex(lf_content))])

    assert expected_hash == lf_hash, "Sanity: expected equals LF-only hash"

    got = run_single_file_hash("title.md", crlf_content)

    assert got == expected_hash, (
        f"TV-17 FAILED\n"
        f"  Expected: {expected_hash}\n"
        f"  Got:      {got}\n"
        f"  Intermediate bytes (CRLF normalized to LF):\n"
        f"    hex: {intermediate.hex()}\n"
        f"    utf-8: {intermediate!r}\n"
        f"  Per-file hash of intermediate: {intermediate_hash}"
    )
    return True


# -- TV-18: UTF-8 BOM stripping -----------------------------------------------

def test_tv18():
    """
    TV-18: .py file with UTF-8 BOM hashes identically to BOM-stripped version.

    Intermediate normalized bytes: the UTF-8 BOM (EF BB BF) is removed from the
    start of the file. 'def hello():\\n    pass\\n' is what enters SHA-256.
    """
    bom            = b"\xef\xbb\xbf"
    bom_content    = bom + b"def hello():\n    pass\n"
    stripped       = b"def hello():\n    pass\n"

    intermediate      = stripped
    intermediate_hash = sha256_hex(intermediate)

    expected_hash = content_hash_from_manifest_entries([("module.py", intermediate_hash)])
    stripped_hash = content_hash_from_manifest_entries([("module.py", sha256_hex(stripped))])

    assert expected_hash == stripped_hash, "Sanity: expected equals BOM-stripped hash"

    got = run_single_file_hash("module.py", bom_content)

    assert got == expected_hash, (
        f"TV-18 FAILED\n"
        f"  Expected: {expected_hash}\n"
        f"  Got:      {got}\n"
        f"  Intermediate bytes (BOM stripped):\n"
        f"    hex: {intermediate.hex()}\n"
        f"    utf-8: {intermediate!r}\n"
        f"  Per-file hash of intermediate: {intermediate_hash}"
    )
    return True


# -- TV-19: Extensionless dotfile treated as binary ----------------------------

def test_tv19():
    """
    TV-19: .gitignore (extensionless dotfile) is treated as binary, not text.

    moat_hash.final_extension('.gitignore') returns '' because the name starts
    with '.' and has no other dot. '' is not in TEXT_EXTENSIONS, so the file
    is classified as binary and hashed as raw bytes with no normalization.

    Intermediate 'normalized' bytes: identical to raw file bytes (no transformation).
    """
    content = b"*.pyc\n__pycache__/\n.env\n"

    intermediate      = content
    intermediate_hash = sha256_hex(intermediate)

    expected_hash = content_hash_from_manifest_entries([(".gitignore", intermediate_hash)])
    got           = run_single_file_hash(".gitignore", content)

    assert got == expected_hash, (
        f"TV-19 FAILED\n"
        f"  Expected: {expected_hash}\n"
        f"  Got:      {got}\n"
        f"  Intermediate bytes (binary — no transformation):\n"
        f"    hex: {intermediate.hex()}\n"
        f"  Per-file hash of intermediate: {intermediate_hash}\n"
        f"  Note: final_extension('.gitignore') == '' — not in TEXT_EXTENSIONS"
    )
    return True


# -- TV-20: NUL byte forces binary classification -----------------------------

def test_tv20():
    """
    TV-20: .json file with a NUL byte in the first 8KB is treated as binary.

    Despite .json being in TEXT_EXTENSIONS, moat_hash.is_text() scans the first
    NUL_SCAN (8192) bytes for NUL bytes. A NUL byte in that window forces binary.

    Intermediate 'normalized' bytes: identical to raw file bytes (no transformation).
    """
    content = b'{"key": "value\x00more"}\n'

    intermediate      = content
    intermediate_hash = sha256_hex(intermediate)

    expected_hash = content_hash_from_manifest_entries([("data.json", intermediate_hash)])
    got           = run_single_file_hash("data.json", content)

    assert got == expected_hash, (
        f"TV-20 FAILED\n"
        f"  Expected: {expected_hash}\n"
        f"  Got:      {got}\n"
        f"  Intermediate bytes (binary override — NUL detected):\n"
        f"    hex: {intermediate.hex()}\n"
        f"  Per-file hash of intermediate: {intermediate_hash}\n"
        f"  Note: .json is in TEXT_EXTENSIONS but NUL in first 8KB forces binary"
    )
    return True


# -- TV-21: CR at chunk boundary -----------------------------------------------

def test_tv21():
    """
    TV-21: CR at chunk boundary (65535th byte is CR, 65536th is LF) is normalized
    as a single CRLF -> LF, not as lone-CR + lone-LF.

    The read buffer (CHUNK) is 65536 bytes. A file where the last byte of chunk 1
    is CR (0x0D) and the first byte of chunk 2 is LF (0x0A) tests the pending_cr
    logic in moat_hash._hash_text(). The CRLF pair MUST be collapsed to a single LF.

    Intermediate normalized bytes: 65535 'a' bytes + b'\\nend\\n'
    (65541 raw bytes -> 65540 normalized bytes)
    """
    before_cr = b"a" * 65535
    raw_content = before_cr + b"\r\nend\n"

    intermediate      = before_cr + b"\nend\n"
    intermediate_hash = sha256_hex(intermediate)

    expected_hash = content_hash_from_manifest_entries([("chunk-boundary.md", intermediate_hash)])
    got           = run_single_file_hash("chunk-boundary.md", raw_content)

    assert got == expected_hash, (
        f"TV-21 FAILED\n"
        f"  Expected: {expected_hash}\n"
        f"  Got:      {got}\n"
        f"  Raw content: 65535 'a' bytes + b'\\r\\nend\\n' ({len(raw_content)} bytes)\n"
        f"  Intermediate bytes: 65535 'a' bytes + b'\\nend\\n' ({len(intermediate)} bytes)\n"
        f"  Intermediate hex (last 10 bytes): ...{intermediate[-10:].hex()}\n"
        f"  Per-file hash of intermediate: {intermediate_hash}\n"
        f"  Note: pending_cr=True at end of chunk 1; next chunk starts with LF -> CRLF collapsed"
    )
    return True


# -- TV-22: Lone CR at EOF -----------------------------------------------------

def test_tv22():
    """
    TV-22: Lone CR at EOF is normalized to LF.

    A file ending with CR (not followed by LF) hits the pending_cr=True path
    at the end of moat_hash._hash_text(). The pending CR is flushed as a single LF.

    Intermediate normalized bytes: 'line1\\nline2\\n' (CR replaced by LF at EOF)
    """
    raw_content = b"line1\nline2\r"

    intermediate      = b"line1\nline2\n"
    intermediate_hash = sha256_hex(intermediate)

    expected_hash = content_hash_from_manifest_entries([("notes.md", intermediate_hash)])
    got           = run_single_file_hash("notes.md", raw_content)

    assert got == expected_hash, (
        f"TV-22 FAILED\n"
        f"  Expected: {expected_hash}\n"
        f"  Got:      {got}\n"
        f"  Raw content hex: {raw_content.hex()}\n"
        f"  Intermediate bytes (lone CR at EOF -> LF):\n"
        f"    hex: {intermediate.hex()}\n"
        f"    utf-8: {intermediate!r}\n"
        f"  Per-file hash of intermediate: {intermediate_hash}\n"
        f"  Note: pending_cr=True after last chunk; flushed as b'\\n' after loop"
    )
    return True


# -- Main ----------------------------------------------------------------------

def main():
    tests = [
        ("TV-17: CRLF normalization (.md)",               test_tv17),
        ("TV-18: UTF-8 BOM stripping (.py)",              test_tv18),
        ("TV-19: Extensionless dotfile treated as binary", test_tv19),
        ("TV-20: NUL byte forces binary (.json)",          test_tv20),
        ("TV-21: CR at chunk boundary",                    test_tv21),
        ("TV-22: Lone CR at EOF",                          test_tv22),
    ]

    print("MOAT Text Normalization Tests (TV-17 through TV-22)")
    print("=" * 60)
    print()

    passed = 0
    failed = 0
    for label, fn in tests:
        try:
            fn()
            print(f"  PASS  {label}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {label}")
            print(f"        {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {label}: {e}")
            failed += 1

    print()
    print("-" * 60)
    if failed == 0:
        print(f"All {passed} normalization tests passed. ✓")
    else:
        print(f"{passed} passed, {failed} FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
