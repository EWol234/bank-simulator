"""Database tables and session helpers.

Each SQLite file is an independent database stored under DATA_DIR.
Sessions are created fresh per-operation — no engine caching or
connection pooling.  Simple and self-contained.
"""

import os
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

# Set once by create_app(); every helper below reads from this.
DATA_DIR: str = ""


# ------------------------------------------------------------------
# ORM models
# ------------------------------------------------------------------


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


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _db_path(db_name: str) -> str:
    return os.path.join(DATA_DIR, f"{db_name}.db")


def _make_engine(db_name: str):
    return create_engine(
        f"sqlite:///{_db_path(db_name)}",
        connect_args={"check_same_thread": False},
    )


@contextmanager
def get_session(db_name: str):
    """Create a throwaway engine + session, yield it, then tear everything down."""
    engine = _make_engine(db_name)
    session: Session = sessionmaker(bind=engine)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def create_database(db_name: str) -> None:
    """Create a new SQLite file with all tables."""
    engine = _make_engine(db_name)
    Base.metadata.create_all(engine)
    engine.dispose()


def database_exists(db_name: str) -> bool:
    return os.path.isfile(_db_path(db_name))


def list_databases() -> list[str]:
    """Return sorted database names (without the .db extension)."""
    return sorted(
        f[:-3]
        for f in os.listdir(DATA_DIR)
        if f.endswith(".db") and os.path.isfile(os.path.join(DATA_DIR, f))
    )


def delete_database(db_name: str) -> None:
    path = _db_path(db_name)
    if os.path.isfile(path):
        os.remove(path)
