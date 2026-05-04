from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


# StrEnum을 사용해 JSON 직렬화 시 "InputType.url"이 아닌 "url" 문자열로 출력되게 한다.
class InputType(StrEnum):
    url = "url"
    text = "text"
    image = "image"


class ErrorResponse(BaseModel):
    error: str = Field(description="에러 식별 코드 (snake_case)", examples=["missing_content"])
    message: str = Field(description="사람이 읽을 수 있는 에러 설명", examples=["content 필드가 비어있습니다."])

    model_config = ConfigDict(
        json_schema_extra={"example": {"error": "missing_content", "message": "content 필드가 비어있습니다."}}
    )
