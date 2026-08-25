from fastapi import FastAPI
from database import Base, engine
from routers.files import router
Base.metadata.create_all(engine)
app = FastAPI(title="File Upload Validation API")
app.include_router(router, prefix="/api")
