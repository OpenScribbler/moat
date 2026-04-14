#!/usr/bin/env python3
"""
MOAT v0.4.0 — Content Hash Reference Implementation (Informative)

This script is an informative reference implementation. The normative authority
for correct output is the test vector suite in generate_test_vectors.py and
test_normalization.py. When this script and a test vector disagree, the test
vector is correct and this script has a bug.

A conforming implementation produces identical output to all test vectors in
generate_test_vectors.py and test_normalization.py — not necessarily identical
output to this script if this script contains a bug.

Usage:
    python3 moat_hash.py <directory>
"""
import hashlib
import sys
import unicodedata
from pathlib import Path

# ── Extension list (normative, spec v0.4.0) ──────────────────────────────────
# Only file extensions (.suffix). Extensionless files — including dotfiles
# like .gitignore and .eslintrc — are treated as binary regardless of content.
TEXT_EXTENSIONS = frozenset({
    # Markup & prose
    ".md", ".txt", ".rst",
    # Data & config
    ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".conf",
    # Web
    ".html", ".htm", ".xml", ".svg", ".css", ".scss", ".less",
    # Code
    ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
    ".py", ".rb", ".lua", ".rs", ".go",
    ".sh", ".bash", ".zsh", ".fish",
    # Data
    ".csv", ".tsv", ".sql",
    # Lockfiles (go.sum, go.mod, Gemfile.lock, etc.)
    ".lock", ".sum", ".mod",
})

UTF8_BOM = b"\xef\xbb\xbf"
CHUNK    = 65536  # 64 KB read buffer
NUL_SCAN = 8192   # 8 KB NUL-byte scan window (matches git's binary heuristic)

# VCS metadata directories — excluded from hashing.
# Registries should use `git archive` or equivalent to produce clean content,
# but this guard prevents surprising hash differences when running locally
# against a working directory.
VCS_DIRS = frozenset({".git", ".svn", ".hg", ".bzr", "_darcs", ".fossil"})

# Files excluded from content hashing by name — root of the content directory only.
# moat-attestation.json is excluded to break the circular dependency: the
# attestation file contains content hashes, so including it would change
# the hash every time attestation is updated.
#
# Root-only is intentional. A file named moat-attestation.json in a subdirectory
# has no protocol meaning and MUST be included in the hash — excluding it at any
# depth would allow malicious content to hide there outside the attested hash.
EXCLUDED_FILES = frozenset({"moat-attestation.json"})


# ── Classification ────────────────────────────────────────────────────────────

def final_extension(name: str) -> str:
    """
    Lowercased final extension. Returns "" for extensionless files.

    .tar.gz   → .gz    (final extension only)
    .gitignore → ""    (dotfile, no other dot → extensionless)
    Makefile   → ""    (no dot at all → extensionless)
    """
    if name.startswith(".") and name.count(".") == 1:
        return ""
    return Path(name).suffix.lower()


def is_text(path: Path) -> bool:
    """
    A file is text if its final extension is in TEXT_EXTENSIONS AND
    its first 8 KB contain no NUL bytes.

    NUL bytes indicate binary content regardless of extension — a binary
    file named with a text extension would otherwise be silently corrupted
    by normalization. This mirrors git's binary detection heuristic.
    """
    if final_extension(path.name) not in TEXT_EXTENSIONS:
        return False
    with path.open("rb") as f:
        return b"\x00" not in f.read(NUL_SCAN)


# ── Hashing ───────────────────────────────────────────────────────────────────

def _hash_binary(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _hash_text(path: Path) -> str:
    """
    SHA-256 of the canonical text form: UTF-8 BOM stripped, line endings
    normalized to LF. Streaming — peak memory is O(chunk size), not O(file size).

    Normalization is a single left-to-right pass with greedy CRLF matching:
      CR LF → LF    (CRLF, including splits across chunk boundaries)
      CR    → LF    (lone CR)
      LF    → LF    (unchanged)
    """
    h = hashlib.sha256()
    first      = True
    pending_cr = False

    with path.open("rb") as f:
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break

            if first:
                if chunk.startswith(UTF8_BOM):
                    chunk = chunk[3:]
                first = False

            if not chunk:
                continue

            out = bytearray()
            i   = 0

            # Resolve CR that was deferred from the end of the previous chunk.
            if pending_cr:
                pending_cr = False
                if chunk[i] == 0x0A:   # previous CR + this LF = CRLF
                    out.append(0x0A)
                    i += 1
                else:                  # previous CR was a lone CR
                    out.append(0x0A)

            while i < len(chunk):
                b = chunk[i]
                if b == 0x0D:                          # CR
                    if i + 1 < len(chunk):
                        out.append(0x0A)               # emit LF for CR or CRLF
                        i += 2 if chunk[i + 1] == 0x0A else 1
                    else:
                        pending_cr = True              # CR at chunk boundary — peek next
                        i += 1
                else:
                    out.append(b)
                    i += 1

            h.update(bytes(out))

    if pending_cr:
        h.update(b"\n")                                # lone CR at EOF

    return h.hexdigest()


# ── Directory hash ────────────────────────────────────────────────────────────

def content_hash(directory: str | Path) -> str:
    """
    Compute the MOAT content hash for a directory.

    Raises ValueError if any symlinks are present (rejected at ingestion)
    or if the directory contains no files.
    """
    root    = Path(directory)
    entries: list[tuple[str, str]] = []

    for path in root.rglob("*"):
        if any(part in VCS_DIRS for part in path.parts):
            continue
        if path.parent == root and path.name in EXCLUDED_FILES:
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink rejected: {path.relative_to(root).as_posix()}")
        if not path.is_file():
            continue

        rel       = unicodedata.normalize("NFC", path.relative_to(root).as_posix())
        file_hash = _hash_text(path) if is_text(path) else _hash_binary(path)
        entries.append((rel, file_hash))

    if not entries:
        raise ValueError("No files found — content is unpublishable")

    # Sort by raw UTF-8 byte order (consistent across platforms and locales)
    entries.sort(key=lambda e: e[0].encode("utf-8"))

    # Manifest: sha256sum format — "hash  path\n" per entry
    manifest = "".join(f"{h}  {p}\n" for p, h in entries).encode("utf-8")
    return "sha256:" + hashlib.sha256(manifest).hexdigest()


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <directory>", file=sys.stderr)
        sys.exit(1)
    try:
        print(content_hash(sys.argv[1]))
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
