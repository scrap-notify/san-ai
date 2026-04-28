from fastapi import APIRouter

from app.schemas.til import TilRequest, TilResponse
from app.services.til import generate_til

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/til", response_model=TilResponse)
async def create_til(request: TilRequest) -> TilResponse:
    return await generate_til(request)
