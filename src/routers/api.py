from fastapi import APIRouter

from src.routers.accounts import account_router

api_v1_router = APIRouter()

api_v1_router.include_router(account_router)
