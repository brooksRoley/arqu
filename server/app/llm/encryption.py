"""
AES-256-GCM encryption for user API keys.
Keys are encrypted at rest — plaintext only exists in memory during request lifecycle.
"""

from __future__ import annotations

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..config import get_settings


def _get_aes_key() -> bytes:
    """Derive the 32-byte AES key from the server encryption key env var."""
    raw = get_settings().server_encryption_key
    # If it's hex-encoded (64 chars), decode it. Otherwise hash it to 32 bytes.
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw)
        except ValueError:
            pass
    # Fallback: SHA-256 hash of the raw string to get exactly 32 bytes
    import hashlib
    return hashlib.sha256(raw.encode()).digest()


def encrypt_api_key(plaintext_key: str) -> tuple[bytes, bytes]:
    """
    Encrypt an API key string.
    Returns (encrypted_key, nonce) — both stored in DB as BYTEA.
    """
    aes_key = _get_aes_key()
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    aesgcm = AESGCM(aes_key)
    encrypted = aesgcm.encrypt(nonce, plaintext_key.encode("utf-8"), None)
    return encrypted, nonce


def decrypt_api_key(encrypted_key: bytes, nonce: bytes) -> str:
    """
    Decrypt an API key. Returns the plaintext string.
    Only called during LLM proxy requests — never stored or logged.
    """
    aes_key = _get_aes_key()
    aesgcm = AESGCM(aes_key)
    plaintext = aesgcm.decrypt(nonce, encrypted_key, None)
    return plaintext.decode("utf-8")


def key_hint(plaintext_key: str) -> str:
    """Extract last 4 characters for display: '...xK4m'"""
    if len(plaintext_key) < 4:
        return "****"
    return f"...{plaintext_key[-4:]}"


async def get_user_llm_key(user_id: str, providers: list[str] | None = None) -> tuple[str, str] | None:
    """
    Fetch and decrypt a user's stored LLM API key.

    If providers is given, tries each in order and returns the first match.
    Returns (provider, plaintext_key) or None if no key found.
    """
    from ..db import get_conn

    if providers is None:
        providers = ["anthropic", "openai", "google", "xai", "together"]

    async with get_conn() as conn:
        for provider in providers:
            row = await conn.fetchrow(
                "SELECT encrypted_key, key_nonce FROM user_api_keys WHERE user_id = $1 AND provider = $2",
                __import__("uuid").UUID(user_id), provider,
            )
            if row:
                plaintext = decrypt_api_key(row["encrypted_key"], row["key_nonce"])
                return provider, plaintext

    return None
