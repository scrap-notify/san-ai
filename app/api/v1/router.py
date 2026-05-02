from fastapi import APIRouter

from app.api.v1.endpoints.analyze import router as analyze_router
from app.api.v1.endpoints.search import router as search_router

api_router = APIRouter()
api_router.include_router(analyze_router)
api_router.include_router(search_router)
