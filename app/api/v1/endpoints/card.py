from typing import Annotated

from fastapi import APIRouter, Body

from app.schemas.card import CardRequest, CardResponse
from app.services.card import generate_card_detail

router = APIRouter(tags=["card"])

_ERROR_RESPONSES = {
    400: {
        "description": "입력값 검증 실패 (`missing_content` | `invalid_input_type` | `invalid_url`)",
        "content": {
            "application/json": {
                "examples": {
                    "missing_content": {
                        "summary": "content 비어있음",
                        "value": {"error": "missing_content", "message": "content는 비어있을 수 없습니다."},
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
        "description": "AI 처리 실패 (`card_detail_failed` | `embedding_failed`)",
        "content": {
            "application/json": {
                "examples": {
                    "card_detail_failed": {
                        "summary": "카드 마크다운 생성 실패",
                        "value": {"error": "card_detail_failed", "message": "카드 마크다운 생성 중 오류가 발생했습니다."},
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
    "/card",
    summary="카드 상세 문서화",
    description=(
        "단일 카드 콘텐츠를 받아 원문을 그대로 구조화한 마크다운 문서와 임베딩을 반환합니다.\n\n"
        "요약 없이 원문 흐름을 유지하며 구조화합니다. 코드가 포함된 경우 언어 식별자가 있는 코드 펜스로 감쌉니다."
    ),
    response_model=CardResponse,
    responses=_ERROR_RESPONSES,
)
async def card(
    request: Annotated[
        CardRequest,
        Body(
            openapi_examples={
                "url_content": {
                    "summary": "URL 콘텐츠 카드 상세보기",
                    "value": {
                        "content": {"input_type": "url", "content": "https://fastapi.tiangolo.com/tutorial/first-steps/"},
                    },
                },
                "text_content": {
                    "summary": "텍스트 콘텐츠 카드 상세보기",
                    "value": {
                        "content": {"input_type": "text", "content": "클로저는 함수가 선언될 당시의 외부 변수를 기억하는 개념이다."},
                    },
                },
            }
        ),
    ],
) -> CardResponse:
    return await generate_card_detail(request)
