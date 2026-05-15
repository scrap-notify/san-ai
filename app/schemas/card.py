from pydantic import BaseModel, ConfigDict, Field

from app.schemas.til import TilContent


class CardRequest(BaseModel):
    content: TilContent = Field(description="카드 콘텐츠. url | text | image 중 하나")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"content": {"input_type": "url", "content": "https://example.com/article"}},
            ]
        }
    )


class CardResponse(BaseModel):
    title: str = Field(
        description="원문 내용을 대표하는 한 줄 제목",
        examples=["FastAPI 비동기 처리와 의존성 주입"],
    )
    card_markdown: str = Field(
        description="원문을 구조화한 마크다운 문서",
        examples=["## 비동기 처리\n\nFastAPI는 async/await를 기반으로 ..."],
    )
    embedding: list[float] = Field(
        description="카드 콘텐츠 임베딩 벡터",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "FastAPI 비동기 처리와 의존성 주입",
                "card_markdown": "## 비동기 처리\n\nFastAPI는 async/await를 기반으로 ...",
                "embedding": [0.012, -0.453, 0.891],
            }
        }
    )
