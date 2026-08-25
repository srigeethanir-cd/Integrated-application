from fastapi import FastAPI
from database import Base, engine
from routers.accounts import router

Base.metadata.create_all(engine)
app = FastAPI(title="Banking Validation API")
app.include_router(router, prefix="/api")
