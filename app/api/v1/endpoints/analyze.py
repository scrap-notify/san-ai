from typing import Annotated

from fastapi import APIRouter, Body

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import analyze as analyze_service

router = APIRouter(tags=["analyze"])

_ERROR_RESPONSES = {
    400: {
        "description": "입력값 검증 실패 (`missing_content` | `invalid_input_type`)",
        "content": {
            "application/json": {
                "examples": {
                    "missing_content": {
                        "summary": "content 필드 누락",
                        "value": {"error": "missing_content", "message": "content 필드가 비어있습니다."},
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
        "description": "AI 처리 실패 (`analyze_failed` | `embedding_failed`)",
        "content": {
            "application/json": {
                "examples": {
                    "analyze_failed": {
                        "summary": "LLM 분석 실패",
                        "value": {"error": "analyze_failed", "message": "LLM 분석 중 오류가 발생했습니다."},
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
    "/analyze",
    summary="스크랩 AI 분석",
    description=(
        "URL·텍스트·이미지를 입력받아 제목, 요약, 태그, 카테고리, 임베딩을 반환합니다.\n\n"
        "- `input_type=url`: 웹 페이지를 크롤링해 본문을 추출합니다.\n"
        "- `input_type=text`: 전달된 텍스트를 그대로 분석합니다.\n"
        "- `input_type=image`: 이미지 URL에서 내용을 추출한 뒤 분석합니다."
    ),
    response_model=AnalyzeResponse,
    responses=_ERROR_RESPONSES,
)
async def analyze(
    request: Annotated[
        AnalyzeRequest,
        Body(
            openapi_examples={
                "url": {
                    "summary": "URL 입력",
                    "value": {"input_type": "url", "content": "https://react.dev/learn/managing-state"},
                },
                "text": {
                    "summary": "텍스트 입력",
                    "value": {"input_type": "text", "content": "클로저는 함수가 선언될 당시의 외부 변수를 기억하는 개념이다."},
                },
                "image": {
                    "summary": "이미지 입력",
                    "value": {"input_type": "image", "content": "https://s3.amazonaws.com/bucket/capture.png"},
                },
            }
        ),
    ],
) -> AnalyzeResponse:
    return await analyze_service(request.input_type, request.content)
