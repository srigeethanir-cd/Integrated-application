from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class AccountCreate(BaseModel):
    owner: str = Field(min_length=2, max_length=100)
    opening_balance: Decimal = Field(default=0, ge=0)

class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner: str
    balance: Decimal

class TransferRequest(BaseModel):
    source_account_id: int = Field(gt=0)
    destination_account_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, le=1_000_000)
