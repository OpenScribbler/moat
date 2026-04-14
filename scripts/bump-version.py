#!/usr/bin/env python3
"""
Propagate the MOAT spec version from the VERSION file to all known locations.

Reads VERSION from the repo root, then updates every file that contains a
hardcoded core spec version string. Reports what changed and warns about
files it couldn't update.

Usage:
    python3 scripts/bump-version.py          # read from VERSION file
    python3 scripts/bump-version.py --dry-run # show what would change
    python3 scripts/bump-version.py --check   # exit non-zero if out of sync
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = REPO_ROOT / "VERSION"

# Each target is (relative_path, regex_pattern, replacement_template).
# The regex must have a named group `ver` matching the old version string.
# The replacement template uses {version} for the new version and {date} for today.
TARGETS = [
    # Core spec header
    (
        "moat-spec.md",
        r"(?P<pre>\*\*Version:\*\*\s+)(?P<ver>\d+\.\d+\.\d+)(?P<post>\s+\(Draft\))",
        r"\g<pre>{version}\g<post>",
    ),
    # Core spec date
    (
        "moat-spec.md",
        r"(?P<pre>\*\*Date:\*\*\s+)(?P<ver>\d{4}-\d{2}-\d{2})",
        r"\g<pre>{date}",
    ),
    # Website core spec page
    (
        "website/src/content/docs/spec/core.md",
        r"(?P<pre>\*\*Version:\*\*\s+)(?P<ver>\d+\.\d+\.\d+)(?P<post>\s+\(Draft\))",
        r"\g<pre>{version}\g<post>",
    ),
    # Website spec-status prose
    (
        "website/src/content/docs/overview/spec-status.md",
        r"(?P<pre>\*\*Core spec:\*\*\s+v)(?P<ver>\d+\.\d+\.\d+)(?P<post>\s+\(Draft\))",
        r"\g<pre>{version}\g<post>",
    ),
    # Website spec-status table
    (
        "website/src/content/docs/overview/spec-status.md",
        r"(?P<pre>\| \[Core spec\]\(/spec/core\) \| )(?P<ver>\d+\.\d+\.\d+)(?P<post> \| Draft \|)",
        r"\g<pre>{version}\g<post>",
    ),
    # README version table
    (
        "README.md",
        r"(?P<pre>\| \*\*Version\*\* \| )(?P<ver>\d+\.\d+\.\d+)(?P<post> \(Draft\) \|)",
        r"\g<pre>{version}\g<post>",
    ),
]


def read_version() -> str:
    if not VERSION_FILE.exists():
        print(f"error: {VERSION_FILE} not found", file=sys.stderr)
        sys.exit(1)
    return VERSION_FILE.read_text().strip()


def bump(dry_run: bool = False, check: bool = False) -> bool:
    version = read_version()
    today = date.today().isoformat()
    all_ok = True
    changes = []

    for rel_path, pattern, template in TARGETS:
        path = REPO_ROOT / rel_path
        if not path.exists():
            print(f"  SKIP  {rel_path} (file not found)")
            continue

        text = path.read_text()
        repl = template.replace("{version}", version).replace("{date}", today)
        new_text, count = re.subn(pattern, repl, text)

        if count == 0:
            # Check if already at target version
            if version in text:
                print(f"  OK    {rel_path} (already at {version})")
            else:
                print(f"  WARN  {rel_path} — pattern not matched", file=sys.stderr)
                all_ok = False
            continue

        # Find what old value was replaced
        match = re.search(pattern, text)
        old_ver = match.group("ver") if match else "?"
        # Determine the new value for display (version or date depending on target)
        new_val = today if "{date}" in template else version

        if check:
            if old_ver == new_val:
                print(f"  OK    {rel_path} (at {new_val})")
            else:
                print(f"  STALE {rel_path}: {old_ver} != {new_val}")
                all_ok = False
            continue

        changes.append((rel_path, old_ver))
        if not dry_run:
            path.write_text(new_text)
            print(f"  DONE  {rel_path}: {old_ver} -> {new_val}")
        else:
            print(f"  WOULD {rel_path}: {old_ver} -> {new_val}")

    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Propagate MOAT spec version from VERSION file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if any file is out of sync")
    args = parser.parse_args()

    version = read_version()
    print(f"MOAT version: {version}")
    print()

    ok = bump(dry_run=args.dry_run, check=args.check)

    if args.check and not ok:
        print(f"\nVersion mismatch detected. Run: python3 scripts/bump-version.py")
        sys.exit(1)
    elif not ok:
        print(f"\nSome patterns did not match — check warnings above.")
        sys.exit(1)
    else:
        print(f"\nAll targets updated." if not args.dry_run else "\nDry run complete.")


if __name__ == "__main__":
    main()
