from fastapi import FastAPI

from .database import Base, engine
from .routers import router

Base.metadata.create_all(bind=engine)
app = FastAPI(title="TestForge Validation Backend")
app.include_router(router)

