from fastapi import APIRouter

from src.routers.accounts import account_router
from src.routers.movies import router as movies_router
from src.routers.genres import router as genres_router
from src.routers.stars import router as stars_router
from src.routers.directors import router as directors_router
from src.routers.payments import payment_router
from src.routers.webhooks import webhooks_router

api_v1_router = APIRouter()

api_v1_router.include_router(account_router)
api_v1_router.include_router(movies_router)
api_v1_router.include_router(genres_router)
api_v1_router.include_router(stars_router)
api_v1_router.include_router(directors_router)
api_v1_router.include_router(payment_router)
api_v1_router.include_router(webhooks_router)
