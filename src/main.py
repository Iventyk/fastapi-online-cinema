from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from src.config import get_settings
from src.routers.api import api_v1_router

settings = get_settings()

app = FastAPI()

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
        request: Request, exc: RequestValidationError
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {"detail": exc.errors()},
        ))
