from __future__ import annotations

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import secrets


_MAGIC = b"QYRSEC"
_VERSION = 1
_KDF_ID = 1
_CIPHER_ID = 1
_KEY_LEN = 32
_DEFAULT_SALT_LEN = 16
_DEFAULT_NONCE_LEN = 12
_INFO = b"qyro-secrets-v1"


class SecretsCryptoError(ValueError):
    pass


def derive_aes256_key(runtime_secret: bytes, salt: bytes) -> bytes:
    if not runtime_secret:
        raise SecretsCryptoError("Runtime secret is required")
    if not salt:
        raise SecretsCryptoError("Salt is required")

    key = HKDF(
        algorithm=hashes.SHA256(),
        length=_KEY_LEN,
        salt=salt,
        info=_INFO,
    ).derive(runtime_secret)

    if len(key) != _KEY_LEN:
        raise SecretsCryptoError("Invalid derived key length")
    return key


def encrypt_secrets_payload(
    plaintext: bytes,
    runtime_secret: bytes,
    *,
    salt: bytes | None = None,
    nonce: bytes | None = None,
) -> bytes:
    if plaintext is None:
        raise SecretsCryptoError("Plaintext is required")

    salt_value = salt or secrets.token_bytes(_DEFAULT_SALT_LEN)
    nonce_value = nonce or secrets.token_bytes(_DEFAULT_NONCE_LEN)

    if len(salt_value) == 0:
        raise SecretsCryptoError("Salt must not be empty")
    if len(nonce_value) != _DEFAULT_NONCE_LEN:
        raise SecretsCryptoError("Nonce must be 12 bytes for AES-GCM")

    header = _build_header(salt_value, nonce_value)
    key = derive_aes256_key(runtime_secret, salt_value)
    ciphertext = AESGCM(key).encrypt(nonce_value, plaintext, header)
    return header + ciphertext


def decrypt_secrets_payload(payload: bytes, runtime_secret: bytes) -> bytes:
    salt, nonce, ciphertext, header = _parse_payload(payload)
    key = derive_aes256_key(runtime_secret, salt)

    try:
        return AESGCM(key).decrypt(nonce, ciphertext, header)
    except InvalidTag as exc:
        raise SecretsCryptoError("Secrets authentication failed") from exc


def _build_header(salt: bytes, nonce: bytes) -> bytes:
    return _MAGIC + bytes([
        _VERSION,
        _KDF_ID,
        _CIPHER_ID,
        len(salt),
        len(nonce),
    ]) + salt + nonce


def _parse_payload(payload: bytes) -> tuple[bytes, bytes, bytes, bytes]:
    min_len = len(_MAGIC) + 5 + 1
    if len(payload) < min_len:
        raise SecretsCryptoError("Encrypted secrets payload is too short")

    cursor = 0
    magic = payload[cursor:cursor + len(_MAGIC)]
    cursor += len(_MAGIC)

    if magic != _MAGIC:
        raise SecretsCryptoError("Invalid encrypted secrets magic")

    version = payload[cursor]
    cursor += 1
    kdf_id = payload[cursor]
    cursor += 1
    cipher_id = payload[cursor]
    cursor += 1

    if version != _VERSION:
        raise SecretsCryptoError(f"Unsupported encrypted secrets version: {version}")
    if kdf_id != _KDF_ID:
        raise SecretsCryptoError(f"Unsupported encrypted secrets KDF id: {kdf_id}")
    if cipher_id != _CIPHER_ID:
        raise SecretsCryptoError(f"Unsupported encrypted secrets cipher id: {cipher_id}")

    salt_len = payload[cursor]
    cursor += 1
    nonce_len = payload[cursor]
    cursor += 1

    if salt_len <= 0:
        raise SecretsCryptoError("Invalid salt length")
    if nonce_len != _DEFAULT_NONCE_LEN:
        raise SecretsCryptoError("Invalid nonce length")

    expected_min = len(_MAGIC) + 5 + salt_len + nonce_len + 16
    if len(payload) < expected_min:
        raise SecretsCryptoError("Encrypted secrets payload is incomplete")

    salt = payload[cursor:cursor + salt_len]
    cursor += salt_len
    nonce = payload[cursor:cursor + nonce_len]
    cursor += nonce_len
    ciphertext = payload[cursor:]
    header = payload[:cursor]

    return salt, nonce, ciphertext, header
