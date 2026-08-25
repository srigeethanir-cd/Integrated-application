from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ProductCreate(BaseModel):
    sku: str = Field(min_length=3, max_length=32, pattern=r"^[A-Z0-9-]+$")
    name: str = Field(min_length=2, max_length=120)
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0)

class ProductOut(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class CartItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)

class Checkout(BaseModel):
    customer_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    items: list[CartItem] = Field(min_length=1)
    discount_code: str | None = Field(default=None, max_length=20)

    @field_validator("discount_code")
    @classmethod
    def uppercase_discount(cls, value):
        return value.upper() if value else value
