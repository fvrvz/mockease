from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user
from src.db.session import get_db
from src.models.user import User
from src.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.services.auth_service import AuthService, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> UserResponse:
    service = AuthService(db)
    try:
        user = await service.register(
            email=str(body.email), username=body.username, password=body.password
        )
    except ValueError as exc:
        code = str(exc)
        if code == "EMAIL_TAKEN":
            raise HTTPException(status_code=409, detail="Email already registered")
        if code == "USERNAME_TAKEN":
            raise HTTPException(status_code=409, detail="Username already taken")
        raise HTTPException(status_code=400, detail="Registration failed")
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        is_active=user.is_active,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    try:
        user = await service.authenticate(email=str(body.email), password=body.password)
    except ValueError as exc:
        code = str(exc)
        if code == "ACCOUNT_DISABLED":
            raise HTTPException(status_code=403, detail="Account is disabled")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
    )
