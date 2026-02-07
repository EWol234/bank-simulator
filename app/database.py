"""Dynamic multi-database manager.

Each SQLite file is an independent database. The DatabaseManager handles
engine creation, session generation, and lifecycle (create / list / delete)
for any number of database files stored under a configurable data directory.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


class DatabaseManager:
    """Manages multiple independent SQLite database files."""

    def __init__(self, data_dir: str) -> None:
        self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        self._engines: dict[str, Engine] = {}

    # ------------------------------------------------------------------
    # Engine helpers
    # ------------------------------------------------------------------

    def _db_path(self, db_name: str) -> str:
        return os.path.join(self.data_dir, f"{db_name}.db")

    def _get_or_create_engine(self, db_name: str) -> Engine:
        if db_name not in self._engines:
            path = self._db_path(db_name)
            self._engines[db_name] = create_engine(
                f"sqlite:///{path}",
                connect_args={"check_same_thread": False},
            )
        return self._engines[db_name]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_database(self, db_name: str) -> str:
        """Create a new SQLite file with all tables. Returns the file path."""
        engine = self._get_or_create_engine(db_name)
        Base.metadata.create_all(engine)
        return self._db_path(db_name)

    def database_exists(self, db_name: str) -> bool:
        return os.path.isfile(self._db_path(db_name))

    def list_databases(self) -> list[str]:
        """Return the names (without extension) of all .db files."""
        return sorted(
            f[:-3]
            for f in os.listdir(self.data_dir)
            if f.endswith(".db") and os.path.isfile(os.path.join(self.data_dir, f))
        )

    def delete_database(self, db_name: str) -> None:
        """Dispose the engine (if cached) and remove the file."""
        if db_name in self._engines:
            self._engines[db_name].dispose()
            del self._engines[db_name]
        path = self._db_path(db_name)
        if os.path.isfile(path):
            os.remove(path)

    def get_session(self, db_name: str) -> Session:
        """Return a new Session bound to the given database."""
        engine = self._get_or_create_engine(db_name)
        return sessionmaker(bind=engine)()

    @contextmanager
    def session_scope(self, db_name: str) -> Generator[Session, None, None]:
        """Context manager that provides a transactional session scope.

        Commits on success, rolls back on exception, and always closes.
        """
        session = self.get_session(db_name)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
