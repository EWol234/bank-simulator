"""Pydantic schemas for request/response serialization."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ------------------------------------------------------------------
# Database
# ------------------------------------------------------------------


class DatabaseCreate(BaseModel):
    name: str


class DatabaseOut(BaseModel):
    name: str


class DatabaseList(BaseModel):
    databases: list[str]


# ------------------------------------------------------------------
# Account
# ------------------------------------------------------------------


class AccountCreate(BaseModel):
    name: str
    balance: float = 0.0


class AccountUpdate(BaseModel):
    name: str | None = None
    balance: float | None = None


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    balance: float
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------------
# Transaction
# ------------------------------------------------------------------


class TransactionCreate(BaseModel):
    from_account_id: int | None = None
    to_account_id: int | None = None
    amount: float
    description: str | None = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_account_id: int | None
    to_account_id: int | None
    amount: float
    description: str | None
    created_at: datetime
