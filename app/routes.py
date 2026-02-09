"""Schemas and API routes."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ConfigDict

from app.database import (
    Account,
    Transaction,
    create_database,
    database_exists,
    delete_database,
    get_session,
    list_databases,
)

# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------


class DatabaseCreate(BaseModel):
    name: str


class DatabaseList(BaseModel):
    databases: list[str]


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


# ------------------------------------------------------------------
# Blueprint
# ------------------------------------------------------------------

bp = Blueprint("api", __name__)


def _ensure_db(db_name: str):
    if not database_exists(db_name):
        return jsonify({"error": f"Database '{db_name}' not found"}), 404
    return None


# ------------------------------------------------------------------
# Database management
# ------------------------------------------------------------------


@bp.route("/databases", methods=["GET"])
def list_databases_route():
    names = list_databases()
    return jsonify(DatabaseList(databases=names).model_dump())


@bp.route("/databases", methods=["POST"])
def create_database_route():
    body = DatabaseCreate.model_validate(request.get_json())
    if database_exists(body.name):
        return jsonify({"error": f"Database '{body.name}' already exists"}), 409
    create_database(body.name)
    return jsonify({"name": body.name, "message": "created"}), 201


@bp.route("/databases/<db_name>", methods=["DELETE"])
def delete_database_route(db_name: str):
    if not database_exists(db_name):
        return jsonify({"error": "not found"}), 404
    delete_database(db_name)
    return jsonify({"name": db_name, "message": "deleted"})


# ------------------------------------------------------------------
# Accounts
# ------------------------------------------------------------------


@bp.route("/databases/<db_name>/accounts", methods=["GET"])
def list_accounts(db_name: str):
    err = _ensure_db(db_name)
    if err:
        return err
    with get_session(db_name) as session:
        rows = session.query(Account).order_by(Account.id).all()
        return jsonify([AccountOut.model_validate(r).model_dump(mode="json") for r in rows])


@bp.route("/databases/<db_name>/accounts", methods=["POST"])
def create_account(db_name: str):
    err = _ensure_db(db_name)
    if err:
        return err
    body = AccountCreate.model_validate(request.get_json())
    with get_session(db_name) as session:
        acct = Account(name=body.name, balance=body.balance)
        session.add(acct)
        session.flush()
        out = AccountOut.model_validate(acct).model_dump(mode="json")
    return jsonify(out), 201


@bp.route("/databases/<db_name>/accounts/<int:account_id>", methods=["GET"])
def get_account(db_name: str, account_id: int):
    err = _ensure_db(db_name)
    if err:
        return err
    with get_session(db_name) as session:
        acct = session.get(Account, account_id)
        if not acct:
            return jsonify({"error": "account not found"}), 404
        return jsonify(AccountOut.model_validate(acct).model_dump(mode="json"))


@bp.route("/databases/<db_name>/accounts/<int:account_id>", methods=["PATCH"])
def update_account(db_name: str, account_id: int):
    err = _ensure_db(db_name)
    if err:
        return err
    body = AccountUpdate.model_validate(request.get_json())
    with get_session(db_name) as session:
        acct = session.get(Account, account_id)
        if not acct:
            return jsonify({"error": "account not found"}), 404
        if body.name is not None:
            acct.name = body.name
        if body.balance is not None:
            acct.balance = body.balance
        acct.updated_at = datetime.now(timezone.utc)
        session.flush()
        return jsonify(AccountOut.model_validate(acct).model_dump(mode="json"))


@bp.route("/databases/<db_name>/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(db_name: str, account_id: int):
    err = _ensure_db(db_name)
    if err:
        return err
    with get_session(db_name) as session:
        acct = session.get(Account, account_id)
        if not acct:
            return jsonify({"error": "account not found"}), 404
        session.delete(acct)
    return jsonify({"message": "deleted"})


# ------------------------------------------------------------------
# Transactions
# ------------------------------------------------------------------


@bp.route("/databases/<db_name>/transactions", methods=["GET"])
def list_transactions(db_name: str):
    err = _ensure_db(db_name)
    if err:
        return err
    with get_session(db_name) as session:
        rows = session.query(Transaction).order_by(Transaction.id).all()
        return jsonify(
            [TransactionOut.model_validate(r).model_dump(mode="json") for r in rows]
        )


@bp.route("/databases/<db_name>/transactions", methods=["POST"])
def create_transaction(db_name: str):
    err = _ensure_db(db_name)
    if err:
        return err
    body = TransactionCreate.model_validate(request.get_json())

    if body.amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    with get_session(db_name) as session:
        if body.from_account_id is not None:
            src = session.get(Account, body.from_account_id)
            if not src:
                return jsonify({"error": "from_account not found"}), 404
            if src.balance < body.amount:
                return jsonify({"error": "insufficient funds"}), 400
            src.balance -= body.amount
            src.updated_at = datetime.now(timezone.utc)

        if body.to_account_id is not None:
            dst = session.get(Account, body.to_account_id)
            if not dst:
                return jsonify({"error": "to_account not found"}), 404
            dst.balance += body.amount
            dst.updated_at = datetime.now(timezone.utc)

        txn = Transaction(
            from_account_id=body.from_account_id,
            to_account_id=body.to_account_id,
            amount=body.amount,
            description=body.description,
        )
        session.add(txn)
        session.flush()
        out = TransactionOut.model_validate(txn).model_dump(mode="json")
    return jsonify(out), 201
