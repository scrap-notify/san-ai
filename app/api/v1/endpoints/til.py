from typing import Annotated

from fastapi import APIRouter, Body

from app.schemas.til import TilRequest, TilResponse
from app.services.til import generate_til

router = APIRouter(tags=["til"])

_ERROR_RESPONSES = {
    400: {
        "description": "입력값 검증 실패 (`missing_contents` | `invalid_input_type`)",
        "content": {
            "application/json": {
                "examples": {
                    "missing_contents": {
                        "summary": "contents 배열 비어있음",
                        "value": {"error": "missing_contents", "message": "contents 배열이 비어있습니다."},
                    },
                    "invalid_input_type": {
                        "summary": "input_type 값 오류",
                        "value": {"error": "invalid_input_type", "message": "input_type은 url, text, image 중 하나여야 합니다."},
                    },
                }
            }
        },
    },
    422: {
        "description": "AI 처리 실패 (`til_generation_failed` | `embedding_failed`)",
        "content": {
            "application/json": {
                "examples": {
                    "til_generation_failed": {
                        "summary": "TIL 마크다운 생성 실패",
                        "value": {"error": "til_generation_failed", "message": "TIL 마크다운 생성 중 오류가 발생했습니다."},
                    },
                    "embedding_failed": {
                        "summary": "임베딩 생성 실패",
                        "value": {"error": "embedding_failed", "message": "임베딩 벡터 생성 중 오류가 발생했습니다."},
                    },
                }
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


@router.post(
    "/til",
    summary="TIL 생성 / 카드 상세 문서화",
    description=(
        "학습 카드 콘텐츠를 받아 마크다운 문서와 임베딩을 반환합니다.\n\n"
        "**`contents` 개수에 따른 동작 차이**\n"
        "- `contents` 1개: 원문 내용을 그대로 구조화한 마크다운 반환 (카드 상세보기용)\n"
        "- `contents` 2개 이상: 여러 원문을 주제별로 재구성한 마크다운 반환 (TIL 생성용)\n\n"
        "**`generate_til` 플래그**\n"
        "- `true`: 마크다운 문서를 생성해 `til_markdown` 필드에 반환합니다.\n"
        "- `false`: 마크다운 생성 없이 임베딩만 반환합니다. `til_markdown`은 `null`입니다.\n\n"
        "`embedding`은 카드별 개별 벡터가 아닌, 전체 contents를 통합한 벡터 1개입니다."
    ),
    response_model=TilResponse,
    responses=_ERROR_RESPONSES,
)
async def til(
    request: Annotated[
        TilRequest,
        Body(
            openapi_examples={
                "single_content": {
                    "summary": "단일 콘텐츠 문서화 (카드 상세보기용)",
                    "value": {
                        "contents": [
                            {"input_type": "url", "content": "https://fastapi.tiangolo.com/tutorial/first-steps/"},
                        ],
                        "generate_til": True,
                    },
                },
                "multiple_contents": {
                    "summary": "복수 콘텐츠 TIL 생성",
                    "value": {
                        "contents": [
                            {"input_type": "url", "content": "https://react.dev/learn/managing-state"},
                            {"input_type": "text", "content": "클로저는 함수가 선언될 당시의 외부 변수를 기억하는 개념이다."},
                            {"input_type": "image", "content": "https://s3.amazonaws.com/bucket/capture.png"},
                        ],
                        "generate_til": True,
                    },
                },
                "generate_til_false": {
                    "summary": "임베딩만 반환 (마크다운 없음)",
                    "value": {
                        "contents": [
                            {"input_type": "url", "content": "https://react.dev/learn/managing-state"},
                        ],
                        "generate_til": False,
                    },
                },
            }
        ),
    ],
) -> TilResponse:
    return await generate_til(request)
