from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import Checkout, ProductCreate, ProductOut
from services.store import checkout, create_product, list_products
router = APIRouter(prefix="/store", tags=["store"])

@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def add_product(payload: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db, payload)

@router.get("/products", response_model=list[ProductOut])
def products(db: Session = Depends(get_db)):
    return list_products(db)

@router.post("/checkout", status_code=201)
def place_order(payload: Checkout, db: Session = Depends(get_db)):
    try:
        order = checkout(db, payload)
        return {"order_id": order.id, "status": order.status}
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
