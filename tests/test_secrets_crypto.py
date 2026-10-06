from __future__ import annotations

import json
import logging

import pytest

from qyro.adapters.resources.secrets_crypto import (
    SecretsCryptoError,
    decrypt_secrets_payload,
    derive_aes256_key,
    encrypt_secrets_payload,
)


def test_encrypt_decrypt_roundtrip_for_json_payload() -> None:
    runtime_secret = b"a" * 32
    original = {"api_key": "secret", "nested": {"enabled": True}}
    payload = json.dumps(original).encode("utf-8")

    encrypted = encrypt_secrets_payload(payload, runtime_secret)
    decrypted = decrypt_secrets_payload(encrypted, runtime_secret)

    assert json.loads(decrypted.decode("utf-8")) == original


def test_modified_ciphertext_is_rejected() -> None:
    runtime_secret = b"b" * 32
    encrypted = bytearray(encrypt_secrets_payload(b'{"token":"abc"}', runtime_secret))
    encrypted[-1] ^= 0x01

    with pytest.raises(SecretsCryptoError):
        decrypt_secrets_payload(bytes(encrypted), runtime_secret)


def test_invalid_tag_is_rejected() -> None:
    runtime_secret = b"c" * 32
    encrypted = bytearray(encrypt_secrets_payload(b'{"token":"abc"}', runtime_secret))
    encrypted[-8] ^= 0x01

    with pytest.raises(SecretsCryptoError):
        decrypt_secrets_payload(bytes(encrypted), runtime_secret)


def test_invalid_salt_or_nonce_in_header_is_rejected() -> None:
    runtime_secret = b"d" * 32
    encrypted = bytearray(encrypt_secrets_payload(b'{"token":"abc"}', runtime_secret))

    # Corrupt nonce length in header.
    encrypted[10] = 11
    with pytest.raises(SecretsCryptoError):
        decrypt_secrets_payload(bytes(encrypted), runtime_secret)

    encrypted = bytearray(encrypt_secrets_payload(b'{"token":"abc"}', runtime_secret))
    # Corrupt salt length in header.
    encrypted[9] = 0
    with pytest.raises(SecretsCryptoError):
        decrypt_secrets_payload(bytes(encrypted), runtime_secret)


def test_wrong_runtime_secret_is_rejected() -> None:
    encrypted = encrypt_secrets_payload(b'{"token":"abc"}', b"e" * 32)

    with pytest.raises(SecretsCryptoError):
        decrypt_secrets_payload(encrypted, b"f" * 32)


def test_same_plaintext_produces_different_ciphertext() -> None:
    runtime_secret = b"g" * 32
    payload = b'{"token":"abc"}'

    encrypted_a = encrypt_secrets_payload(payload, runtime_secret)
    encrypted_b = encrypt_secrets_payload(payload, runtime_secret)

    assert encrypted_a != encrypted_b


def test_derived_key_has_expected_length() -> None:
    key = derive_aes256_key(runtime_secret=b"h" * 32, salt=b"s" * 16)
    assert len(key) == 32


@pytest.mark.parametrize("platform_name", ["windows", "linux", "mac"])
def test_roundtrip_is_platform_agnostic(platform_name: str) -> None:
    runtime_secret = (platform_name.encode("utf-8") * 8)[:32]
    payload = b'{"platform":"ok"}'

    encrypted = encrypt_secrets_payload(payload, runtime_secret)
    decrypted = decrypt_secrets_payload(encrypted, runtime_secret)

    assert decrypted == payload


def test_secret_values_do_not_appear_in_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    runtime_secret = b"z" * 32
    secret_payload = b'{"password":"super-secret-value"}'

    encrypted = encrypt_secrets_payload(secret_payload, runtime_secret)
    _ = decrypt_secrets_payload(encrypted, runtime_secret)

    captured = "\n".join(record.getMessage() for record in caplog.records)
    assert "super-secret-value" not in captured
    assert runtime_secret.hex() not in captured


def test_payload_format_contains_magic_and_version() -> None:
    encrypted = encrypt_secrets_payload(b"{}", b"i" * 32)

    assert encrypted.startswith(b"QYRSEC")
    assert encrypted[6] == 1
