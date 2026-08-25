from fastapi import FastAPI
from database import Base, engine
from routers.auth import router
Base.metadata.create_all(engine)
app = FastAPI(title="JWT Authentication Validation API")
app.include_router(router, prefix="/api")
