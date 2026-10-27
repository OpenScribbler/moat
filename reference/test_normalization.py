#!/usr/bin/env python3
"""
MOAT — Text Normalization and Path Reject Integration Tests (TV-17 through TV-29)

Tests the full file I/O pipeline of moat_hash.py against real filesystem fixtures.
Unlike generate_test_vectors.py (which tests the manifest format using dict[str, bytes]),
this script tests BOM stripping, CRLF normalization, and binary classification
by writing real files to a temp directory and calling moat_hash.content_hash().
The path-reject tests (TV-23 through TV-29) write raw file names and check that
paths with invalid UTF-8 or a C0 control or DEL are refused, in that order of
precedence and before an NFC collision is reported.

Each test includes the intermediate normalized byte sequence so implementers can
pinpoint exactly where their normalization diverges from the spec.

Usage: python3 test_normalization.py
"""

import hashlib
import os
import pathlib
import sys
import tempfile
import textwrap
import unicodedata

sys.path.insert(0, os.path.dirname(__file__))
import generate_test_vectors as gtv
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


# -- Path rejects (TV-23 through TV-29) ----------------------------------------
#
# Paths are written from raw bytes. A platform that cannot create a name (C0
# controls on Windows, invalid UTF-8 on macOS) skips the test rather than
# failing it.

class Skip(Exception):
    pass


def build_tree(root: pathlib.Path, files: dict[bytes, bytes]) -> None:
    """Write raw-named files under root; skips when the platform cannot create them."""
    try:
        for rel, data in files.items():
            p = root / os.fsdecode(rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    except (OSError, UnicodeError) as err:
        raise Skip(f"this platform cannot create the input ({err.__class__.__name__})")
    # A normalization-insensitive filesystem (APFS) folds an NFD name onto its NFC twin.
    if sum(1 for q in root.rglob("*") if q.is_file()) != len(files):
        raise Skip("this filesystem folds distinct names together (normalization-insensitive)")


def run_tree(files: dict[bytes, bytes]) -> str:
    """Write raw-named files to a temp dir and return moat_hash.content_hash()."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir)
        build_tree(root, files)
        return moat_hash.content_hash(root)


def expect_reject(files: dict[bytes, bytes], reason: str) -> None:
    try:
        got = run_tree(files)
    except ValueError as err:
        assert reason in str(err), f"expected a refusal naming {reason!r}, got: {err}"
        return
    raise AssertionError(f"expected a refusal naming {reason!r}, got {got}")


NOT_UTF8 = "not valid UTF-8"
CONTROL = "control character"
SKILL = {b"SKILL.md": b"# Skill\n"}


def test_path_not_utf8():
    """A file name containing byte 0xFF is refused."""
    expect_reject({**SKILL, b"notes\xff.md": b"x\n"}, NOT_UTF8)


def test_path_lf():
    """A line feed in a file name is refused."""
    expect_reject({**SKILL, b"notes\n.md": b"x\n"}, CONTROL)


def test_path_cr_in_directory():
    """A carriage return in a directory name is refused."""
    expect_reject({**SKILL, b"lib\r/a.py": b"x\n"}, CONTROL)


def test_path_del():
    """U+007F in a file name is refused."""
    expect_reject({**SKILL, b"a\x7fb.md": b"x\n"}, CONTROL)


def test_path_c1_accepted():
    """U+0080 (a C1 control) is accepted and hashed under its UTF-8 path."""
    c1 = "a\u0080b.md"
    got = run_tree({**SKILL, c1.encode(): b"x\n"})
    expected = content_hash_from_manifest_entries([
        ("SKILL.md", sha256_hex(b"# Skill\n")),
        (c1, sha256_hex(b"x\n")),
    ])
    assert got == expected, f"C1 path\n  Expected: {expected}\n  Got:      {got}"


def test_path_control_before_collision():
    """With an NFC collision and a control character, the control character is reported."""
    expect_reject({"café.md".encode(): b"nfc\n", "café.md".encode(): b"nfd\n",
                   b"z\x01.md": b"x\n"}, CONTROL)


def test_path_not_utf8_before_control():
    """With invalid UTF-8 in one path and a control character in another, invalid UTF-8 is reported."""
    expect_reject({b"a\nb.md": b"x\n", b"c\xff.md": b"y\n"}, NOT_UTF8)
    expect_reject({b"a\xffb.md": b"x\n", b"c\n.md": b"y\n"}, NOT_UTF8)


def test_path_nfc_collision():
    """Two paths that are equal after NFC are refused by the directory algorithm (TV-04)."""
    expect_reject({"café.md".encode(): b"nfc\n", "café.md".encode(): b"nfd\n"}, "collision")


# -- Embedded workflow copies --------------------------------------------------
#
# The publisher and registry workflows each embed their own copy of the content
# hash. Pull `moat_content_hash` and the constants and helpers it uses out of
# each copy and check it agrees with moat_hash.content_hash(): the same hash, or
# the same kind of refusal, on the path-reject vectors and a plain directory.

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW_COPIES = [
    ".github/workflows/moat-publisher.yml",
    ".github/workflows/moat-registry.yml",
    "reference/moat-publisher.yml",
    "reference/moat-registry.yml",
]


def load_embedded_content_hash(rel: str):
    lines = textwrap.dedent("\n".join(
        (REPO_ROOT / rel).read_text(encoding="utf-8").split("python3 << 'PYEOF'\n", 1)[1]
        .split("\n          PYEOF", 1)[0].splitlines())).splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("# ─── Embedded MOAT content hash"))
    fn = next(i for i, ln in enumerate(lines) if ln.startswith("def moat_content_hash("))
    end = fn + 1
    while end < len(lines) and (not lines[end].strip() or lines[end][0].isspace()):
        end += 1
    ns = {"hashlib": hashlib, "os": os, "unicodedata": unicodedata, "Path": pathlib.Path}
    exec("\n".join(lines[start:end]), ns)
    return ns["moat_content_hash"]


def outcome(fn, root: pathlib.Path) -> str:
    try:
        return fn(root)
    except ValueError as err:
        return "refused: " + gtv._path_kind(err)


def test_embedded_workflow_hashes_agree():
    """Each workflow's embedded content hash matches moat_hash.py on TV-04, TV-23..TV-29 and a plain directory."""
    cases = [("plain directory", {b"SKILL.md": b"# Skill\n", b"lib/a.py": b"x = 1\r\n", b"img.png": b"\x89PNG\x00"}),
             ("TV-04", {"café.md".encode(): b"nfc\n", "café.md".encode(): b"nfd\n"})]
    for gen in gtv.PATH_REJECT_VECTORS:
        v = gen()
        cases.append((f"TV-{v['id']}", v["raw_files"]))
    for rel in WORKFLOW_COPIES:
        embedded = load_embedded_content_hash(rel)
        for label, files in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = pathlib.Path(tmpdir)
                try:
                    build_tree(root, files)
                except Skip:
                    continue  # this platform cannot create the vector, as in the other tests
                want, got = outcome(moat_hash.content_hash, root), outcome(embedded, root)
            assert got == want, f"{rel}, {label}: moat_hash.py gives {want}, the embedded copy gives {got}"


# -- Main ----------------------------------------------------------------------

def main():
    tests = [
        ("TV-17: CRLF normalization (.md)",               test_tv17),
        ("TV-18: UTF-8 BOM stripping (.py)",              test_tv18),
        ("TV-19: Extensionless dotfile treated as binary", test_tv19),
        ("TV-20: NUL byte forces binary (.json)",          test_tv20),
        ("TV-21: CR at chunk boundary",                    test_tv21),
        ("TV-22: Lone CR at EOF",                          test_tv22),
        ("TV-23: LF in a file name refused",               test_path_lf),
        ("TV-24: CR in a directory name refused",          test_path_cr_in_directory),
        ("TV-25: DEL in a file name refused",              test_path_del),
        ("TV-26: C1 control in a file name accepted",      test_path_c1_accepted),
        ("TV-27: Path that is not valid UTF-8 refused",    test_path_not_utf8),
        ("TV-28: Control character reported before collision", test_path_control_before_collision),
        ("TV-29: Invalid UTF-8 reported before control",   test_path_not_utf8_before_control),
        ("TV-04: NFC collision refused",                   test_path_nfc_collision),
        ("Embedded workflow hashes agree with moat_hash.py", test_embedded_workflow_hashes_agree),
    ]

    print("MOAT Text Normalization and Path Reject Tests (TV-17 through TV-29)")
    print("=" * 60)
    print()

    passed = 0
    failed = 0
    for label, fn in tests:
        try:
            fn()
            print(f"  PASS  {label}")
            passed += 1
        except Skip as e:
            print(f"  SKIP  {label}: {e}")
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
