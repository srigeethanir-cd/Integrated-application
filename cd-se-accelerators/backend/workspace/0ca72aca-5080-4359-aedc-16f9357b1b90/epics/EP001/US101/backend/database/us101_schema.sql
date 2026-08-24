python
# models.py
from pydantic import BaseModel
from typing import Optional

class Product(BaseModel):
    id: Optional[int]
    name: str
    sku: str
    description: Optional[str]

class ProductCreate(BaseModel):
    name: str
    sku: str
    description: Optional[str]