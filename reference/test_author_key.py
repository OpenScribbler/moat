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
     check to ssh-keygen; this test pins that fact. OpenSSH likewise accepts
     TV-AK-13 (small-order key and R) and TV-AK-14 (armor over 16384 bytes),
     which the profile refuses, so neither check can be delegated either.
  2. Every test key's fingerprint equals `ssh-keygen -l`'s SHA256 fingerprint.
  3. A signature made by `ssh-keygen -Y sign -n file` with a freshly generated
     ssh-ed25519 key verifies under moat_author_key.verify_item.
  4. `ssh-keygen -Y verify` reads a list carrying the `# moat-sequence: <n>`
     line, so the sequence line does not break stock tooling.
  5. List changes signed by `ssh-keygen -Y sign`: a change verifies for the
     source_uri it was signed for and is `signature_invalid` for any other,
     and replaying an earlier change after a later one was recorded is
     `sequence_not_greater`.
  6. Signatures `ssh-keygen -Y sign` makes outside the profile are
     `signature_invalid`: one under a namespace other than `file`, one with
     `-O hashalg=sha256`, and one over the bare canonical payload without the
     `moat-author-item-v1` line.
  7. List parsing: fields separate on spaces or tabs only, and a sequence line
     with whitespace before `#` or after `<n>` makes the list malformed.
  8. Strict Ed25519 and the armor cap: a small-order A or a small-order R is
     refused, as is armor one byte over 16384 bytes; armor of exactly 16384
     bytes is still read.

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
import hashlib

import generate_test_vectors as gtv
import moat_author_key as ak

# Vectors whose signature OpenSSH's `-Y verify` accepts but the profile refuses.
OPENSSH_ACCEPTS = {"TV-AK-08", "TV-AK-13", "TV-AK-14"}


def strict_ed25519_checks() -> list[tuple[str, str, str]]:
    """(label, got, want) for small-order A, small-order R and the armor cap."""
    fx = gtv.author_key_fixtures()
    lists = fx["lists"]
    ch = gtv.acif_vectors()[3]["content_hash"]
    data = ak._signed_data(ak.item_message(ch))
    ident = gtv.ED25519_IDENTITY

    def sshsig(blob: bytes, sig: bytes) -> str:
        return ak._sshsig(blob, ak._string(ak.KT_ED25519) + ak._string(sig))

    # Small-order A, ordinary R: A = identity, R = [r]B, S = r.
    r = 0x1234567
    small_a = sshsig(fx["keys"]["Z"], ak._ed_compress(ak._ed_mul(r, ak._G)) + r.to_bytes(32, "little"))
    # Small-order R, real key A: R = identity, S = k*a, where k = H(R || A || M).
    a, _ = ak._ed_expand(gtv._seed("A"))
    pub = ak.ed25519_public(gtv._seed("A"))
    k = int.from_bytes(hashlib.sha512(ident + pub + data).digest(), "little") % ak._Q
    small_r = sshsig(ak.key_blob_ed25519(pub), ident + (k * a % ak._Q).to_bytes(32, "little"))

    sig_a = ak.sign_ed25519(gtv._seed("A"), ak.item_message(ch))
    at_cap = sig_a + "\n" * (ak.MAX_ARMOR_BYTES - len(sig_a.encode()))
    # S + L: the same signature with S replaced by S + L. [S + L]B = [S]B, so the
    # equation still holds and only the S < L check refuses it.
    seed_a = gtv._seed("A")
    raw = ak.ed25519_sign(seed_a, data)
    s_plus_l = (int.from_bytes(raw[32:], "little") + ak._Q).to_bytes(32, "little")
    blob_a = ak.key_blob_ed25519(pub)

    # Non-canonical A or R: y encoded as y + p, still below 2^255. y = 3 is on the
    # curve and not of small order, so `y >= p` is the only condition that refuses
    # it. A and R decode through the same function, so one decode check covers both,
    # and verification is also refused with the bad encoding in either position.
    y = 3
    canonical = y.to_bytes(32, "little")
    non_canonical = (y + ak._P).to_bytes(32, "little")
    refuse = lambda ok: "refused" if not ok else "accepted"
    return [
        ("canonical y = 3 decodes (control)", refuse(ak._ed_decompress(canonical) is not None), "accepted"),
        ("non-canonical A or R (y + p) does not decode", refuse(ak._ed_decompress(non_canonical) is not None), "refused"),
        ("non-canonical A (y + p) in verification", refuse(ak.ed25519_verify(non_canonical, data, raw)), "refused"),
        ("non-canonical R (y + p) in verification", refuse(ak.ed25519_verify(pub, data, non_canonical + raw[32:])), "refused"),
        ("S < L (control)", ak.verify_item(ch, sshsig(blob_a, raw), lists["L1"]), ak.OK),
        ("S + L", ak.verify_item(ch, sshsig(blob_a, raw[:32] + s_plus_l), lists["L1"]), ak.SIGNATURE_INVALID),
        ("small-order A, ordinary R", ak.verify_item(ch, small_a, lists["LZ"]), ak.SIGNATURE_INVALID),
        ("small-order R, real key", ak.verify_item(ch, small_r, lists["L1"]), ak.SIGNATURE_INVALID),
        ("armor of exactly 16384 bytes", ak.verify_item(ch, at_cap, lists["L1"]), ak.OK),
        ("armor of 16385 bytes", ak.verify_item(ch, at_cap + "\n", lists["L1"]), ak.SIGNATURE_INVALID),
        ("armor of 16385 bytes, padded with spaces before the END line",
         ak.verify_item(ch, sig_a.replace("-----END", " " * (ak.MAX_ARMOR_BYTES + 1 - len(sig_a.encode()))
                                          + "-----END"), lists["L1"]), ak.SIGNATURE_INVALID),
    ]


def ssh_verify(tmp: pathlib.Path, list_bytes: bytes, principal: str, sig: str, message: bytes) -> bool:
    (tmp / "allowed_signers").write_bytes(list_bytes)
    (tmp / "msg.sig").write_text(sig)
    r = subprocess.run(
        ["ssh-keygen", "-Y", "verify", "-f", str(tmp / "allowed_signers"),
         "-I", principal, "-n", "file", "-s", str(tmp / "msg.sig")],
        input=message, capture_output=True)
    return r.returncode == 0


def ssh_sign(tmp: pathlib.Path, key: str, message: bytes, namespace: str = "file",
             options: tuple[str, ...] = ()) -> str:
    (tmp / "msg").write_bytes(message)
    (tmp / "msg.sig").unlink(missing_ok=True)
    subprocess.run(["ssh-keygen", "-Y", "sign", "-q", "-f", str(tmp / key),
                    "-n", namespace, *options, str(tmp / "msg")], check=True)
    return (tmp / "msg.sig").read_text()


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
            sig_valid = v["expected"] in (ak.OK, ak.SIGNER_NOT_ALLOWED) or v["id"] in OPENSSH_ACCEPTS
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
        real_line = ak.allowed_signers_line(blob)
        real_list = f"# moat-sequence: 0\n{real_line}\n".encode()
        got = ak.verify_item(content_hash, (tmp / "item.sig").read_text(), real_list)
        print(f"  ssh-keygen -Y sign -> verify_item: {got}")
        if got != ak.OK:
            failures.append("ssh-keygen signature")

        accepted = ssh_verify(tmp, real_list, ak.fingerprint(blob),
                              (tmp / "item.sig").read_text(), ak.item_message(content_hash))
        print(f"  ssh-keygen -Y verify reads a list with a sequence line: {'OK' if accepted else 'MISMATCH'}")
        if not accepted:
            failures.append("sequence line breaks ssh-keygen")

        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "",
                        "-f", str(tmp / "real2")], check=True)
        line2 = ak.allowed_signers_line(base64.b64decode((tmp / "real2.pub").read_text().split()[1]))
        r1 = f"# moat-sequence: 1\n{real_line}\n{line2}\n".encode()
        r2 = f"# moat-sequence: 2\n{real_line}\n".encode()
        src, other = gtv.AK_SOURCE_URI, gtv.AK_OTHER_SOURCE_URI
        add = ssh_sign(tmp, "real", ak.list_change_message(src, real_list, r1))
        remove = ssh_sign(tmp, "real", ak.list_change_message(src, r1, r2))
        checks = [
            ("change verifies for its source_uri", ak.verify_list_change(src, real_list, r1, add), ak.OK),
            ("removal verifies", ak.verify_list_change(src, r1, r2, remove), ak.OK),
            ("change checked for another source_uri",
             ak.verify_list_change(other, real_list, r1, add), ak.SIGNATURE_INVALID),
            ("replay of the addition after the removal",
             ak.verify_list_change(src, r2, r1, add), ak.SEQUENCE_NOT_GREATER),
        ]
        item_sig = (tmp / "item.sig").read_text()
        item_msg = ak.item_message(content_hash)
        checks += [
            ("item signed under namespace git",
             ak.verify_item(content_hash, ssh_sign(tmp, "real", item_msg, "git"), real_list),
             ak.SIGNATURE_INVALID),
            ("item signed with hashalg=sha256",
             ak.verify_item(content_hash, ssh_sign(tmp, "real", item_msg, options=("-O", "hashalg=sha256")),
                            real_list),
             ak.SIGNATURE_INVALID),
            ("bare payload without the moat-author-item-v1 line",
             ak.verify_item(content_hash, ssh_sign(tmp, "real", ak.canonical_payload(content_hash)), real_list),
             ak.SIGNATURE_INVALID),
            ("tab-separated fields",
             ak.verify_item(content_hash, item_sig, real_list.replace(b" ", b"\t").replace(
                 b"#\tmoat-sequence:\t0", b"# moat-sequence: 0")), ak.OK),
            ("no-break space between fields",
             ak.verify_item(content_hash, item_sig, real_list.replace(
                 real_line.encode(), real_line.replace(" ", "\u00a0", 1).encode())), ak.LIST_MALFORMED),
            ("leading space before the sequence line",
             ak.verify_item(content_hash, item_sig, b" " + real_list), ak.LIST_MALFORMED),
            ("leading tab before the sequence line",
             ak.verify_item(content_hash, item_sig, b"\t" + real_list), ak.LIST_MALFORMED),
            ("trailing space after the sequence number",
             ak.verify_item(content_hash, item_sig, real_list.replace(b": 0\n", b": 0 \n")), ak.LIST_MALFORMED),
        ]
        for label, got, want in checks:
            print(f"  ssh-keygen, {label}: {got}")
            if got != want:
                failures.append(f"{label}: expected {want}, got {got}")

        for label, got, want in strict_ed25519_checks():
            print(f"  strict Ed25519 / armor cap, {label}: {got}")
            if got != want:
                failures.append(f"{label}: expected {want}, got {got}")

    if failures:
        print(f"FAIL: {', '.join(failures)}")
        return 1
    print("All author-key interoperability checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
