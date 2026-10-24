#!/usr/bin/env python3
"""
MOAT — moat-verify unsupported-item checks

specs/moat-verify.md says this version of moat-verify does not verify ACIF
content items or Author-Key publisher attestations, and must fail them with
exit 1 before any Rekor request:

  1. Online Step 3 fails a matching manifest entry that carries `acif`, even
     when its content_hash is the directory algorithm's output.
  2. Offline Step 3 fails a matching lockfile entry that carries `acif`.
  3. Online Step 5 fails a moat-attestation.json item that carries
     `key_fingerprint`, even when its rekor_log_index names a valid keyless
     entry, and never reports DUAL-ATTESTED.

Network, cosign, and Rekor are stubbed; any Rekor request fails the test.

Usage: python3 test_verify_unsupported.py
"""

import contextlib
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import moat_verify as mv

HASH = "sha256:" + "ab" * 32
SOURCE = "https://github.com/alice/ai-skills"


class RekorCalled(AssertionError):
    pass


def _no_rekor(*_args, **_kwargs):
    raise RekorCalled("Rekor was queried")


@contextlib.contextmanager
def stubbed(**overrides):
    saved = {name: getattr(mv, name) for name in overrides}
    for name, value in overrides.items():
        setattr(mv, name, value)
    try:
        yield
    finally:
        for name, value in saved.items():
            setattr(mv, name, value)


def run_quiet(fn, *args) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


def manifest(entry_extra: dict) -> dict:
    entry = {"name": "my-skill", "type": "skill", "content_hash": HASH, "source_uri": SOURCE,
             "attested_at": "2026-10-24T00:00:00Z", "private_repo": False, "rekor_log_index": 1}
    entry.update(entry_extra)
    return {"schema_version": 1, "manifest_uri": "https://example.com/m.json", "content": [entry],
            "registry_signing_profile": {"issuer": "i", "subject": "s"}}


def test_online_acif_entry_fails_in_step3():
    with stubbed(_step1_compute_hash=lambda _d: HASH,
                 _online_step2=lambda _u: (b"", manifest({"acif": {"entry_file": "SKILL.md"}})),
                 _fetch_rekor_entry=_no_rekor, _verify_rekor_entry=_no_rekor,
                 _online_step4=_no_rekor):
        code, out = run_quiet(mv._run_online, "unused", "https://example.com/m.json", None, False)
    assert code == mv.EXIT_FAIL, f"expected exit 1, got {code}"
    assert "ACIF content items are not supported" in out, out


def test_offline_acif_entry_fails_in_step3():
    entry = {"name": "my-skill", "type": "skill", "registry": "https://example.com/m.json",
             "content_hash": HASH, "trust_tier": "SIGNED", "attested_at": "x", "pinned_at": "x",
             "attestation_bundle": {}, "signed_payload": "{}", "acif": {"entry_file": "SKILL.md"}}
    lock = {"moat_lockfile_version": 1, "registries": {}, "entries": [entry], "revoked_hashes": []}
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "moat-lockfile.json")
        with open(path, "w") as f:
            json.dump(lock, f)
        with stubbed(_step1_compute_hash=lambda _d: HASH, _offline_step4=_no_rekor,
                     _run_cosign=_no_rekor):
            code, out = run_quiet(mv._run_offline, "unused", path, False)
    assert code == mv.EXIT_FAIL, f"expected exit 1, got {code}"
    assert "ACIF content items are not supported" in out, out


def test_author_key_attestation_fails_in_step5():
    attestation = {"items": [{"name": "my-skill", "content_hash": HASH, "rekor_log_index": 7,
                              "key_fingerprint": "SHA256:c+9RtDpLaogkdIBaK4R83aEOVfIlPvftuiSpqVLOQA4"}]}
    keyless = ("https://github.com/alice/ai-skills/.github/workflows/moat-publisher.yml@refs/heads/main",
               "https://token.actions.githubusercontent.com")
    calls = []

    def verify_rekor(log_index, _content_hash):
        calls.append(log_index)
        return keyless

    with stubbed(_step1_compute_hash=lambda _d: HASH,
                 _online_step2=lambda _u: (b"", manifest({})),
                 _online_step4=lambda _i, _h, _p: ("registry", "issuer", 1),
                 _fetch_url=lambda _u, _l: json.dumps(attestation).encode(),
                 _verify_rekor_entry=verify_rekor, _fetch_rekor_entry=_no_rekor):
        code, out = run_quiet(mv._run_online, "unused", "https://example.com/m.json", SOURCE, False)
    assert code == mv.EXIT_FAIL, f"expected exit 1, got {code}"
    assert "DUAL-ATTESTED" not in out, out
    assert "Author-Key publisher attestations are not supported" in out, out
    assert not calls, f"publisher Rekor entry was queried: {calls}"


def main() -> int:
    tests = [
        ("online Step 3 fails an acif entry", test_online_acif_entry_fails_in_step3),
        ("offline Step 3 fails an acif entry", test_offline_acif_entry_fails_in_step3),
        ("Step 5 fails a key_fingerprint attestation before Rekor", test_author_key_attestation_fails_in_step5),
    ]
    failures = []
    for label, fn in tests:
        try:
            fn()
            print(f"  {label}: OK")
        except (AssertionError, mv._Exit) as e:
            print(f"  {label}: FAIL ({type(e).__name__}: {e})")
            failures.append(label)
    if failures:
        print(f"FAIL: {', '.join(failures)}")
        return 1
    print("All moat-verify unsupported-item checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
