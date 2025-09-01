# Main Objective: 
# Backend Application using FastAPI that functions as a digital wallet system.
# It should allow users to manage their wallets, maintain transaction history, and perform secure transactions(simulate money transfer between users).


from typing import Annotated, Union

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel
from datetime import datetime
from sqlmodel import Relationship
from typing import List, Optional
#-------------------------


# DATABASE TABLES
class User(SQLModel, table=True):
    id: Union[int, None] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    phone_number: str = Field(index=True, unique=True)
    balance: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="User.id")
    # Transaction type: one of 'CREDIT', 'DEBIT', 'TRANSFER_IN', 'TRANSFER_OUT'
    transaction_type: str
    recipient_user_id: int = Field(foreign_key="User.id")
    amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# REQUEST RESPONSE MODELS
class UserBase(SQLModel):
    username: str = Field(index=True)
    email: str = Field(index=True)
    phone_number: str = Field(index=True)
    balance: float = Field(default=0.0)

class UserCreate(UserBase):
    username:str
    email: str
    phone_number: str

class UserPublic(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

class UserUpdate(UserBase):
    username: Optional[str] = None
    phone_number: Optional[str] = None


#----------------
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/users/", response_model=UserPublic)
def create_user(user: UserCreate, session: SessionDep):
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.get("/users/", response_model=list[UserPublic])
def read_users(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return users


@app.get("/users/{user_id}", response_model=UserPublic)
def read_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# PUT /users/{user_id} update user username and email
@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate, session: SessionDep):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.username or db_user.username
    db_user.email = user.email or db_user.email
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


# GET /wallet/{user_id}/balance
@app.get("/wallet/{user_id}/balance")
def get_wallet_balance(user_id: int, session: SessionDep):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.id,"balance": user.balance,"last_updated": user.updated_at}


# POST /wallet/{user_id}/add-money
@app.post("/wallet/{user_id}/add-money")
def add_money_to_wallet(user_id: int, amount: float,description: str, session: SessionDep):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.balance += amount
    session.add(user)
    session.commit()
    session.refresh(user)
    return {
  "user_id": user.id, "amount": amount, "new_balance": user.balance, "transaction_type": "CREDIT"
}