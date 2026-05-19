from fastapi import APIRouter

from app.api.v1.endpoints.analyze import router as analyze_router
from app.api.v1.endpoints.card import router as card_router
from app.api.v1.endpoints.quiz import router as quiz_router
from app.api.v1.endpoints.recommend import router as recommend_router
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.til import router as til_router

api_router = APIRouter()
api_router.include_router(analyze_router)
api_router.include_router(search_router)
api_router.include_router(til_router)
api_router.include_router(card_router)
api_router.include_router(quiz_router)
api_router.include_router(recommend_router)
