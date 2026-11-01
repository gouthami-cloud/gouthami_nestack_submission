

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import initialize_db
from app.routes.accounts import router as accounts_router
from app.routes.records import router as records_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist automatically on startup
    initialize_db()
    yield

app = FastAPI(
    title="Nestack Secure Records API",
    description="A multi-tenant secure records backend demonstrating authentication, RBAC, and abuse resistance.",
    lifespan=lifespan
)


from pydantic import ValidationError

@app.exception_handler(RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid or missing input"}
    )


app.include_router(accounts_router)
app.include_router(records_router)

@app.get("/")
def home():
    return {"message": "Nestack Security API is running"}

