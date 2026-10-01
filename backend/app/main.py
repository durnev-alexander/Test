import os
from typing import Generator

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from datetime import datetime, timezone
from pwdlib import PasswordHash

from .security import create_access_token, decode_access_token, hash_password, verify_password

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://jkx:change-me-local-only@localhost:5432/jkx",
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    username: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


app = FastAPI(title="ЖКХ API", version="0.1.0")
origins = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_demo_user(db: Session) -> None:
    username = os.getenv("DEMO_USERNAME", "demo")
    password = os.getenv("DEMO_PASSWORD", "demo")
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        db.add(User(username=username, password_hash=hash_password(password), is_active=True))
        db.commit()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_demo_user(db)


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительная или истёкшая сессия",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if not username:
            raise unauthorized
    except jwt.PyJWTError:
        raise unauthorized
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not user.is_active:
        raise unauthorized
    return user


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == data.username))
    if user is None or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    return TokenResponse(
        access_token=create_access_token(user.username),
        user=UserResponse(username=user.username, is_active=user.is_active),
    )


@app.get("/api/auth/me", response_model=UserResponse)
def me(user: User = Depends(current_user)) -> UserResponse:
    return UserResponse(username=user.username, is_active=user.is_active)


@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user)) -> dict:
    return {
        "message": f"Добро пожаловать, {user.username}",
        "address_count": 0,
        "open_requests": 0,
        "pending_requests": 0,
    }
