from typing import Annotated

from fastapi import APIRouter, Body

from app.schemas.quiz import QuizRequest, QuizResponse
from app.services.quiz import generate_quiz

router = APIRouter(tags=["quiz"])

_ERROR_RESPONSES = {
    400: {
        "description": "입력값 검증 실패 (`missing_contents` | `invalid_input_type`)",
        "content": {
            "application/json": {
                "examples": {
                    "missing_contents": {
                        "summary": "contents 배열 비어있음",
                        "value": {"error": "missing_contents", "message": "contents는 비어있을 수 없습니다."},
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
        "description": "AI 처리 실패 (`quiz_generation_failed`)",
        "content": {
            "application/json": {
                "example": {"error": "quiz_generation_failed", "message": "퀴즈 생성 중 오류가 발생했습니다."},
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
    "/quiz",
    summary="퀴즈 생성",
    description=(
        "스크랩된 콘텐츠를 받아 퀴즈 문제를 생성합니다.\n\n"
        "**문제 수 결정**\n"
        "- 별도로 지정하지 않으며, 콘텐츠 1개당 문제 1개가 자동으로 생성됩니다.\n\n"
        "**퀴즈 유형 (`quiz_type`)**\n"
        "- `short_answer`: 단답형. 1~3 단어 혹은 짧은 구로 답하는 형식입니다.\n"
        "- `ox`: O/X 퀴즈. 참/거짓을 판단하는 형식입니다. (추후 지원)\n\n"
        "질문·정답·해설은 입력 콘텐츠의 언어(한국어/영어 등)를 그대로 따릅니다."
    ),
    response_model=QuizResponse,
    responses=_ERROR_RESPONSES,
)
async def quiz(
    request: Annotated[
        QuizRequest,
        Body(
            openapi_examples={
                "short_answer_text": {
                    "summary": "단답형 — 텍스트 콘텐츠",
                    "value": {
                        "contents": [
                            {"input_type": "text", "content": "FastAPI는 Python 기반 비동기 웹 프레임워크로, Pydantic을 활용한 타입 검증을 지원한다."},
                            {"input_type": "text", "content": "uvicorn은 ASGI 서버로, FastAPI 애플리케이션을 구동하는 데 사용된다."},
                            {"input_type": "text", "content": "Starlette은 FastAPI의 기반 프레임워크로, 라우팅과 미들웨어를 제공한다."},
                        ],
                        "quiz_type": "short_answer",
                    },
                },
                "short_answer_url": {
                    "summary": "단답형 — URL 콘텐츠",
                    "value": {
                        "contents": [
                            {"input_type": "url", "content": "https://fastapi.tiangolo.com/tutorial/first-steps/"},
                        ],
                        "quiz_type": "short_answer",
                    },
                },
            }
        ),
    ],
) -> QuizResponse:
    return await generate_quiz(request)
