from pydantic import BaseModel

from app.schemas.common import InputType


class TilContent(BaseModel):
    input_type: InputType
    content: str


class TilRequest(BaseModel):
    contents: list[TilContent]
    # False이면 임베딩만 반환하고 마크다운 문서는 생성하지 않는다.
    generate_til: bool


class TilResponse(BaseModel):
    # generate_til=False이면 null을 반환한다.
    til_markdown: str | None
    # 카드별 개별 임베딩이 아닌 전체 contents를 통합한 임베딩 벡터 1개를 반환한다.
    embeddings: list[float]
