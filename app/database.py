"""Simulation tables and session helpers.

Each SQLite file is an independent simulation stored under DATA_DIR.
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


class SimulationMetadata(Base):
    __tablename__ = "simulation_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<SimulationMetadata id={self.id} "
            f"start={self.start_datetime} end={self.end_datetime}>"
        )


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    balance_entries = relationship(
        "BalanceEntry", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Account id={self.id} name={self.name!r}>"


class BalanceEntry(Base):
    __tablename__ = "balance_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(16), nullable=False)
    description = Column(Text, nullable=True)
    effective_time = Column(DateTime, nullable=False)
    rule_id = Column(Integer, ForeignKey("funding_rules.id"), nullable=True)

    account = relationship("Account", back_populates="balance_entries")

    def __repr__(self) -> str:
        return (
            f"<BalanceEntry id={self.id} account={self.account_id} "
            f"amount={self.amount} currency={self.currency!r}>"
        )


class FundingRule(Base):
    __tablename__ = "funding_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_type = Column(String(16), nullable=False)  # "BACKUP_FUNDING" or "TOPUP"
    target_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    source_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    time_of_day = Column(String(8), nullable=False)  # "HH:MM:SS" in ET
    currency = Column(String(16), nullable=False)
    threshold = Column(Float, nullable=False, default=0.0)
    target_amount = Column(Float, nullable=False, default=0.0)

    target_account = relationship("Account", foreign_keys=[target_account_id])
    source_account = relationship("Account", foreign_keys=[source_account_id])

    def __repr__(self) -> str:
        return (
            f"<FundingRule id={self.id} "
            f"target={self.target_account_id} source={self.source_account_id} "
            f"time={self.time_of_day!r}>"
        )


def get_balance(session, account_id, timestamp, currency, rule_id=None):
    """Return the sum of all balance entries for an account/currency at or before a timestamp."""
    from sqlalchemy import func
    filters = [
        BalanceEntry.account_id == account_id,
        BalanceEntry.currency == currency,
        BalanceEntry.effective_time <= timestamp,
    ]
    if rule_id is not None:
        filters.append(BalanceEntry.rule_id == rule_id)

    result = session.query(func.coalesce(func.sum(BalanceEntry.amount), 0.0)).filter(*filters).scalar()
    return result

def get_balance_at_timestamp(session, account_id, timestamp, currency, rule_id=None):
    """Return the sum of all balance entries for an account/currency at or before a timestamp."""
    from sqlalchemy import func
    filters = [
        BalanceEntry.account_id == account_id,
        BalanceEntry.currency == currency,
        BalanceEntry.effective_time == timestamp,
    ]
    if rule_id is not None:
        filters.append(BalanceEntry.rule_id == rule_id)

    result = session.query(func.coalesce(func.sum(BalanceEntry.amount), 0.0)).filter(*filters).scalar()
    return result


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _sim_path(sim_name: str) -> str:
    return os.path.join(DATA_DIR, f"{sim_name}.db")


def _make_engine(sim_name: str):
    return create_engine(
        f"sqlite:///{_sim_path(sim_name)}",
        connect_args={"check_same_thread": False},
    )


@contextmanager
def get_session(sim_name: str):
    """Create a throwaway engine + session, yield it, then tear everything down."""
    engine = _make_engine(sim_name)
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


def create_simulation(sim_name: str, start_date: str | None = None, end_date: str | None = None) -> None:
    """Create a new SQLite file with all tables, optionally with date range metadata."""
    engine = _make_engine(sim_name)
    Base.metadata.create_all(engine)
    if start_date or end_date:
        session: Session = sessionmaker(bind=engine)()
        try:
            meta = SimulationMetadata(
                start_datetime=datetime.fromisoformat(start_date) if start_date else datetime.now(timezone.utc),
                end_datetime=datetime.fromisoformat(end_date) if end_date else datetime.now(timezone.utc),
            )
            session.add(meta)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    engine.dispose()


def simulation_exists(sim_name: str) -> bool:
    return os.path.isfile(_sim_path(sim_name))


def list_simulations() -> list[str]:
    """Return sorted simulation names (without the .db extension)."""
    return sorted(
        f[:-3]
        for f in os.listdir(DATA_DIR)
        if f.endswith(".db") and os.path.isfile(os.path.join(DATA_DIR, f))
    )


def ensure_tables(sim_name: str) -> None:
    """Ensure all ORM tables exist in the given simulation DB (idempotent)."""
    engine = _make_engine(sim_name)
    Base.metadata.create_all(engine)
    engine.dispose()


def delete_simulation(sim_name: str) -> None:
    path = _sim_path(sim_name)
    if os.path.isfile(path):
        os.remove(path)
