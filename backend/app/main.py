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
    locality: Mapped[str] = mapped_column(String(200), default="")
    street: Mapped[str] = mapped_column(String(200), default="")
    building: Mapped[str] = mapped_column(String(100), default="")
    apartment: Mapped[str] = mapped_column(String(100), default="")
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
    address_type: str = Field(default="apartment", pattern="^(locality|street|building|apartment|other)$")
    locality: str = Field(default="", max_length=200)
    street: str = Field(default="", max_length=200)
    building: str = Field(default="", max_length=100)
    apartment: str = Field(default="", max_length=100)


class AddressUpdate(AddressCreate):
    pass


class AddressResponse(BaseModel):
    id: int
    address_text: str
    address_type: str
    locality: str
    street: str
    building: str
    apartment: str
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


class CounterpartyUpdate(CounterpartyCreate):
    pass


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


class ResidentUpdate(ResidentCreate):
    pass


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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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


def migrate_address_columns() -> None:
    # Preserve the existing Docker/PostgreSQL volume when address components are added.
    with engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE addresses ADD COLUMN IF NOT EXISTS locality VARCHAR(200) NOT NULL DEFAULT ''")
        connection.exec_driver_sql("ALTER TABLE addresses ADD COLUMN IF NOT EXISTS street VARCHAR(200) NOT NULL DEFAULT ''")
        connection.exec_driver_sql("ALTER TABLE addresses ADD COLUMN IF NOT EXISTS building VARCHAR(100) NOT NULL DEFAULT ''")
        connection.exec_driver_sql("ALTER TABLE addresses ADD COLUMN IF NOT EXISTS apartment VARCHAR(100) NOT NULL DEFAULT ''")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    migrate_address_columns()
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


def compose_address(data: AddressCreate) -> str:
    parts = []
    address_type = data.address_type
    locality = data.locality.strip()
    street = data.street.strip()
    building = data.building.strip()
    apartment = data.apartment.strip()

    if not locality:
        raise HTTPException(status_code=422, detail="Укажите населённый пункт")

    if address_type == "locality":
        parts.append(locality)
    elif address_type == "street":
        if not street:
            raise HTTPException(status_code=422, detail="Укажите название улицы")
        parts.extend([locality, "ул. " + street])
    elif address_type == "building":
        if not building:
            raise HTTPException(status_code=422, detail="Укажите номер дома")
        parts.extend([locality, "д. " + building])
    elif address_type == "apartment":
        if not building:
            raise HTTPException(status_code=422, detail="Укажите номер дома")
        if not apartment:
            raise HTTPException(status_code=422, detail="Укажите номер квартиры")
        parts.extend([locality, "д. " + building, "кв. " + apartment])
    else:
        parts.append(locality)
        if street:
            parts.append("ул. " + street)
        if building:
            parts.append("д. " + building)
        if apartment:
            parts.append("кв. " + apartment)

    return ", ".join(parts)


def address_response(address: Address) -> AddressResponse:
    return AddressResponse(id=address.id, address_text=address.address_text, address_type=address.address_type, locality=address.locality, street=address.street, building=address.building, apartment=address.apartment, is_active=address.is_active)


@app.get("/api/addresses", response_model=list[AddressResponse])
def list_addresses(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[AddressResponse]:
    addresses = db.scalars(select(Address).where(Address.is_active.is_(True)).order_by(Address.address_text)).all()
    return [address_response(a) for a in addresses]


@app.post("/api/addresses", response_model=AddressResponse, status_code=201)
def create_address(data: AddressCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> AddressResponse:
    address_text = compose_address(data)
    if len(address_text) < 2:
        raise HTTPException(status_code=422, detail="Заполните хотя бы одно поле адреса")
    if db.scalar(select(Address).where(func.lower(Address.address_text) == address_text.lower())):
        raise HTTPException(status_code=409, detail="Такой адрес уже есть в справочнике")
    address = Address(address_text=address_text, address_type=data.address_type, locality=data.locality.strip(), street=data.street.strip(), building=data.building.strip(), apartment=data.apartment.strip())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address_response(address)


@app.put("/api/addresses/{address_id}", response_model=AddressResponse)
def update_address(address_id: int, data: AddressUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> AddressResponse:
    address = db.get(Address, address_id)
    if address is None or not address.is_active:
        raise HTTPException(status_code=404, detail="Адрес не найден")
    address_text = compose_address(data)
    if len(address_text) < 2:
        raise HTTPException(status_code=422, detail="Заполните хотя бы одно поле адреса")
    duplicate = db.scalar(select(Address).where(func.lower(Address.address_text) == address_text.lower(), Address.id != address_id))
    if duplicate:
        raise HTTPException(status_code=409, detail="Такой адрес уже есть в справочнике")
    address.address_text=address_text; address.address_type=data.address_type; address.locality=data.locality.strip(); address.street=data.street.strip(); address.building=data.building.strip(); address.apartment=data.apartment.strip()
    db.commit()
    db.refresh(address)
    return address_response(address)


@app.delete("/api/addresses/{address_id}", status_code=204)
def delete_address(address_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    address = db.get(Address, address_id)
    if address is None or not address.is_active:
        raise HTTPException(status_code=404, detail="Адрес не найден")
    if db.scalar(select(Resident).where(Resident.address_id == address_id)) or db.scalar(select(ServiceRequest).where(ServiceRequest.address_id == address_id)):
        raise HTTPException(status_code=409, detail="Адрес используется жильцом или заявкой и не может быть удалён")
    address.is_active=False
    db.commit()




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


@app.put("/api/counterparties/{item_id}", response_model=CounterpartyResponse)
def update_counterparty(item_id: int, data: CounterpartyUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> CounterpartyResponse:
    item=db.get(Counterparty,item_id)
    if item is None: raise HTTPException(status_code=404, detail="Контрагент не найден")
    name=data.name.strip()
    if db.scalar(select(Counterparty).where(func.lower(Counterparty.name)==name.lower(), Counterparty.id!=item_id)): raise HTTPException(status_code=409, detail="Такой контрагент уже есть в справочнике")
    item.name=name; item.inn=data.inn.strip(); item.kpp=data.kpp.strip(); item.ogrn=data.ogrn.strip(); item.postal_address=data.postal_address.strip(); item.legal_address=data.legal_address.strip(); item.phone=data.phone.strip(); item.email=data.email.strip(); item.comment=data.comment.strip()
    db.commit(); db.refresh(item)
    return CounterpartyResponse(id=item.id, name=item.name, inn=item.inn, kpp=item.kpp, ogrn=item.ogrn, postal_address=item.postal_address, legal_address=item.legal_address, phone=item.phone, email=item.email, comment=item.comment)


@app.delete("/api/counterparties/{item_id}", status_code=204)
def delete_counterparty(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item=db.get(Counterparty,item_id)
    if item is None: raise HTTPException(status_code=404, detail="Контрагент не найден")
    db.delete(item)
    db.commit()


@app.get("/api/residents", response_model=list[ResidentResponse])
def list_residents(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[ResidentResponse]:
    items = db.scalars(select(Resident).order_by(Resident.last_name, Resident.first_name, Resident.middle_name)).all()
    return [ResidentResponse(id=item.id, last_name=item.last_name, first_name=item.first_name, middle_name=item.middle_name, birth_date=item.birth_date.date().isoformat() if item.birth_date else None, address_id=item.address_id, address_text=item.address.address_text, phone=item.phone, comment=item.comment) for item in items]


@app.post("/api/residents", response_model=ResidentResponse, status_code=201)
def create_resident(data: ResidentCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ResidentResponse:
    address = db.get(Address, data.address_id)
    if address is None or not address.is_active:
        raise HTTPException(status_code=422, detail="Выберите адрес из действующего справочника")
    birth_date = None
    if data.birth_date:
        try:
            birth_date = datetime.strptime(data.birth_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=422, detail="Дата рождения указана неверно")
    item = Resident(last_name=data.last_name.strip(), first_name=data.first_name.strip(), middle_name=data.middle_name.strip(), birth_date=birth_date, address_id=address.id, phone=data.phone.strip(), comment=data.comment.strip())
    db.add(item)
    db.commit()
    db.refresh(item)
    return ResidentResponse(id=item.id, last_name=item.last_name, first_name=item.first_name, middle_name=item.middle_name, birth_date=item.birth_date.date().isoformat() if item.birth_date else None, address_id=item.address_id, address_text=address.address_text, phone=item.phone, comment=item.comment)


@app.put("/api/residents/{item_id}", response_model=ResidentResponse)
def update_resident(item_id: int, data: ResidentUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ResidentResponse:
    item=db.get(Resident,item_id)
    if item is None: raise HTTPException(status_code=404, detail="Жилец не найден")
    address=db.get(Address,data.address_id)
    if address is None or not address.is_active: raise HTTPException(status_code=422, detail="Выберите адрес из действующего справочника")
    birth_date=None
    if data.birth_date:
        try: birth_date=datetime.strptime(data.birth_date,"%Y-%m-%d")
        except ValueError: raise HTTPException(status_code=422, detail="Дата рождения указана неверно")
    item.last_name=data.last_name.strip(); item.first_name=data.first_name.strip(); item.middle_name=data.middle_name.strip(); item.birth_date=birth_date; item.address_id=address.id; item.phone=data.phone.strip(); item.comment=data.comment.strip()
    db.commit(); db.refresh(item)
    return ResidentResponse(id=item.id,last_name=item.last_name,first_name=item.first_name,middle_name=item.middle_name,birth_date=item.birth_date.date().isoformat() if item.birth_date else None,address_id=item.address_id,address_text=address.address_text,phone=item.phone,comment=item.comment)


@app.delete("/api/residents/{item_id}", status_code=204)
def delete_resident(item_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    item=db.get(Resident,item_id)
    if item is None: raise HTTPException(status_code=404,detail="Жилец не найден")
    db.delete(item)
    db.commit()


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
