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
    python3 moat_hash.py --acif <entry-file> --publisher-section <file.json> <directory>
    python3 moat_hash.py --acif <entry-file> --no-publisher-section <directory>
"""
import hashlib
import json
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


# ── ACIF content items ────────────────────────────────────────────────────────
#
# For an ACIF content item the MOAT Content Hash is not the directory hash
# above. It is "sha256:" + the item's ACIF attestation input digest
# ([ACIF-REGISTRY] §6), computed over the installed bytes. It equals the
# attestation_hash an ACIF record publishes only when the item's bytes are
# already ACIF-canonical. That digest covers both ACIF hashes of the item:
#
#   body_hash      [ACIF-CORE] §7.2-§7.5 (frontmatter-bearing content types)
#   metadata_hash  [ACIF-PUBLISHER] §6 (absent when no publisher_section)
#
# This reference recomputes body_hash from the item's bytes. metadata_hash is
# computed from a publisher_section object the caller supplies: deriving that
# object from the item's declaration surface (frontmatter or authored sidecar)
# is ACIF's observation step ([ACIF-PUBLISHER] §5) and needs a YAML parser,
# which this stdlib-only script does not carry.

ACIF_SIDECAR_NAME = "acif-sidecar.yaml"
ACIF_ATTESTATION_INPUT_TAG = b"acif-attestation-input-v1"


def canonical_text(data: bytes) -> bytes:
    """BOM strip + single-pass CRLF/CR -> LF (the same rule _hash_text streams)."""
    if data.startswith(UTF8_BOM):
        data = data[3:]
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def strip_frontmatter(data: bytes) -> bytes:
    """
    [ACIF-CORE] §7.3 entry-file frontmatter strip, over the canonical text form.
    The block opens with a leading '---' line and closes at the next '---' line,
    terminated by LF or by end of input; both delimiter lines are removed.
    """
    text = canonical_text(data)
    if not text.startswith(b"---\n"):
        return text
    end = text.find(b"\n---\n", 3)
    if end != -1:
        return text[end + len(b"\n---\n"):]
    if text.endswith(b"\n---"):
        return b""
    return text


def _acif_root_excluded_from_classification(name: str) -> bool:
    upper = name.upper()
    return upper.startswith("LICENSE") or upper.startswith("README") \
        or name == ACIF_SIDECAR_NAME


def _acif_body(directory: str | Path, entry_file: str) -> tuple[list[tuple[str, Path]], str, bool]:
    """
    The files an ACIF body_hash covers, as (relative path, path) pairs, plus
    the NFC entry path and whether the body is multi-file. A single-file body
    covers the entry file alone.
    """
    if not isinstance(entry_file, str) or not entry_file or entry_file.startswith("/") \
            or Path(entry_file).is_absolute() or ".." in entry_file.replace("\\", "/").split("/"):
        raise ValueError(f"Malformed acif entry_file: {entry_file!r}")
    root = Path(directory)
    files: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        if any(part in VCS_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink rejected: {path.relative_to(root).as_posix()}")
        if not path.is_file():
            continue
        if path.parent == root and path.name == ACIF_SIDECAR_NAME:
            continue
        rel = unicodedata.normalize("NFC", path.relative_to(root).as_posix())
        files.append((rel, path))

    entry = unicodedata.normalize("NFC", entry_file)
    rels = [rel for rel, _ in files]
    if len(rels) != len(set(rels)):
        raise ValueError("NFC path collision — content is unpublishable")
    if entry not in rels:
        raise ValueError(f"Entry file not found: {entry_file}")

    multi_file = any(
        rel != entry and not ("/" not in rel and _acif_root_excluded_from_classification(rel))
        for rel in rels
    )
    if not multi_file:
        files = [(rel, path) for rel, path in files if rel == entry]
    return files, entry, multi_file


def acif_installed_files(directory: str | Path, entry_file: str) -> list[str]:
    """
    The relative paths a conforming client installs for an ACIF content item:
    exactly the files its body_hash covers (moat-spec.md §ACIF Content Items).
    A single-file body installs the entry file alone, so root LICENSE*/README*
    files are dropped; the root acif-sidecar.yaml and VCS metadata directories
    are never installed.
    """
    files, _, _ = _acif_body(directory, entry_file)
    return sorted(rel for rel, _ in files)


def acif_body_hash(directory: str | Path, entry_file: str) -> str:
    """
    ACIF body_hash for a frontmatter-bearing item, returned as "sha256:<hex>".

    entry_file is the canonical entry file's path relative to the item root
    (SKILL.md for a skill). Single-file bodies hash the entry file's
    frontmatter-stripped canonical text; multi-file bodies hash the §7.4
    manifest, with the entry file's per-file hash taken over that same
    stripped text. Root LICENSE*/README* files count only against the
    single/multi-file classification; they are hashed in a multi-file body.
    """
    files, entry, multi_file = _acif_body(directory, entry_file)
    if not multi_file:
        return "sha256:" + hashlib.sha256(strip_frontmatter(files[0][1].read_bytes())).hexdigest()

    entries = []
    for rel, path in files:
        if rel == entry:
            h = hashlib.sha256(strip_frontmatter(path.read_bytes())).hexdigest()
        else:
            h = _hash_text(path) if is_text(path) else _hash_binary(path)
        entries.append((rel, h))
    entries.sort(key=lambda e: e[0].encode("utf-8"))
    manifest = "".join(f"{h}  {p}\n" for p, h in entries).encode("utf-8")
    return "sha256:" + hashlib.sha256(manifest).hexdigest()


JCS_MAX_SAFE_INTEGER = 2**53 - 1


def jcs(value) -> bytes:
    """
    RFC 8785 canonical JSON for the value space ACIF records use: objects,
    arrays, strings, booleans, null and integers within ±(2**53 - 1).
    RFC 8785 serializes numbers as IEEE-754 doubles, and an integer beyond
    ±(2**53 - 1) cannot round-trip through a double, so two producers that
    parse it differently can disagree on its digits. Non-integer numbers and
    integers outside that range are refused with TypeError rather than
    serialized approximately.
    """
    def enc(v) -> str:
        if isinstance(v, dict):
            items = sorted(v.items(), key=lambda kv: kv[0].encode("utf-16-be"))
            return "{" + ",".join(f"{enc_str(k)}:{enc(x)}" for k, x in items) + "}"
        if isinstance(v, list):
            return "[" + ",".join(enc(x) for x in v) + "]"
        if isinstance(v, bool):
            return "true" if v else "false"
        if v is None:
            return "null"
        if isinstance(v, int) and abs(v) <= JCS_MAX_SAFE_INTEGER:
            return str(v)
        if isinstance(v, int):
            raise TypeError(f"integer {v} is outside ±(2**53 - 1) and cannot round-trip through "
                            "an IEEE-754 double")
        if isinstance(v, str):
            return enc_str(v)
        raise TypeError(f"unsupported JCS value: {type(v).__name__}")

    def enc_str(s: str) -> str:
        return json.dumps(s, ensure_ascii=False, separators=(",", ":"))

    return enc(value).encode("utf-8")


def acif_metadata_hash(publisher_section: dict | None) -> str | None:
    """[ACIF-PUBLISHER] §6: SHA-256 of JCS(publisher_section) || LF; None when absent."""
    if publisher_section is None:
        return None
    return "sha256:" + hashlib.sha256(jcs(publisher_section) + b"\n").hexdigest()


def acif_attestation_input_preimage(body_hash: str, metadata_hash: str | None) -> bytes:
    """
    [ACIF-REGISTRY] §6 attestation input preimage:
      "acif-attestation-input-v1" LF BH LF MH LF
    where BH and MH are "<algorithm>:<value>" and MH is the four bytes "null"
    when the record has no metadata_hash.
    """
    mh = metadata_hash if metadata_hash is not None else "null"
    return (ACIF_ATTESTATION_INPUT_TAG + b"\n" + body_hash.encode("utf-8") + b"\n"
            + mh.encode("utf-8") + b"\n")


def content_hash_from_acif(field: dict) -> str:
    """
    Map an ACIF {algorithm, value} hash field to a MOAT "<algorithm>:<hex>"
    Content Hash. Only sha256 with a 64-character lowercase hex value maps;
    anything else is refused.
    """
    algorithm, value = field.get("algorithm"), field.get("value")
    if algorithm != "sha256":
        raise ValueError(f"Unsupported ACIF hash algorithm: {algorithm!r}")
    if not isinstance(value, str) or len(value) != 64 \
            or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("ACIF hash value is not 64 lowercase hex characters")
    return f"sha256:{value}"


def acif_content_hash(directory: str | Path, entry_file: str,
                      publisher_section: dict | None) -> str:
    """
    MOAT Content Hash of an ACIF content item: "sha256:" + the ACIF attestation
    input digest over the installed bytes. Equals an ACIF record's
    attestation_hash only when those bytes are already ACIF-canonical.
    """
    body = acif_body_hash(directory, entry_file)
    meta = acif_metadata_hash(publisher_section)
    digest = hashlib.sha256(acif_attestation_input_preimage(body, meta)).hexdigest()
    return content_hash_from_acif({"algorithm": "sha256", "value": digest})


# ── CLI ───────────────────────────────────────────────────────────────────────

def _main(argv: list[str]) -> int:
    usage = (f"Usage: {argv[0]} <directory>\n"
             f"       {argv[0]} --acif <entry-file> --publisher-section <file.json> <directory>\n"
             f"       {argv[0]} --acif <entry-file> --no-publisher-section <directory>")
    args = argv[1:]
    try:
        if len(args) == 1 and not args[0].startswith("--"):
            print(content_hash(args[0]))
            return 0
        if len(args) == 5 and args[0] == "--acif" and args[2] == "--publisher-section":
            section = json.loads(Path(args[3]).read_text(encoding="utf-8"))
            print(acif_content_hash(args[4], args[1], section))
            return 0
        if len(args) == 4 and args[0] == "--acif" and args[2] == "--no-publisher-section":
            print(acif_content_hash(args[3], args[1], None))
            return 0
    except (ValueError, OSError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(usage, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
