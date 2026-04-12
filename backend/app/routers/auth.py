"""Auth router — email + Google OAuth"""
import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models import User, AuthProvider
from app.auth import (hash_password, verify_password, create_access_token,
                      create_refresh_token, decode_token, get_google_auth_url,
                      exchange_google_code, get_google_user_info)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterReq(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginReq(BaseModel):
    email: EmailStr
    password: str


class RefreshReq(BaseModel):
    refresh_token: str


class TokenResp(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool = False


@router.post("/register", response_model=TokenResp, status_code=201)
async def register(body: RegisterReq, db: AsyncSession = Depends(get_db)):
    if (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none():
        raise HTTPException(409, "Email already registered")
    if len(body.password) < 8:
        raise HTTPException(422, "Password must be at least 8 characters")
    user = User(id=uuid.uuid4(), email=body.email, password_hash=hash_password(body.password), full_name=body.full_name)
    db.add(user)
    await db.flush()
    return TokenResp(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id), is_new_user=True)


@router.post("/login", response_model=TokenResp)
async def login(body: LoginReq, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return TokenResp(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.post("/refresh", response_model=TokenResp)
async def refresh(body: RefreshReq, db: AsyncSession = Depends(get_db)):
    uid = decode_token(body.refresh_token, "refresh")
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found")
    return TokenResp(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.get("/google")
async def google_login():
    url = get_google_auth_url()
    return {"url": url}


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    try:
        token_data = await exchange_google_code(code)
        user_info = await get_google_user_info(token_data["access_token"])
    except Exception:
        raise HTTPException(400, "Google authentication failed")

    google_id = user_info.get("id")
    email = user_info.get("email")
    name = user_info.get("name", email)
    avatar = user_info.get("picture")

    # Find or create user
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()
    is_new = False

    if not user:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if not user:
        user = User(id=uuid.uuid4(), email=email, full_name=name, auth_provider=AuthProvider.google,
                    google_id=google_id, avatar_url=avatar, google_calendar_token=token_data, calendar_connected=True)
        db.add(user)
        is_new = True
    else:
        user.google_id = google_id
        user.avatar_url = avatar
        user.google_calendar_token = token_data
        user.calendar_connected = True
        db.add(user)

    await db.flush()
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Redirect to frontend with tokens
    redirect_url = f"{settings.FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}&is_new={is_new}"
    from fastapi.responses import RedirectResponse
    return RedirectResponse(redirect_url)
