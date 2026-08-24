from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Initialize FastAPI app
app = FastAPI()

# Initialize database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///inventory.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define Product model
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    sku = Column(String, unique=True, index=True)

Base.metadata.create_all(bind=engine)

# Define Product request body
class ProductRequest(BaseModel):
    name: str
    sku: str

# Define Product response
class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str

# Create product endpoint
@app.post("/products", response_model=ProductResponse)
def create_product(product_request: ProductRequest):
    db = SessionLocal()
    if not product_request.name:
        raise HTTPException(status_code=400, detail="Product name is mandatory.")
    
    existing_product = db.query(Product).filter(Product.sku == product_request.sku).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="SKU must be unique.")
    
    new_product = Product(name=product_request.name, sku=product_request.sku)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product