import os
import logging
import secrets
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any

from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.responses import JSONResponse, HTMLResponse

from src.config.limiter import limiter
from src.databases import Base
from src.databases.dev_engine import AsyncSessionLocal, engine
from src.databases.populate import seed_groups
from src.routers import api_v1_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

security = HTTPBasic()


def check_docs_permissions(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """
    Checking login and password to enter documentation.
    """
    DOCS_USERNAME = os.getenv("DOCS_LOGIN", "admin")
    DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "password")

    correct_username = secrets.compare_digest(
        credentials.username, DOCS_USERNAME
    )
    correct_password = secrets.compare_digest(
        credentials.password, DOCS_PASSWORD
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_groups(session)
    yield


app = FastAPI(
    lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None
)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded, _rate_limit_exceeded_handler  # type: ignore[arg-type]
)

app.include_router(api_v1_router)


@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(
    username: str = Depends(check_docs_permissions),
) -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/openapi.json", title="Online Cinema API Docs"
    )


@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(
    username: str = Depends(check_docs_permissions),
) -> dict[str, Any]:
    return get_openapi(
        title="FastAPI Online Cinema",
        version="1.0.0",
        description="API documentation protected by Basic Auth",
        routes=app.routes,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": exc.errors()}),
    )
