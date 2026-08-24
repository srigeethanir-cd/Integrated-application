from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

app = FastAPI()

class Product(BaseModel):
    id: Optional[UUID]
    name: str
    sku: str

products = {}

@app.post("/products/")
async def create_product(product: Product):
    if not product.name:
        raise HTTPException(status_code=400, detail="Product name is mandatory.")
    if product.sku in [p.sku for p in products.values()]:
        raise HTTPException(status_code=400, detail="SKU must be unique.")
    product_id = UUID(len(products) + 1)
    products[product_id] = product
    return {"id": product_id, "message": "Product is saved successfully."}