"""AES-128-CBC + HMAC-SHA256 encryption with PBKDF2 key derivation."""
import os
import hmac
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

PBKDF2_ITERATIONS = 200_000
SALT_LEN = 16
IV_LEN = 16
HMAC_LEN = 32
AES_KEY_LEN = 16
HMAC_KEY_LEN = 32


def _derive_keys(password: str, salt: bytes):
    full = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt,
        PBKDF2_ITERATIONS, dklen=AES_KEY_LEN + HMAC_KEY_LEN,
    )
    return full[:AES_KEY_LEN], full[AES_KEY_LEN:]


def encrypt(plaintext: str, password: str) -> bytes:
    """Returns: salt(16) || iv(16) || ciphertext || hmac(32)"""
    salt = os.urandom(SALT_LEN)
    iv = os.urandom(IV_LEN)
    aes_key, hmac_key = _derive_keys(password, salt)
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(plaintext.encode("utf-8"), AES.block_size))
    body = salt + iv + ct
    tag = hmac.new(hmac_key, body, hashlib.sha256).digest()
    return body + tag


def decrypt(blob: bytes, password: str) -> str:
    if len(blob) < SALT_LEN + IV_LEN + HMAC_LEN + AES.block_size:
        raise ValueError("ciphertext too short")
    salt = blob[:SALT_LEN]
    iv = blob[SALT_LEN:SALT_LEN + IV_LEN]
    tag = blob[-HMAC_LEN:]
    ct = blob[SALT_LEN + IV_LEN:-HMAC_LEN]
    aes_key, hmac_key = _derive_keys(password, salt)
    expected = hmac.new(hmac_key, blob[:-HMAC_LEN], hashlib.sha256).digest()
    if not hmac.compare_digest(expected, tag):
        raise ValueError("authentication failed (wrong key or tampered data)")
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size).decode("utf-8")
