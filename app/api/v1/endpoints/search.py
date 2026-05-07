from fastapi import APIRouter

from app.core.exceptions import ContentValidationError
from app.llms.embeddings import EmbeddingClient
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])

_ERROR_RESPONSES = {
    400: {
        "description": "입력값 검증 실패",
        "content": {
            "application/json": {
                "example": {"error": "missing_query", "message": "query 필드는 비어있을 수 없습니다."}
            }
        },
    },
    422: {
        "description": "AI 처리 실패",
        "content": {
            "application/json": {
                "example": {"error": "embedding_failed", "message": "임베딩 생성 중 오류가 발생했습니다."}
            }
        },
    },
    500: {
        "description": "서버 내부 오류",
        "content": {
            "application/json": {
                "example": {"error": "internal_error", "message": "예상치 못한 오류가 발생했습니다."}
            }
        },
    },
}


# /search 엔드포인트는 자연어 질의를 임베딩 벡터로 변환해 반환한다. 벡터 DB 조회는 백엔드가 담당한다.
@router.post(
    "/search",
    summary="자연어 검색 임베딩 생성",
    description=(
        "자연어 질의를 임베딩 벡터로 변환해 반환합니다.\n\n"
    ),
    response_model=SearchResponse,
    responses=_ERROR_RESPONSES,
)
async def search(request: SearchRequest) -> SearchResponse:
    query = request.query.strip()
    if not query:
        raise ContentValidationError(code="missing_query", message="query 필드는 비어있을 수 없습니다.")

    embedding = EmbeddingClient().embed(query)
    return SearchResponse(embedding=embedding)
