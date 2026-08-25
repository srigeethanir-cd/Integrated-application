from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Account, Transaction
from schemas import AccountCreate, TransferRequest

class InsufficientFundsError(Exception):
    pass

def create_account(db: Session, payload: AccountCreate) -> Account:
    account = Account(owner=payload.owner, balance=payload.opening_balance)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

def transfer(db: Session, payload: TransferRequest) -> Account:
    try:
        source = db.get(Account, payload.source_account_id)
        destination = db.get(Account, payload.destination_account_id)
        if source is None or destination is None:
            raise LookupError("account not found")
        if source.id == destination.id:
            raise ValueError("accounts must differ")
        if Decimal(source.balance) < payload.amount:
            raise InsufficientFundsError("insufficient funds")
        source.balance -= payload.amount
        destination.balance += payload.amount
        db.add_all([
            Transaction(account=source, kind="debit", amount=payload.amount),
            Transaction(account=destination, kind="credit", amount=payload.amount),
        ])
        db.commit()
        db.refresh(source)
        return source
    except Exception:
        db.rollback()
        raise

def list_accounts(db: Session) -> list[Account]:
    return list(db.scalars(select(Account).order_by(Account.id)))
