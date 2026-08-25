from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from database import Base, engine
from routers.jobs import router
from services.jobs import DependencyUnavailableError
Base.metadata.create_all(engine)
app = FastAPI(title="Exception Validation API")
@app.exception_handler(DependencyUnavailableError)
async def dependency_error(_: Request, error: DependencyUnavailableError):
    return JSONResponse(status_code=503, content={"detail": str(error)})
app.include_router(router, prefix="/api")
