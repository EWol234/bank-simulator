"""Routes for accounts and transactions within a specific database.

All routes are scoped under /databases/<db_name>/... so the database
file to operate on is always explicit in the URL.
"""

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app.models import Account, Transaction
from app.schemas import (
    AccountCreate,
    AccountOut,
    AccountUpdate,
    TransactionCreate,
    TransactionOut,
)

bp = Blueprint("accounts", __name__, url_prefix="/databases/<db_name>")


def _db_manager():
    return current_app.config["DB_MANAGER"]


def _ensure_db(db_name: str):
    mgr = _db_manager()
    if not mgr.database_exists(db_name):
        return None, (jsonify({"error": f"Database '{db_name}' not found"}), 404)
    return mgr, None


# ------------------------------------------------------------------
# Accounts
# ------------------------------------------------------------------


@bp.route("/accounts", methods=["GET"])
def list_accounts(db_name: str):
    mgr, err = _ensure_db(db_name)
    if err:
        return err
    with mgr.session_scope(db_name) as session:
        rows = session.query(Account).order_by(Account.id).all()
        return jsonify([AccountOut.model_validate(r).model_dump(mode="json") for r in rows])


@bp.route("/accounts", methods=["POST"])
def create_account(db_name: str):
    mgr, err = _ensure_db(db_name)
    if err:
        return err
    body = AccountCreate.model_validate(request.get_json())
    with mgr.session_scope(db_name) as session:
        acct = Account(name=body.name, balance=body.balance)
        session.add(acct)
        session.flush()
        out = AccountOut.model_validate(acct).model_dump(mode="json")
    return jsonify(out), 201


@bp.route("/accounts/<int:account_id>", methods=["GET"])
def get_account(db_name: str, account_id: int):
    mgr, err = _ensure_db(db_name)
    if err:
        return err
    with mgr.session_scope(db_name) as session:
        acct = session.get(Account, account_id)
        if not acct:
            return jsonify({"error": "account not found"}), 404
        return jsonify(AccountOut.model_validate(acct).model_dump(mode="json"))


@bp.route("/accounts/<int:account_id>", methods=["PATCH"])
def update_account(db_name: str, account_id: int):
    mgr, err = _ensure_db(db_name)
    if err:
        return err
    body = AccountUpdate.model_validate(request.get_json())
    with mgr.session_scope(db_name) as session:
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


@bp.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(db_name: str, account_id: int):
    mgr, err = _ensure_db(db_name)
    if err:
        return err
    with mgr.session_scope(db_name) as session:
        acct = session.get(Account, account_id)
        if not acct:
            return jsonify({"error": "account not found"}), 404
        session.delete(acct)
    return jsonify({"message": "deleted"})


# ------------------------------------------------------------------
# Transactions
# ------------------------------------------------------------------


@bp.route("/transactions", methods=["GET"])
def list_transactions(db_name: str):
    mgr, err = _ensure_db(db_name)
    if err:
        return err
    with mgr.session_scope(db_name) as session:
        rows = session.query(Transaction).order_by(Transaction.id).all()
        return jsonify(
            [TransactionOut.model_validate(r).model_dump(mode="json") for r in rows]
        )


@bp.route("/transactions", methods=["POST"])
def create_transaction(db_name: str):
    mgr, err = _ensure_db(db_name)
    if err:
        return err
    body = TransactionCreate.model_validate(request.get_json())

    if body.amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    with mgr.session_scope(db_name) as session:
        # Validate referenced accounts exist
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
