from enum import StrEnum

from pydantic import BaseModel


# StrEnum을 사용해 JSON 직렬화 시 "InputType.url"이 아닌 "url" 문자열로 출력되게 한다.
class InputType(StrEnum):
    url = "url"
    text = "text"
    image = "image"


class ErrorResponse(BaseModel):
    # API 클라이언트가 에러 종류를 코드로 분기 처리할 수 있도록 문자열 코드를 포함한다.
    error: str
    message: str
