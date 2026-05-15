from typing import Annotated

from fastapi import APIRouter, Body

from app.schemas.quiz import QuizRequest, QuizResponse
from app.services.quiz import generate_quiz

router = APIRouter(tags=["quiz"])

_RESPONSES = {
    200: {
        "description": "퀴즈 생성 성공",
        "content": {
            "application/json": {
                "examples": {
                    "short_answer": {
                        "summary": "단답형 응답",
                        "value": {
                            "quiz_type": "short_answer",
                            "questions": [
                                {"question": "FastAPI가 타입 검증에 활용하는 라이브러리는?", "answer": "Pydantic", "explanation": "FastAPI는 Pydantic 모델을 통해 요청/응답 데이터의 타입을 자동으로 검증한다."},
                                {"question": "FastAPI 애플리케이션을 구동하는 ASGI 서버는?", "answer": "uvicorn", "explanation": "uvicorn은 비동기 요청을 처리하는 ASGI 서버로 FastAPI와 함께 사용된다."},
                            ],
                        },
                    },
                    "ox": {
                        "summary": "O/X 퀴즈 응답",
                        "value": {
                            "quiz_type": "ox",
                            "questions": [
                                {"statement": "FastAPI는 Pydantic으로 타입 검증을 한다.", "is_correct": True, "explanation": "FastAPI는 Pydantic 모델을 통해 타입을 검증한다."},
                                {"statement": "uvicorn은 WSGI 서버다.", "is_correct": False, "explanation": "uvicorn은 ASGI 서버다."},
                            ],
                        },
                    },
                }
            }
        },
    },
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
        "- `ox`: O/X 퀴즈. 참/거짓을 판단하는 형식입니다.\n\n"
        "질문·정답·해설은 입력 콘텐츠의 언어(한국어/영어 등)를 그대로 따릅니다."
    ),
    response_model=QuizResponse,
    responses=_RESPONSES,
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
                            {"input_type": "text", "content": "Docker는 애플리케이션을 컨테이너로 패키징해 어디서든 동일하게 실행할 수 있게 해주는 플랫폼이다."},
                            {"input_type": "text", "content": "Kubernetes는 컨테이너화된 애플리케이션의 배포, 확장, 관리를 자동화하는 오픈소스 오케스트레이션 시스템이다."},
                            {"input_type": "text", "content": "React는 Meta가 만든 UI 라이브러리로, 컴포넌트 기반으로 인터페이스를 구성하며 가상 DOM을 활용해 렌더링 성능을 최적화한다."},
                            {"input_type": "text", "content": "클로저는 함수가 선언될 당시의 외부 스코프 변수를 기억하고 참조할 수 있는 JavaScript의 특성이다."},
                            {"input_type": "text", "content": "Git은 분산 버전 관리 시스템으로, 코드의 변경 이력을 추적하고 여러 개발자가 협업할 수 있게 해준다."},
                            {"input_type": "text", "content": "의존성 주입(DI)은 객체가 필요로 하는 의존성을 직접 생성하지 않고 외부에서 주입받는 설계 패턴이다."},
                            {"input_type": "text", "content": "클린 아키텍처는 소프트웨어를 계층으로 나눠 의존성이 항상 안쪽을 향하도록 설계하는 아키텍처 원칙이다."},
                        ],
                        "quiz_type": "short_answer",
                    },
                },
                "short_answer_url": {
                    "summary": "단답형 — URL 콘텐츠",
                    "value": {
                        "contents": [
                            {"input_type": "url", "content": "https://fastapi.tiangolo.com/tutorial/first-steps/"},
                            {"input_type": "url", "content": "https://docs.python.org/3/tutorial/classes.html"},
                            {"input_type": "url", "content": "https://martinfowler.com/articles/injection.html"},
                            {"input_type": "url", "content": "https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html"},
                            {"input_type": "url", "content": "https://www.baeldung.com/solid-principles"},
                            {"input_type": "url", "content": "https://docs.docker.com/get-started/overview/"},
                            {"input_type": "url", "content": "https://react.dev/learn"},
                            {"input_type": "url", "content": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Closures"},
                            {"input_type": "url", "content": "https://kubernetes.io/docs/concepts/overview/"},
                            {"input_type": "url", "content": "https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F"},
                        ],
                        "quiz_type": "short_answer",
                    },
                },
                "ox_text": {
                    "summary": "O/X 퀴즈 — 텍스트 콘텐츠",
                    "value": {
                        "contents": [
                            {"input_type": "text", "content": "FastAPI는 Python 기반 비동기 웹 프레임워크로, Pydantic을 활용한 타입 검증을 지원한다."},
                            {"input_type": "text", "content": "uvicorn은 ASGI 서버로, FastAPI 애플리케이션을 구동하는 데 사용된다."},
                            {"input_type": "text", "content": "Starlette은 FastAPI의 기반 프레임워크로, 라우팅과 미들웨어를 제공한다."},
                            {"input_type": "text", "content": "Docker는 애플리케이션을 컨테이너로 패키징해 어디서든 동일하게 실행할 수 있게 해주는 플랫폼이다."},
                            {"input_type": "text", "content": "Kubernetes는 컨테이너화된 애플리케이션의 배포, 확장, 관리를 자동화하는 오픈소스 오케스트레이션 시스템이다."},
                            {"input_type": "text", "content": "React는 Meta가 만든 UI 라이브러리로, 컴포넌트 기반으로 인터페이스를 구성하며 가상 DOM을 활용해 렌더링 성능을 최적화한다."},
                            {"input_type": "text", "content": "클로저는 함수가 선언될 당시의 외부 스코프 변수를 기억하고 참조할 수 있는 JavaScript의 특성이다."},
                            {"input_type": "text", "content": "Git은 분산 버전 관리 시스템으로, 코드의 변경 이력을 추적하고 여러 개발자가 협업할 수 있게 해준다."},
                            {"input_type": "text", "content": "의존성 주입(DI)은 객체가 필요로 하는 의존성을 직접 생성하지 않고 외부에서 주입받는 설계 패턴이다."},
                            {"input_type": "text", "content": "클린 아키텍처는 소프트웨어를 계층으로 나눠 의존성이 항상 안쪽을 향하도록 설계하는 아키텍처 원칙이다."},
                        ],
                        "quiz_type": "ox",
                    },
                },
                "ox_url": {
                    "summary": "O/X 퀴즈 — URL 콘텐츠",
                    "value": {
                        "contents": [
                            {"input_type": "url", "content": "https://fastapi.tiangolo.com/tutorial/first-steps/"},
                            {"input_type": "url", "content": "https://docs.python.org/3/tutorial/classes.html"},
                            {"input_type": "url", "content": "https://martinfowler.com/articles/injection.html"},
                            {"input_type": "url", "content": "https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html"},
                            {"input_type": "url", "content": "https://www.baeldung.com/solid-principles"},
                            {"input_type": "url", "content": "https://docs.docker.com/get-started/overview/"},
                            {"input_type": "url", "content": "https://react.dev/learn"},
                            {"input_type": "url", "content": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Closures"},
                            {"input_type": "url", "content": "https://kubernetes.io/docs/concepts/overview/"},
                            {"input_type": "url", "content": "https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F"},
                        ],
                        "quiz_type": "ox",
                    },
                },
            }
        ),
    ],
) -> QuizResponse:
    return await generate_quiz(request)
