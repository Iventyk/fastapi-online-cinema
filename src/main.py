from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from src.databases.dev_engine import AsyncSessionLocal
from src.databases.populate import seed_groups
from src.routers import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with AsyncSessionLocal() as session:
        await seed_groups(session)
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(api_v1_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": exc.errors()}),
    )
