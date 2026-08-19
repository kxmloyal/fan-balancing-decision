import base64
import binascii
import hashlib
import logging
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

_FERNET_PREFIX = "fernet:"


def _derive_fernet_key(secret_key: str) -> bytes:
    salt_raw = os.environ.get("CRYPTO_SALT")
    if not salt_raw:
        raise RuntimeError("CRYPTO_SALT 环境变量未设置！密码学操作需要此变量。")
    salt = salt_raw.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    raw = secret_key.encode() if isinstance(secret_key, str) else secret_key
    return base64.urlsafe_b64encode(kdf.derive(raw))


def _get_secret_key():
    try:
        from flask import current_app

        key = current_app.config.get("SECRET_KEY")
        if key:
            return key
    except (ImportError, RuntimeError):
        pass

    key = os.environ.get("SECRET_KEY")
    if not key:
        raise RuntimeError("SECRET_KEY 未配置！请设置环境变量 SECRET_KEY 或在 Flask 配置中提供。")
    return key


def encrypt_password(password: str) -> str:
    """使用 Fernet (AES-128-CBC + HMAC-SHA256) 加密密码

    安全防护：如果输入已经是 fernet: 前缀的密文，直接返回，
    防止重复加密导致密码不可恢复。
    """
    if not password:
        return ""
    if password.startswith(_FERNET_PREFIX):
        return password
    key = _derive_fernet_key(_get_secret_key())
    f = Fernet(key)
    encrypted = f.encrypt(password.encode("utf-8"))
    return _FERNET_PREFIX + base64.urlsafe_b64encode(encrypted).decode("ascii")


def decrypt_password(encrypted_str: str) -> str:
    """解密密码，兼容旧版 XOR 加密格式。非加密明文直接返回。"""
    if not encrypted_str:
        return ""

    if encrypted_str.startswith(_FERNET_PREFIX):
        key = _derive_fernet_key(_get_secret_key())
        f = Fernet(key)
        raw = base64.urlsafe_b64decode(encrypted_str[len(_FERNET_PREFIX) :])
        return f.decrypt(raw).decode("utf-8")

    # 非 Fernet 格式：尝试旧版 XOR 解密，失败则视为明文直接返回
    try:
        return _legacy_xor_decrypt(encrypted_str)
    except (ValueError, binascii.Error, UnicodeDecodeError, RuntimeError):
        return encrypted_str


def _legacy_xor_decrypt(encrypted_str: str) -> str:
    """兼容旧版 XOR 加密的解密（移除后仅保留 Fernet）"""
    key = hashlib.sha256(_get_secret_key().encode()).digest()
    encrypted = base64.b64decode(encrypted_str.encode("ascii"))
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted)]).decode("utf-8")
