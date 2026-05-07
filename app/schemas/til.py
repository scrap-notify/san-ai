from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import InputType


class TilContent(BaseModel):
    input_type: InputType = Field(
        description="입력 콘텐츠 유형. url | text | image 중 하나",
        examples=["url"],
    )
    content: str = Field(
        description="input_type에 따라 URL 문자열, 본문 텍스트, 이미지 URL 중 하나",
        examples=["https://example.com/article"],
    )


class TilRequest(BaseModel):
    contents: list[TilContent] = Field(
        description="TIL을 구성할 카드 목록. 1개 이상 필요",
    )
    generate_til: bool = Field(
        description="true이면 TIL 마크다운을 생성해 반환. false이면 임베딩만 반환",
        examples=[True],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "contents": [
                        {"input_type": "url", "content": "https://example.com/article"},
                        {"input_type": "text", "content": "FastAPI는 Python 비동기 웹 프레임워크입니다."},
                    ],
                    "generate_til": True,
                },
                {
                    "contents": [{"input_type": "url", "content": "https://example.com/article"}],
                    "generate_til": False,
                },
            ]
        }
    )


class TilResponse(BaseModel):
    title: str | None = Field(
        description="`generate_til=true`일 때만 반환. 생성된 TIL 문서의 제목. `false`이면 `null`",
        examples=["React 상태 관리와 클로저 정리"],
    )
    til_markdown: str | None = Field(
        description="`generate_til=true`일 때만 반환. 주제별로 구조화된 마크다운 문서. `false`이면 `null`",
        examples=["# TIL - 2025.04.24\n\n## React 상태 관리\n\nReact에서 상태는 컴포넌트가 기억해야 할 정보를 의미한다. ...\n\n## JavaScript 클로저\n\n클로저는 함수가 선언될 당시의 외부 변수를 기억하는 개념이다. ..."],
    )
    embedding: list[float] = Field(
        description="전체 contents를 통합한 임베딩 벡터 1개. 카드별 개별 임베딩이 아님",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "React 상태 관리와 클로저 정리",
                "til_markdown": "# TIL - 2025.04.24\n\n## React 상태 관리\n\nReact에서 상태는 컴포넌트가 기억해야 할 정보를 의미한다. ...\n\n## JavaScript 클로저\n\n클로저는 함수가 선언될 당시의 외부 변수를 기억하는 개념이다. ...",
                "embedding": [0.012, -0.453, 0.891, 0.234, -0.102],
            }
        }
    )
