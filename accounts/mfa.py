"""Minimal RFC 6238 TOTP (works with Google Authenticator, Authy, Microsoft Authenticator)."""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote


def new_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode()  # 32 chars


def _code(secret, counter):
    key = base64.b32decode(secret, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{number:06d}"


def verify(secret, code, window=1):
    code = (code or "").strip().replace(" ", "")
    if not secret or len(code) != 6 or not code.isdigit():
        return False
    now = int(time.time() // 30)
    return any(hmac.compare_digest(_code(secret, now + d), code) for d in range(-window, window + 1))


def provisioning_uri(secret, username, issuer="CampusHub"):
    return f"otpauth://totp/{quote(issuer)}:{quote(username)}?secret={secret}&issuer={quote(issuer)}"
