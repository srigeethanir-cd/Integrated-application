from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Order, OrderItem, Product
from schemas import Checkout, ProductCreate

def create_product(db: Session, payload: ProductCreate) -> Product:
    product = Product(**payload.model_dump())
    db.add(product); db.commit(); db.refresh(product)
    return product

def list_products(db: Session) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.name)))

def checkout(db: Session, payload: Checkout) -> Order:
    order = Order(customer_email=payload.customer_email)
    discount = Decimal("0.10") if payload.discount_code == "SAVE10" else Decimal("0")
    try:
        for item in payload.items:
            product = db.get(Product, item.product_id)
            if product is None:
                raise LookupError("product not found")
            if product.stock < item.quantity:
                raise ValueError("insufficient inventory")
            product.stock -= item.quantity
            order.items.append(OrderItem(product=product, quantity=item.quantity))
        order.status = f"confirmed:{discount}"
        db.add(order); db.commit(); db.refresh(order)
        return order
    except Exception:
        db.rollback()
        raise
