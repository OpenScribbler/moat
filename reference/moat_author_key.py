#!/usr/bin/env python3
"""
MOAT author-key profile — reference implementation (Informative)

Signs and verifies the two messages the author-key publisher signing profile
defines (moat-spec.md §Author-Key Profile), using OpenSSH SSHSIG signatures
(PROTOCOL.sshsig) so a Publisher signs with stock `ssh-keygen -Y sign` on
Linux, macOS and Windows:

  item message          b"moat-author-item-v1\\n" || canonical attestation payload
  list-change message   b"moat-allowed-signers-change-v1\\n"
                        || "<source_uri>\\n" || "<new list sequence>\\n"
                        || "<previous list digest>\\n" || "<new list digest>\\n"

Every allowed-signers list carries exactly one sequence line,
"# moat-sequence: <n>", which OpenSSH reads as a comment. A list change is
accepted only when the new list's sequence is greater than the recorded
list's, so a change signed before a key was removed cannot be replayed.

Every signature uses SSHSIG namespace "file" and hash algorithm "sha512", the
values Rekor's `rekord` entry type verifies SSH signatures with; the message
prefixes above carry MOAT's domain separation instead of the namespace.

Accepted key types:
  ssh-ed25519
  sk-ssh-ed25519@openssh.com             (FIDO2 security key, Ed25519)
  sk-ecdsa-sha2-nistp256@openssh.com     (FIDO2 security key, ECDSA P-256)

The Ed25519 and P-256 arithmetic below is a dependency-free transcription of
RFC 8032 §6 and SEC 1, written for clarity and test-vector generation. It is
not constant-time and MUST NOT sign with real keys.

The test-vector suite in generate_test_vectors.py is the normative authority;
where this script and a vector disagree, the vector is correct.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re

ITEM_PREFIX = b"moat-author-item-v1\n"
LIST_CHANGE_PREFIX = b"moat-allowed-signers-change-v1\n"
SSHSIG_NAMESPACE = "file"
SSHSIG_HASH = "sha512"
SSHSIG_MAGIC = b"SSHSIG"

KT_ED25519 = "ssh-ed25519"
KT_SK_ED25519 = "sk-ssh-ed25519@openssh.com"
KT_SK_ECDSA = "sk-ecdsa-sha2-nistp256@openssh.com"
ALLOWED_KEY_TYPES = (KT_ED25519, KT_SK_ED25519, KT_SK_ECDSA)
SECURITY_KEY_TYPES = (KT_SK_ED25519, KT_SK_ECDSA)
SK_FLAG_USER_PRESENT = 0x01
SEQUENCE_LINE = re.compile(r"# moat-sequence: (0|[1-9][0-9]*)")
SEQUENCE_LINE_START = re.compile(r"#\s*moat-sequence")
MAX_SEQUENCE = 2**53 - 1

# Verification outcomes (moat-spec.md §Author-Key Profile).
OK = "ok"
SIGNATURE_INVALID = "signature_invalid"
SIGNER_NOT_ALLOWED = "signer_not_allowed"
LIST_MALFORMED = "allowed_signers_malformed"
SEQUENCE_NOT_GREATER = "sequence_not_greater"


# ── SSH wire encoding ─────────────────────────────────────────────────────────

def _string(b: bytes | str) -> bytes:
    if isinstance(b, str):
        b = b.encode("utf-8")
    return len(b).to_bytes(4, "big") + b


def _mpint(n: int) -> bytes:
    if n == 0:
        return _string(b"")
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    if raw[0] & 0x80:
        raw = b"\x00" + raw
    return _string(raw)


class _Reader:
    def __init__(self, data: bytes):
        self.data, self.pos = data, 0

    def take(self, n: int) -> bytes:
        if self.pos + n > len(self.data):
            raise ValueError("truncated SSH wire data")
        out = self.data[self.pos:self.pos + n]
        self.pos += n
        return out

    def u32(self) -> int:
        return int.from_bytes(self.take(4), "big")

    def string(self) -> bytes:
        return self.take(self.u32())

    def mpint(self) -> int:
        return int.from_bytes(self.string(), "big")

    def done(self) -> bool:
        return self.pos == len(self.data)


# ── Ed25519 (RFC 8032 §6) ─────────────────────────────────────────────────────

_P = 2**255 - 19
_Q = 2**252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_SQRT_M1 = pow(2, (_P - 1) // 4, _P)


def _ed_add(a, b):
    A = (a[1] - a[0]) * (b[1] - b[0]) % _P
    B = (a[1] + a[0]) * (b[1] + b[0]) % _P
    C = 2 * a[3] * b[3] * _D % _P
    D = 2 * a[2] * b[2] % _P
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F, G * H, F * G, E * H)


def _ed_mul(s: int, pt):
    acc = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            acc = _ed_add(acc, pt)
        pt = _ed_add(pt, pt)
        s >>= 1
    return acc


def _ed_equal(a, b) -> bool:
    return (a[0] * b[2] - b[0] * a[2]) % _P == 0 and (a[1] * b[2] - b[1] * a[2]) % _P == 0


def _ed_recover_x(y: int, sign: int):
    if y >= _P:
        return None
    x2 = (y * y - 1) * pow(_D * y * y + 1, _P - 2, _P)
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = x * _SQRT_M1 % _P
    if (x * x - x2) % _P != 0:
        return None
    if (x & 1) != sign:
        x = _P - x
    return x


_GY = 4 * pow(5, _P - 2, _P) % _P
_GX = _ed_recover_x(_GY, 0)
_G = (_GX, _GY, 1, _GX * _GY % _P)


def _ed_compress(pt) -> bytes:
    zinv = pow(pt[2], _P - 2, _P)
    x, y = pt[0] * zinv % _P, pt[1] * zinv % _P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _ed_decompress(s: bytes):
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _ed_recover_x(y, sign)
    return None if x is None else (x, y, 1, x * y % _P)


def _ed_expand(seed: bytes):
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def ed25519_public(seed: bytes) -> bytes:
    return _ed_compress(_ed_mul(_ed_expand(seed)[0], _G))


def ed25519_sign(seed: bytes, msg: bytes) -> bytes:
    a, prefix = _ed_expand(seed)
    pub = _ed_compress(_ed_mul(a, _G))
    r = int.from_bytes(hashlib.sha512(prefix + msg).digest(), "little") % _Q
    rs = _ed_compress(_ed_mul(r, _G))
    h = int.from_bytes(hashlib.sha512(rs + pub + msg).digest(), "little") % _Q
    return rs + ((r + h * a) % _Q).to_bytes(32, "little")


def ed25519_verify(pub: bytes, msg: bytes, sig: bytes) -> bool:
    if len(sig) != 64:
        return False
    A, R = _ed_decompress(pub), _ed_decompress(sig[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= _Q:
        return False
    h = int.from_bytes(hashlib.sha512(sig[:32] + pub + msg).digest(), "little") % _Q
    return _ed_equal(_ed_mul(s, _G), _ed_add(R, _ed_mul(h, A)))


# ── ECDSA P-256 (SEC 1 §4.1) ──────────────────────────────────────────────────

_EP = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
_EA = _EP - 3
_EB = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
_EN = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
_EG = (0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
       0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)


def _ec_add(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if a[0] == b[0] and (a[1] + b[1]) % _EP == 0:
        return None
    if a == b:
        lam = (3 * a[0] * a[0] + _EA) * pow(2 * a[1], _EP - 2, _EP) % _EP
    else:
        lam = (b[1] - a[1]) * pow(b[0] - a[0], _EP - 2, _EP) % _EP
    x = (lam * lam - a[0] - b[0]) % _EP
    return (x, (lam * (a[0] - x) - a[1]) % _EP)


def _ec_mul(k: int, pt):
    acc = None
    while k > 0:
        if k & 1:
            acc = _ec_add(acc, pt)
        pt = _ec_add(pt, pt)
        k >>= 1
    return acc


def _ec_on_curve(pt) -> bool:
    x, y = pt
    return 0 <= x < _EP and 0 <= y < _EP and (y * y - (x * x * x + _EA * x + _EB)) % _EP == 0


def p256_public(d: int) -> bytes:
    x, y = _ec_mul(d, _EG)
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")


def p256_sign_test_only(d: int, digest: bytes) -> tuple[int, int]:
    """ECDSA with a nonce derived from the key and digest. Test vectors only."""
    e = int.from_bytes(digest, "big") % _EN
    k = int.from_bytes(hashlib.sha256(b"moat-test-nonce" + d.to_bytes(32, "big") + digest).digest(), "big") % _EN
    r = _ec_mul(k, _EG)[0] % _EN
    s = pow(k, _EN - 2, _EN) * (e + r * d) % _EN
    return r, s


def p256_verify(q: bytes, digest: bytes, r: int, s: int) -> bool:
    if len(q) != 65 or q[0] != 4 or not (0 < r < _EN and 0 < s < _EN):
        return False
    pt = (int.from_bytes(q[1:33], "big"), int.from_bytes(q[33:], "big"))
    if not _ec_on_curve(pt):
        return False
    e = int.from_bytes(digest, "big") % _EN
    w = pow(s, _EN - 2, _EN)
    x = _ec_add(_ec_mul(e * w % _EN, _EG), _ec_mul(r * w % _EN, pt))
    return x is not None and x[0] % _EN == r


# ── Public keys and fingerprints ──────────────────────────────────────────────

def key_blob_ed25519(pub: bytes) -> bytes:
    return _string(KT_ED25519) + _string(pub)


def key_blob_sk_ed25519(pub: bytes, application: str = "ssh:") -> bytes:
    return _string(KT_SK_ED25519) + _string(pub) + _string(application)


def key_blob_sk_ecdsa(q: bytes, application: str = "ssh:") -> bytes:
    return _string(KT_SK_ECDSA) + _string("nistp256") + _string(q) + _string(application)


def key_type(blob: bytes) -> str:
    return _Reader(blob).string().decode("utf-8")


def fingerprint(blob: bytes) -> str:
    """OpenSSH SHA256 fingerprint: "SHA256:" + unpadded base64 of SHA-256(key blob)."""
    return "SHA256:" + base64.b64encode(hashlib.sha256(blob).digest()).decode("ascii").rstrip("=")


def allowed_signers_line(blob: bytes) -> str:
    """One allowed-signers line: the principal is the key's fingerprint; no comment."""
    return f"{fingerprint(blob)} {key_type(blob)} {base64.b64encode(blob).decode('ascii')}"


# ── Allowed-signers list ──────────────────────────────────────────────────────

def _canonical_text(data: bytes) -> bytes:
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def list_digest(list_bytes: bytes) -> str:
    """Digest of an allowed-signers list over its canonical text form."""
    return "sha256:" + hashlib.sha256(_canonical_text(list_bytes)).hexdigest()


def _parse(list_bytes: bytes) -> tuple[dict[str, bytes], int]:
    keys: dict[str, bytes] = {}
    sequences: list[int] = []
    for raw in _canonical_text(list_bytes).decode("utf-8").split("\n"):
        line = raw.strip(" \t")
        if SEQUENCE_LINE_START.match(line):
            m = SEQUENCE_LINE.fullmatch(raw)
            if not m or int(m.group(1)) > MAX_SEQUENCE:
                raise ValueError(f"malformed sequence line: {raw!r}")
            sequences.append(int(m.group(1)))
            continue
        if not line or line.startswith("#"):
            continue
        fields = re.split(r"[ \t]+", line)
        if len(fields) != 3:
            raise ValueError(f"malformed allowed-signers line: {line!r}")
        principal, ktype, b64 = fields
        blob = base64.b64decode(b64, validate=True)
        if ktype not in ALLOWED_KEY_TYPES or key_type(blob) != ktype:
            raise ValueError(f"unaccepted or inconsistent key type: {ktype}")
        if principal != fingerprint(blob):
            raise ValueError(f"principal is not the key fingerprint: {principal}")
        keys[principal] = blob
    if not keys:
        raise ValueError("allowed-signers list has no keys")
    if len(sequences) != 1:
        raise ValueError(f"allowed-signers list has {len(sequences)} sequence lines, not 1")
    return keys, sequences[0]


def parse_allowed_signers(list_bytes: bytes) -> dict[str, bytes]:
    """
    Parse an allowed-signers list into {fingerprint: key blob}.

    Each non-blank line is a comment beginning with '#', the one sequence
    line "# moat-sequence: <n>" (n a decimal integer without leading zeros,
    at most 2**53 - 1) with nothing before the '#' or after <n>, or exactly
    three fields separated by spaces or tabs:
    <fingerprint> <key-type> <base64 key blob>. The fingerprint MUST equal the
    blob's fingerprint, the key type MUST equal the blob's own type and be an
    accepted type. A comment that starts like a sequence line but is not one,
    a missing or repeated sequence line, or any other line makes the whole
    list malformed.
    """
    return _parse(list_bytes)[0]


def list_sequence(list_bytes: bytes) -> int:
    """The sequence number a well-formed allowed-signers list carries."""
    return _parse(list_bytes)[1]


# ── Messages ──────────────────────────────────────────────────────────────────

def canonical_payload(content_hash: str) -> bytes:
    return json.dumps({"_version": 1, "content_hash": content_hash},
                      separators=(",", ":"), sort_keys=True).encode("utf-8")


def item_message(content_hash: str) -> bytes:
    return ITEM_PREFIX + canonical_payload(content_hash)


def list_change_message(source_uri: str, previous_list: bytes, new_list: bytes) -> bytes:
    """
    Binds the source the list belongs to, the new list's sequence, and both
    list digests, so a change signature neither replays on another source nor
    replays after a later change on the same source.
    """
    if not source_uri or "\n" in source_uri or "\r" in source_uri:
        raise ValueError("source_uri must be non-empty and contain no line break")
    return (LIST_CHANGE_PREFIX + source_uri.encode("utf-8") + b"\n"
            + str(list_sequence(new_list)).encode("ascii") + b"\n"
            + list_digest(previous_list).encode("ascii") + b"\n"
            + list_digest(new_list).encode("ascii") + b"\n")


# ── SSHSIG ────────────────────────────────────────────────────────────────────

def _signed_data(message: bytes) -> bytes:
    return (SSHSIG_MAGIC + _string(SSHSIG_NAMESPACE) + _string(b"")
            + _string(SSHSIG_HASH) + _string(hashlib.sha512(message).digest()))


def _armor(blob: bytes) -> str:
    b64 = base64.b64encode(blob).decode("ascii")
    lines = [b64[i:i + 70] for i in range(0, len(b64), 70)]
    return "-----BEGIN SSH SIGNATURE-----\n" + "\n".join(lines) + "\n-----END SSH SIGNATURE-----\n"


def _unarmor(text: str) -> bytes:
    lines = [ln.strip() for ln in text.strip().splitlines()]
    if not lines or lines[0] != "-----BEGIN SSH SIGNATURE-----" \
            or lines[-1] != "-----END SSH SIGNATURE-----":
        raise ValueError("not an armored SSH signature")
    return base64.b64decode("".join(lines[1:-1]), validate=True)


def _sshsig(key_blob: bytes, sig_field: bytes) -> str:
    return _armor(SSHSIG_MAGIC + (1).to_bytes(4, "big") + _string(key_blob)
                  + _string(SSHSIG_NAMESPACE) + _string(b"") + _string(SSHSIG_HASH)
                  + _string(sig_field))


def _sk_signed(application: str, flags: int, counter: int, data: bytes) -> bytes:
    return (hashlib.sha256(application.encode("utf-8")).digest() + bytes([flags])
            + counter.to_bytes(4, "big") + hashlib.sha256(data).digest())


def sign_ed25519(seed: bytes, message: bytes) -> str:
    """What `ssh-keygen -Y sign -n file` produces for an ssh-ed25519 key."""
    sig = ed25519_sign(seed, _signed_data(message))
    return _sshsig(key_blob_ed25519(ed25519_public(seed)), _string(KT_ED25519) + _string(sig))


def sign_sk_ed25519_emulated(seed: bytes, message: bytes, flags: int = SK_FLAG_USER_PRESENT,
                             counter: int = 1, application: str = "ssh:") -> str:
    """Software emulation of a FIDO authenticator's sk-ssh-ed25519 signature. Test only."""
    signed = _sk_signed(application, flags, counter, _signed_data(message))
    sig = ed25519_sign(seed, signed)
    blob = key_blob_sk_ed25519(ed25519_public(seed), application)
    field = _string(KT_SK_ED25519) + _string(sig) + bytes([flags]) + counter.to_bytes(4, "big")
    return _sshsig(blob, field)


def sign_sk_ecdsa_emulated(d: int, message: bytes, flags: int = SK_FLAG_USER_PRESENT,
                           counter: int = 1, application: str = "ssh:") -> str:
    """Software emulation of a FIDO authenticator's sk-ecdsa-sha2-nistp256 signature. Test only."""
    digest = hashlib.sha256(_sk_signed(application, flags, counter, _signed_data(message))).digest()
    r, s = p256_sign_test_only(d, digest)
    blob = key_blob_sk_ecdsa(p256_public(d), application)
    field = (_string(KT_SK_ECDSA) + _string(_mpint(r) + _mpint(s))
             + bytes([flags]) + counter.to_bytes(4, "big"))
    return _sshsig(blob, field)


def verify_sshsig(armored: str, message: bytes) -> bytes | None:
    """
    Verify an SSHSIG over message under namespace "file" and hash "sha512".
    Returns the signer's public key blob, or None when the signature is invalid.
    Security-key signatures MUST carry the user-presence flag.
    """
    try:
        rd = _Reader(_unarmor(armored))
        if rd.take(6) != SSHSIG_MAGIC or rd.u32() != 1:
            return None
        key_blob = rd.string()
        namespace, _reserved, hash_alg = rd.string(), rd.string(), rd.string()
        sig_field = rd.string()
        if not rd.done() or namespace != SSHSIG_NAMESPACE.encode() or hash_alg != SSHSIG_HASH.encode():
            return None
        data = _signed_data(message)

        kr, sr = _Reader(key_blob), _Reader(sig_field)
        ktype, stype = kr.string().decode("utf-8"), sr.string().decode("utf-8")
        if ktype != stype or ktype not in ALLOWED_KEY_TYPES:
            return None
        if ktype == KT_ED25519:
            pub, sig = kr.string(), sr.string()
            ok = kr.done() and sr.done() and ed25519_verify(pub, data, sig)
            return key_blob if ok else None

        if ktype == KT_SK_ED25519:
            pub = kr.string()
            raw_sig = sr.string()
        else:
            if kr.string() != b"nistp256":
                return None
            pub = kr.string()
            inner = _Reader(sr.string())
            r, s = inner.mpint(), inner.mpint()
            if not inner.done():
                return None
        application = kr.string().decode("utf-8")
        flags, counter = sr.take(1)[0], int.from_bytes(sr.take(4), "big")
        if not (kr.done() and sr.done()) or not flags & SK_FLAG_USER_PRESENT:
            return None
        signed = _sk_signed(application, flags, counter, data)
        if ktype == KT_SK_ED25519:
            ok = ed25519_verify(pub, signed, raw_sig)
        else:
            ok = p256_verify(pub, hashlib.sha256(signed).digest(), r, s)
        return key_blob if ok else None
    except (ValueError, UnicodeDecodeError):
        return None


# ── Profile checks ────────────────────────────────────────────────────────────

def verify_item(content_hash: str, armored: str, allowed_list: bytes) -> str:
    """
    content_hash is the Content Hash the verifier recomputed over the bytes it
    installs, never a value copied from a record. The item is accepted only
    when the signature verifies over the item message for that hash AND the
    signer's fingerprint is in the recorded allowed-signers list.
    """
    try:
        allowed = parse_allowed_signers(allowed_list)
    except ValueError:
        return LIST_MALFORMED
    blob = verify_sshsig(armored, item_message(content_hash))
    if blob is None:
        return SIGNATURE_INVALID
    return OK if fingerprint(blob) in allowed else SIGNER_NOT_ALLOWED


def verify_list_change(source_uri: str, recorded_list: bytes, new_list: bytes, armored: str) -> str:
    """
    A new allowed-signers list replaces the one recorded for source_uri only
    when its sequence is greater than the recorded list's AND the change
    message for source_uri, binding both digests, is signed by a key the
    RECORDED list allows. A change signed for another source_uri does not
    verify here.
    """
    try:
        allowed, recorded_sequence = _parse(recorded_list)
        _, new_sequence = _parse(new_list)
    except ValueError:
        return LIST_MALFORMED
    if new_sequence <= recorded_sequence:
        return SEQUENCE_NOT_GREATER
    blob = verify_sshsig(armored, list_change_message(source_uri, recorded_list, new_list))
    if blob is None:
        return SIGNATURE_INVALID
    return OK if fingerprint(blob) in allowed else SIGNER_NOT_ALLOWED
