from pydantic import BaseModel

from app.schemas.common import InputType


class AnalyzeRequest(BaseModel):
    input_type: InputType
    # content는 input_type에 따라 URL 문자열, 텍스트 원문, S3 이미지 링크 중 하나다.
    content: str


class AnalyzeResponse(BaseModel):
    title: str
    summary: str
    tags: list[str]
    category: str
    embedding: list[float]
