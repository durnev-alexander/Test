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


class Address(Base):
    __tablename__ = "addresses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address_text: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    address_type: Mapped[str] = mapped_column(String(30), default="other")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)




class Counterparty(Base):
    __tablename__ = "counterparties"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(300), index=True)
    inn: Mapped[str] = mapped_column(String(20), default="")
    kpp: Mapped[str] = mapped_column(String(20), default="")
    ogrn: Mapped[str] = mapped_column(String(20), default="")
    postal_address: Mapped[str] = mapped_column(String(500), default="")
    legal_address: Mapped[str] = mapped_column(String(500), default="")
    phone: Mapped[str] = mapped_column(String(100), default="")
    email: Mapped[str] = mapped_column(String(254), default="")
    comment: Mapped[str] = mapped_column(Text, default="")


class Resident(Base):
    __tablename__ = "residents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_name: Mapped[str] = mapped_column(String(120), index=True)
    first_name: Mapped[str] = mapped_column(String(120))
    middle_name: Mapped[str] = mapped_column(String(120), default="")
    birth_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"), index=True)
    phone: Mapped[str] = mapped_column(String(100), default="")
    comment: Mapped[str] = mapped_column(Text, default="")
    address: Mapped[Address] = relationship()


class ServiceRequest(Base):
    __tablename__ = "service_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    status: Mapped[str] = mapped_column(String(30), default="open")
    address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"), index=True)
    created_by: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    address: Mapped[Address] = relationship()


class AddressCreate(BaseModel):
    address_text: str = Field(min_length=2, max_length=500)
    address_type: str = Field(default="other", pattern="^(locality|street|building|apartment|other)$")


class AddressResponse(BaseModel):
    id: int
    address_text: str
    address_type: str
    is_active: bool




class CounterpartyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    inn: str = Field(default="", max_length=20)
    kpp: str = Field(default="", max_length=20)
    ogrn: str = Field(default="", max_length=20)
    postal_address: str = Field(default="", max_length=500)
    legal_address: str = Field(default="", max_length=500)
    phone: str = Field(default="", max_length=100)
    email: str = Field(default="", max_length=254)
    comment: str = Field(default="", max_length=5000)


class CounterpartyResponse(BaseModel):
    id: int
    name: str
    inn: str
    kpp: str
    ogrn: str
    postal_address: str
    legal_address: str
    phone: str
    email: str
    comment: str


class ResidentCreate(BaseModel):
    last_name: str = Field(min_length=1, max_length=120)
    first_name: str = Field(min_length=1, max_length=120)
    middle_name: str = Field(default="", max_length=120)
    birth_date: str | None = Field(default=None)
    address_id: int = Field(gt=0)
    phone: str = Field(default="", max_length=100)
    comment: str = Field(default="", max_length=5000)


class ResidentResponse(BaseModel):
    id: int
    last_name: str
    first_name: str
    middle_name: str
    birth_date: str | None
    address_id: int
    address_text: str
    phone: str
    comment: str


class RequestCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=5000)
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    address_id: int = Field(gt=0)


class RequestResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: str
    status: str
    address_id: int
    address_text: str
    created_by: str
    created_at: datetime


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


@app.get("/api/addresses", response_model=list[AddressResponse])
def list_addresses(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[AddressResponse]:
    addresses = db.scalars(select(Address).where(Address.is_active.is_(True)).order_by(Address.address_text)).all()
    return [AddressResponse(id=a.id, address_text=a.address_text, address_type=a.address_type, is_active=a.is_active) for a in addresses]


@app.post("/api/addresses", response_model=AddressResponse, status_code=201)
def create_address(data: AddressCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> AddressResponse:
    address_text = data.address_text.strip()
    if db.scalar(select(Address).where(func.lower(Address.address_text) == address_text.lower())):
        raise HTTPException(status_code=409, detail="Такой адрес уже есть в справочнике")
    address = Address(address_text=address_text, address_type=data.address_type)
    db.add(address)
    db.commit()
    db.refresh(address)
    return AddressResponse(id=address.id, address_text=address.address_text, address_type=address.address_type, is_active=address.is_active)




@app.get("/api/counterparties", response_model=list[CounterpartyResponse])
def list_counterparties(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[CounterpartyResponse]:
    items = db.scalars(select(Counterparty).order_by(Counterparty.name)).all()
    return [CounterpartyResponse(
        id=item.id, name=item.name, inn=item.inn, kpp=item.kpp, ogrn=item.ogrn,
        postal_address=item.postal_address, legal_address=item.legal_address,
        phone=item.phone, email=item.email, comment=item.comment,
    ) for item in items]


@app.post("/api/counterparties", response_model=CounterpartyResponse, status_code=201)
def create_counterparty(data: CounterpartyCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> CounterpartyResponse:
    name = data.name.strip()
    if db.scalar(select(Counterparty).where(func.lower(Counterparty.name) == name.lower())):
        raise HTTPException(status_code=409, detail="Такой контрагент уже есть в справочнике")
    item = Counterparty(
        name=name, inn=data.inn.strip(), kpp=data.kpp.strip(), ogrn=data.ogrn.strip(),
        postal_address=data.postal_address.strip(), legal_address=data.legal_address.strip(),
        phone=data.phone.strip(), email=data.email.strip(), comment=data.comment.strip(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return CounterpartyResponse(
        id=item.id, name=item.name, inn=item.inn, kpp=item.kpp, ogrn=item.ogrn,
        postal_address=item.postal_address, legal_address=item.legal_address,
        phone=item.phone, email=item.email, comment=item.comment,
    )


@app.get("/api/requests", response_model=list[RequestResponse])
def list_requests(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[RequestResponse]:
    items = db.scalars(select(ServiceRequest).order_by(ServiceRequest.created_at.desc())).all()
    return [RequestResponse(id=r.id, title=r.title, description=r.description, priority=r.priority, status=r.status, address_id=r.address_id, address_text=r.address.address_text, created_by=r.created_by, created_at=r.created_at) for r in items]


@app.post("/api/requests", response_model=RequestResponse, status_code=201)
def create_request(data: RequestCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> RequestResponse:
    address = db.get(Address, data.address_id)
    if address is None or not address.is_active:
        raise HTTPException(status_code=422, detail="Выберите адрес из действующего справочника")
    item = ServiceRequest(title=data.title.strip(), description=data.description.strip(), priority=data.priority, address_id=address.id, created_by=user.username)
    db.add(item)
    db.commit()
    db.refresh(item)
    return RequestResponse(id=item.id, title=item.title, description=item.description, priority=item.priority, status=item.status, address_id=item.address_id, address_text=address.address_text, created_by=item.created_by, created_at=item.created_at)


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
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    address_count = db.scalar(select(func.count(Address.id)).where(Address.is_active.is_(True))) or 0
    open_requests = db.scalar(select(func.count(ServiceRequest.id)).where(ServiceRequest.status == "open")) or 0
    return {
        "message": f"Добро пожаловать, {user.username}",
        "address_count": address_count,
        "open_requests": open_requests,
        "pending_requests": open_requests,
    }
