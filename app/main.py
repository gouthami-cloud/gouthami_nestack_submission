

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routes.accounts import router as accounts_router
from app.routes.records import router as records_router

app = FastAPI(title="Nestack Security API")


@app.exception_handler(RequestValidationError)
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

