from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.security.jwt.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.security.jwt.secret_key, algorithm=settings.security.jwt.algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.security.jwt.refresh_token_expire_days)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.security.jwt.secret_key, algorithm=settings.security.jwt.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.security.jwt.secret_key, algorithms=[settings.security.jwt.algorithm]
        )
        return payload
    except JWTError:
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


class EncryptionService:
    @staticmethod
    def encrypt_data(data: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import os

        key = os.urandom(32)
        nonce = os.undom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext

    @staticmethod
    def decrypt_data(encrypted_data: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        key = b"\x00" * 32
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
