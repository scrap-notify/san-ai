from fastapi import APIRouter

from app.schemas.recommend import GitHubStarsRecommendRequest, GitHubStarsRecommendResponse
from app.services.recommend import recommend_github_stars

router = APIRouter(prefix="/recommend", tags=["recommend"])

_RESPONSES = {
    400: {
        "description": "입력값 검증 실패 (`missing_github_username` | `invalid_limit`)",
        "content": {
            "application/json": {
                "examples": {
                    "missing_github_username": {
                        "summary": "GitHub 사용자명 누락",
                        "value": {
                            "error": "missing_github_username",
                            "message": "github_username 필드는 비어있을 수 없습니다.",
                        },
                    },
                    "invalid_limit": {
                        "summary": "limit 범위 오류",
                        "value": {
                            "error": "invalid_limit",
                            "message": "limit은 1 이상 10 이하의 정수여야 합니다.",
                        },
                    },
                }
            }
        },
    },
    404: {
        "description": "GitHub 사용자 없음",
        "content": {
            "application/json": {
                "example": {
                    "error": "github_user_not_found",
                    "message": "GitHub 사용자를 찾을 수 없습니다.",
                }
            }
        },
    },
    422: {
        "description": "외부 API 또는 추천 처리 실패",
        "content": {
            "application/json": {
                "examples": {
                    "github_fetch_failed": {
                        "summary": "GitHub Star 목록 조회 실패",
                        "value": {
                            "error": "github_fetch_failed",
                            "message": "GitHub Star 목록 조회 실패",
                        },
                    },
                    "search_failed": {
                        "summary": "Tavily 검색 실패",
                        "value": {
                            "error": "search_failed",
                            "message": "Tavily 검색 처리 실패",
                        },
                    },
                    "recommendation_failed": {
                        "summary": "추천 결과 생성 실패",
                        "value": {
                            "error": "recommendation_failed",
                            "message": "추천 결과 생성에 실패했습니다.",
                        },
                    },
                }
            }
        },
    },
}


@router.post(
    "/github-stars",
    summary="GitHub Star 기반 cold-start 글 추천",
    description=(
        "GitHub 사용자의 공개 Star 목록을 기반으로 신규 사용자가 스크랩할 만한 외부 글 URL을 추천합니다.\n\n"
        "GitHub API는 공개 API를 사용하며, 서버에 `GITHUB_API_TOKEN`이 설정된 경우에만 토큰을 함께 전송합니다. "
        "추천 결과는 `/ai/analyze` 요청 Body로 바로 사용할 수 있는 `input_type=url`, `content=<URL>` 구조입니다."
    ),
    response_model=GitHubStarsRecommendResponse,
    responses=_RESPONSES,
)
async def recommend_github_stars_endpoint(
    request: GitHubStarsRecommendRequest,
) -> GitHubStarsRecommendResponse:
    return await recommend_github_stars(request)
