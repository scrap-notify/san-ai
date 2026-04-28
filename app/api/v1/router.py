from fastapi import APIRouter

from app.api.v1.endpoints import til

api_router = APIRouter()
api_router.include_router(til.router)
