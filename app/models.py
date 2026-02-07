"""SQLAlchemy ORM models.

These models are defined against a shared declarative Base. They are not tied
to any single engine — the Base.metadata.create_all(engine) call is made
dynamically per-database file by the DatabaseManager.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    sent_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.from_account_id",
        back_populates="from_account",
    )
    received_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.to_account_id",
        back_populates="to_account",
    )

    def __repr__(self) -> str:
        return f"<Account id={self.id} name={self.name!r} balance={self.balance}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    from_account = relationship(
        "Account", foreign_keys=[from_account_id], back_populates="sent_transactions"
    )
    to_account = relationship(
        "Account",
        foreign_keys=[to_account_id],
        back_populates="received_transactions",
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} amount={self.amount} "
            f"from={self.from_account_id} to={self.to_account_id}>"
        )
