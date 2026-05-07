from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    query: str = Field(
        description="검색할 자연어 질의문",
        examples=["FastAPI 비동기 처리 방법"],
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"query": "FastAPI 비동기 처리 방법"}}
    )


class SearchResponse(BaseModel):
    embedding: list[float] = Field(description="자연어 질의 기반 임베딩 벡터 결과값")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"embedding": [0.023, -0.341, 0.756, 0.112, -0.289]}
        }
    )
