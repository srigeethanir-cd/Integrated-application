from fastapi import FastAPI
from database import Base, engine
from routers.profiles import router
Base.metadata.create_all(engine)
app = FastAPI(title="Validation Heavy API")
app.include_router(router, prefix="/api")
