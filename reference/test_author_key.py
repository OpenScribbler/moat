#!/usr/bin/env python3
"""
MOAT — Author-key profile interoperability tests

Checks the author-key vectors (TV-AK-*) against OpenSSH, so the profile is
proven implementable with stock tooling rather than only with
moat_author_key.py:

  1. Every vector signature that the reference accepts as cryptographically
     valid, `ssh-keygen -Y verify -n file` also accepts; a signature over the
     tampered message (TV-AK-03) is rejected by both. TV-AK-08 (no
     user-presence flag) is cryptographically valid, and OpenSSH's
     `-Y verify` accepts it, so a client cannot delegate the user-presence
     check to ssh-keygen; this test pins that fact.
  2. Every test key's fingerprint equals `ssh-keygen -l`'s SHA256 fingerprint.
  3. A signature made by `ssh-keygen -Y sign -n file` with a freshly generated
     ssh-ed25519 key verifies under moat_author_key.verify_item.

Requires ssh-keygen from OpenSSH 8.2 or later on PATH.

Usage: python3 test_author_key.py
"""

import base64
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import generate_test_vectors as gtv
import moat_author_key as ak


def ssh_verify(tmp: pathlib.Path, list_bytes: bytes, principal: str, sig: str, message: bytes) -> bool:
    (tmp / "allowed_signers").write_bytes(list_bytes)
    (tmp / "msg.sig").write_text(sig)
    r = subprocess.run(
        ["ssh-keygen", "-Y", "verify", "-f", str(tmp / "allowed_signers"),
         "-I", principal, "-n", "file", "-s", str(tmp / "msg.sig")],
        input=message, capture_output=True)
    return r.returncode == 0


def main() -> int:
    if shutil.which("ssh-keygen") is None:
        print("FAIL: ssh-keygen not found on PATH")
        return 1

    failures = []
    fx = gtv.author_key_fixtures()
    keys, lists = fx["keys"], fx["lists"]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = pathlib.Path(tmpdir)

        for label, blob in keys.items():
            (tmp / "k.pub").write_text(f"{ak.key_type(blob)} {base64.b64encode(blob).decode()}\n")
            out = subprocess.run(["ssh-keygen", "-l", "-f", str(tmp / "k.pub")],
                                 capture_output=True, text=True).stdout.split()
            ok = len(out) > 1 and out[1] == ak.fingerprint(blob)
            print(f"  fingerprint {label}: {'OK' if ok else 'MISMATCH'}")
            if not ok:
                failures.append(f"fingerprint {label}")

        for v in gtv.author_key_vectors():
            if v["expected"] == ak.LIST_MALFORMED:
                continue
            signer_fp = ak.fingerprint(keys[v["signer"]])
            sig_valid = v["expected"] in (ak.OK, ak.SIGNER_NOT_ALLOWED) or v["id"] == "TV-AK-08"
            # ssh-keygen checks the signature against a list naming the signer, so a
            # signer_not_allowed vector still proves the signature itself verifies.
            own_list = (ak.allowed_signers_line(keys[v["signer"]]) + "\n").encode()
            got = ssh_verify(tmp, own_list, signer_fp, v["signature"], v["message"])
            ok = got == sig_valid
            if v["expected"] == ak.SIGNER_NOT_ALLOWED:
                list_name = v.get("list") or v.get("previous_list")
                refused = not ssh_verify(tmp, lists[list_name], signer_fp, v["signature"], v["message"])
                ok = ok and refused
            print(f"  {v['id']} ({v['expected']}): {'OK' if ok else 'MISMATCH'}")
            if not ok:
                failures.append(v["id"])

        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "",
                        "-f", str(tmp / "real")], check=True)
        content_hash = gtv.acif_vectors()[3]["content_hash"]
        (tmp / "item").write_bytes(ak.item_message(content_hash))
        subprocess.run(["ssh-keygen", "-Y", "sign", "-q", "-f", str(tmp / "real"),
                        "-n", "file", str(tmp / "item")], check=True)
        blob = base64.b64decode((tmp / "real.pub").read_text().split()[1])
        real_list = (ak.allowed_signers_line(blob) + "\n").encode()
        got = ak.verify_item(content_hash, (tmp / "item.sig").read_text(), real_list)
        print(f"  ssh-keygen -Y sign -> verify_item: {got}")
        if got != ak.OK:
            failures.append("ssh-keygen signature")

    if failures:
        print(f"FAIL: {', '.join(failures)}")
        return 1
    print("All author-key interoperability checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
