from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import AccountCreate, AccountOut, TransferRequest
from services.banking import InsufficientFundsError, create_account, list_accounts, transfer

router = APIRouter(prefix="/banking", tags=["banking"])

def authenticate(x_api_key: str = Header()) -> str:
    if x_api_key != "validation-bank-key":
        raise HTTPException(status_code=401, detail="invalid API key")
    return x_api_key

@router.post("/accounts", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def open_account(payload: AccountCreate, db: Session = Depends(get_db), _: str = Depends(authenticate)):
    return create_account(db, payload)

@router.get("/accounts", response_model=list[AccountOut])
def accounts(db: Session = Depends(get_db), _: str = Depends(authenticate)):
    return list_accounts(db)

@router.post("/transfers", response_model=AccountOut)
def make_transfer(payload: TransferRequest, db: Session = Depends(get_db), _: str = Depends(authenticate)):
    try:
        return transfer(db, payload)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (ValueError, InsufficientFundsError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
