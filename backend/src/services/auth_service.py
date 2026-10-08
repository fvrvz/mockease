from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config.settings import settings
from src.models.user import User
from src.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

import bcrypt


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))


def create_access_token(payload: dict[str, Any]) -> str:
    data = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    data.update({"exp": expire})
    return jwt.encode(data, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def register(self, email: str, username: str, password: str) -> User:
        if await self.repo.get_by_email(email):
            raise ValueError("EMAIL_TAKEN")
        if await self.repo.get_by_username(username):
            raise ValueError("USERNAME_TAKEN")
        password_hash = hash_password(password)
        return await self.repo.create(email=email, username=username, password_hash=password_hash)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("INVALID_CREDENTIALS")
        if not user.is_active:
            raise ValueError("ACCOUNT_DISABLED")
        return user
