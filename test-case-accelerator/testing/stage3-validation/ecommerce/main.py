from fastapi import FastAPI
from database import Base, engine
from routers.store import router
Base.metadata.create_all(engine)
app = FastAPI(title="E-Commerce Validation API")
app.include_router(router, prefix="/api/v1")
