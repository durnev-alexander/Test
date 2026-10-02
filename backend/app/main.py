
@app.get("/api/addresses", response_model=list[AddressResponse])
def list_addresses(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[AddressResponse]:
    addresses = db.scalars(select(Address).where(Address.is_active.is_(True)).order_by(Address.address_text)).all()
    return [AddressResponse(id=a.id, address_text=a.address_text, address_type=a.address_type, locality=a.locality, street=a.street, building=a.building, apartment=a.apartment, is_active=a.is_active) for a in addresses]

def compose_address(data: AddressCreate) -> str:
    parts = []
    if data.locality.strip(): parts.append(data.locality.strip())
    if data.street.strip(): parts.append("ул. " + data.street.strip())
    if data.building.strip(): parts.append("д. " + data.building.strip())
    if data.apartment.strip(): parts.append("кв. " + data.apartment.strip())
    return ", ".join(parts)

@app.post("/api/addresses", response_model=AddressResponse, status_code=201)
def create_address(data: AddressCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> AddressResponse:
    address_text = compose_address(data)
    if len(address_text) < 2: raise HTTPException(status_code=422, detail="Заполните хотя бы одно поле адреса")
    if db.scalar(select(Address).where(func.lower(Address.address_text) == address_text.lower())): raise HTTPException(status_code=409, detail="Такой адрес уже есть в справочнике")
    address = Address(address_text=address_text, address_type=data.address_type, locality=data.locality.strip(), street=data.street.strip(), building=data.building.strip(), apartment=data.apartment.strip())
    db.add(address); db.commit(); db.refresh(address)
    return AddressResponse(id=address.id, address_text=address.address_text, address_type=address.address_type, locality=address.locality, street=address.street, building=address.building, apartment=address.apartment, is_active=address.is_active)

@app.put("/api/addresses/{address_id}", response_model=AddressResponse)
def update_address(address_id: int, data: AddressUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> AddressResponse:
    address = db.get(Address, address_id)
    if address is None or not address.is_active: raise HTTPException(status_code=404, detail="Адрес не найден")
    address_text = compose_address(data)
    if len(address_text) < 2: raise HTTPException(status_code=422, detail="Заполните хотя бы одно поле адреса")
    duplicate = db.scalar(select(Address).where(func.lower(Address.address_text) == address_text.lower(), Address.id != address_id))
    if duplicate: raise HTTPException(status_code=409, detail="Такой адрес уже есть в справочнике")
    address.address_text=address_text; address.address_type=data.address_type; address.locality=data.locality.strip(); address.street=data.street.strip(); address.building=data.building.strip(); address.apartment=data.apartment.strip()
    db.commit(); db.refresh(address)
    return AddressResponse(id=address.id, address_text=address.address_text, address_type=address.address_type, locality=address.locality, street=address.street, building=address.building, apartment=address.apartment, is_active=address.is_active)

@app.delete("/api/addresses/{address_id}", status_code=204)
def delete_address(address_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    address = db.get(Address, address_id)
    if address is None or not address.is_active: raise HTTPException(status_code=404, detail="Адрес не найден")
    if db.scalar(select(Resident).where(Resident.address_id == address_id)) or db.scalar(select(ServiceRequest).where(ServiceRequest.address_id == address_id)):
        raise HTTPException(status_code=409, detail="Адрес используется жильцом или заявкой и не может быть удалён")
    address.is_active=False; db.commit()

@app.get("/api/counterparties", response_model=list[CounterpartyResponse])
def list_counterparties(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[CounterpartyResponse]:
    items = db.scalars(select(Counterparty).order_by(Counterparty.name)).all()
    return [CounterpartyResponse(id=item.id, name=item.name, inn=item.inn, kpp=item.kpp, ogrn=item.ogrn, postal_address=item.postal_address, legal_address=item.legal_address, phone=item.phone, email=item.email, comment=item.comment) for item in items]

@app.post("/api/counterparties", response_model=CounterpartyResponse, status_code=201)
def create_counterparty(data: CounterpartyCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> CounterpartyResponse:
    name=data.name.strip()
    if db.scalar(select(Counterparty).where(func.lower(Counterparty.name) == name.lower())): raise HTTPException(status_code=409, detail="Такой контрагент уже есть в справочнике")
    item=Counterparty(name=name, inn=data.inn.strip(), kpp=data.kpp.strip(), ogrn=data.ogrn.strip(), postal_address=data.postal_address.strip(), legal_address=data.legal_address.strip(), phone=data.phone.strip(), email=data.email.strip(), comment=data.comment.strip())
    db.add(item); db.commit(); db.refresh(item)
    return CounterpartyResponse(id=item.id, name=item.name, inn=item.inn, kpp=item.kpp, ogrn=item.ogrn, postal_address=item.postal_address, legal_address=item.legal_address, phone=item.phone, email=item.email, comment=item.comment)

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
    db.delete(item); db.commit()

@app.get("/api/residents", response_model=list[ResidentResponse])
def list_residents(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[ResidentResponse]:
    items = db.scalars(select(Resident).order_by(Resident.last_name, Resident.first_name, Resident.middle_name)).all()
    return [ResidentResponse(id=item.id, last_name=item.last_name, first_name=item.first_name, middle_name=item.middle_name, birth_date=item.birth_date.date().isoformat() if item.birth_date else None, address_id=item.address_id, address_text=item.address.address_text, phone=item.phone, comment=item.comment) for item in items]

@app.post("/api/residents", response_model=ResidentResponse, status_code=201)
def create_resident(data: ResidentCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ResidentResponse:
    address=db.get(Address,data.address_id)
    if address is None or not address.is_active: raise HTTPException(status_code=422, detail="Выберите адрес из действующего справочника")
    birth_date=None
    if data.birth_date:
        try: birth_date=datetime.strptime(data.birth_date,"%Y-%m-%d")
        except ValueError: raise HTTPException(status_code=422, detail="Дата рождения указана неверно")
    item=Resident(last_name=data.last_name.strip(), first_name=data.first_name.strip(), middle_name=data.middle_name.strip(), birth_date=birth_date, address_id=address.id, phone=data.phone.strip(), comment=data.comment.strip())
    db.add(item); db.commit(); db.refresh(item)
    return ResidentResponse(id=item.id,last_name=item.last_name,first_name=item.first_name,middle_name=item.middle_name,birth_date=item.birth_date.date().isoformat() if item.birth_date else None,address_id=item.address_id,address_text=address.address_text,phone=item.phone,comment=item.comment)

@app.put("/api/residents/{item_id}", response_model=ResidentResponse)
def update_resident(item_id:int,data:ResidentUpdate,user:User=Depends(current_user),db:Session=Depends(get_db))->ResidentResponse:
    item=db.get(Resident,item_id)
    if item is None: raise HTTPException(status_code=404,detail="Жилец не найден")
    address=db.get(Address,data.address_id)
    if address is None or not address.is_active: raise HTTPException(status_code=422,detail="Выберите адрес из действующего справочника")
    birth_date=None
    if data.birth_date:
        try: birth_date=datetime.strptime(data.birth_date,"%Y-%m-%d")
        except ValueError: raise HTTPException(status_code=422,detail="Дата рождения указана неверно")
    item.last_name=data.last_name.strip(); item.first_name=data.first_name.strip(); item.middle_name=data.middle_name.strip(); item.birth_date=birth_date; item.address_id=address.id; item.phone=data.phone.strip(); item.comment=data.comment.strip()
    db.commit(); db.refresh(item)
    return ResidentResponse(id=item.id,last_name=item.last_name,first_name=item.first_name,middle_name=item.middle_name,birth_date=item.birth_date.date().isoformat() if item.birth_date else None,address_id=item.address_id,address_text=address.address_text,phone=item.phone,comment=item.comment)

@app.delete("/api/residents/{item_id}", status_code=204)
def delete_resident(item_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    item=db.get(Resident,item_id)
    if item is None: raise HTTPException(status_code=404,detail="Жилец не найден")
    db.delete(item); db.commit()

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
