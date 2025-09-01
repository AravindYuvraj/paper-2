# Main Objective: 
# Backend Application using FastAPI that functions as a digital wallet system.
# It should allow users to manage their wallets, maintain transaction history, and perform secure transactions(simulate money transfer between users).


from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel
from datetime import datetime
from sqlmodel import Relationship



# Relationship class to link between the user and transactions
class UserTransactionLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    transaction_id: int = Field(foreign_key="transaction.id", primary_key=True)
#-------------------------
# Database Models (TABLES)
#-------------------------
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    # password: str
    phone_number: str = Field(index=True, unique=True)
    balance: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    transactions: list["Transaction"] = Relationship(back_populates="user", link_model=UserTransactionLink)

class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    # Transaction type: one of 'CREDIT', 'DEBIT', 'TRANSFER_IN', 'TRANSFER_OUT'
    transaction_type: str
    recipient_user_id: int = Field(foreign_key="user.id")
    amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

#------------------
# REQUEST MODELS
#-------------------
class UserCreate(BaseModel):
    username: str
    email: str
    phone_number: str

class TransactionRequest(BaseModel):
    user_id: int
    transaction_type: str
    recipient_user_id: int
    amount: float
    balance: float

    class Config:
        orm_mode = True

class TransactionResponse(BaseModel):
    user_id: int
    transaction_type: str
    recipient_user_id: int
    amount: float

    class Config:
        orm_mode = True

        

#----------------
# DATABASE SETUP
#----------------

sqlite_file_name = "transaction.db"
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

#------------------
# API ENDPOINTS
#-----------------

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return {"Hello": "Welcome to the Digital Wallet API"}


# CRUD for User

# 1. Create
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, session: SessionDep):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

