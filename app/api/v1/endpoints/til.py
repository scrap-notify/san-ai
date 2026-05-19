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
    summary="TIL 생성",
    description=(
        "여러 카드 콘텐츠를 받아 오늘 배운 내용을 요약/정리한 TIL 마크다운 문서와 임베딩을 반환합니다.\n\n"
        "각 카드를 개별 요약(병렬)한 뒤, 맥락을 파악해 주제별로 묶은 TIL 문서를 생성합니다.\n\n"
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
                "til_generate_url": {
                    "summary": "TIL 생성 (URL 3개)",
                    "value": {
                        "contents": [
                            {"input_type": "url", "content": "https://fastapi.tiangolo.com/async/"},
                            {"input_type": "url", "content": "https://javascript.info/closure"},
                            {"input_type": "url", "content": "https://web.dev/articles/promises"},
                        ],
                        "generate_til": True,
                    },
                },
                "til_generate_text": {
                    "summary": "TIL 생성 (텍스트 3개)",
                    "value": {
                        "contents": [
                            {"input_type": "text", "content": "클로저(Closure)는 함수가 선언될 당시의 외부 스코프 변수를 기억하고 접근할 수 있는 특성이다. 내부 함수가 외부 함수의 실행이 끝난 뒤에도 외부 변수를 참조할 수 있으며, 이를 통해 상태를 캡슐화하거나 팩토리 함수를 만드는 데 활용된다."},
                            {"input_type": "text", "content": "Docker 컨테이너는 애플리케이션과 실행 환경을 하나의 단위로 패키징한 것이다. 호스트 OS 커널을 공유하되 프로세스, 파일시스템, 네트워크를 격리해 가볍고 빠르게 실행된다. 이미지는 컨테이너의 읽기 전용 템플릿이며 컨테이너는 이미지 위에 쓰기 레이어를 추가한 실행 인스턴스다."},
                            {"input_type": "text", "content": "의존성 주입(DI)은 객체가 필요로 하는 의존성을 내부에서 직접 생성하지 않고 외부에서 주입받는 설계 패턴이다. 결합도를 낮추고 테스트 가능성을 높이며, 생성자 주입, 세터 주입, 인터페이스 주입 세 가지 방식이 있다. FastAPI의 Depends()가 대표적인 프레임워크 수준의 DI 구현 예시다."},
                        ],
                        "generate_til": True,
                    },
                },
                "embedding_only": {
                    "summary": "임베딩만 반환 (마크다운 없음)",
                    "value": {
                        "contents": [
                            {"input_type": "url", "content": "https://fastapi.tiangolo.com/async/"},
                            {"input_type": "url", "content": "https://javascript.info/closure"},
                            {"input_type": "url", "content": "https://web.dev/articles/promises"},
                        ],
                        "generate_til": False,
                    },
                },
            }
        ),
    ],
) -> TilResponse:
    return await generate_til(request)
