from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import InputType


class AnalyzeRequest(BaseModel):
    input_type: InputType = Field(
        description="입력 콘텐츠 유형. url | text | image 중 하나",
        examples=["url"],
    )
    content: str = Field(
        description="input_type에 따라 URL 문자열, 본문 텍스트, 이미지 URL 중 하나",
        examples=["https://example.com/article"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"input_type": "url", "content": "https://example.com/article"},
                {"input_type": "text", "content": "FastAPI는 Python 비동기 웹 프레임워크입니다."},
                {"input_type": "image", "content": "https://s3.amazonaws.com/bucket/img.png"},
            ]
        }
    )


class AnalyzeResponse(BaseModel):
    title: str = Field(description="원문을 대표하는 제목 1개 (20자 이하 권장)", examples=["React 상태 관리"])
    summary: str = Field(
        description="요약 텍스트 (3문장 이내, 각 문장 27자 이하 권장)",
        examples=["상태는 화면 정보를 기억한다.\nuseState로 상태를 선언한다.\n상태 위치가 설계의 핵심이다."],
    )
    tags: list[str] = Field(description="핵심 키워드 태그 목록 (5개 이내)", examples=[["React", "상태관리", "useState", "리렌더링"]])
    category: str = Field(description="프론트엔드 | 백엔드 | AI/ML | 데이터 | 인프라/DevOps | CS | 보안 | 모바일 | 기타 중 하나", examples=["프론트엔드"])
    embedding: list[float] = Field(description="입력 데이터 기반 임베딩 벡터 결과값")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "React 상태 관리",
                "summary": "상태는 화면 정보를 기억한다.\nuseState로 상태를 선언한다.\n상태 위치가 설계의 핵심이다.",
                "tags": ["React", "상태관리", "useState", "리렌더링"],
                "category": "프론트엔드",
                "embedding": [0.012, -0.453, 0.891, 0.234, -0.102],
            }
        }
    )
