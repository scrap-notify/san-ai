from fastapi import APIRouter

from app.core.exceptions import ContentValidationError
from app.llms.embeddings import EmbeddingClient
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


# /search 엔드포인트는 자연어 질의를 임베딩 벡터로 변환해 반환한다. 벡터 DB 조회는 백엔드가 담당한다.
@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    query = request.query.strip()
    if not query:
        raise ContentValidationError(code="missing_query", message="query 필드는 비어있을 수 없습니다.")

    embedding = EmbeddingClient().embed(query)
    return SearchResponse(embedding=embedding)
