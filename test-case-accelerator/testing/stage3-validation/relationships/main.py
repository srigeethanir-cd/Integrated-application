from fastapi import FastAPI
from database import Base, engine
from routers.library import router
Base.metadata.create_all(engine)
app = FastAPI(title="Relationships Validation API")
app.include_router(router, prefix="/api")
