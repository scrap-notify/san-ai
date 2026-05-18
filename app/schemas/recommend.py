from pydantic import BaseModel, ConfigDict, Field


class GitHubStarsRecommendRequest(BaseModel):
    github_username: str = Field(
        default="",
        description="추천에 사용할 GitHub 사용자명",
        examples=["octocat"],
    )
    limit: int = Field(
        default=5,
        description="추천 결과 최대 반환 개수. 기본값 5, 허용 범위 1~10",
        examples=[5],
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"github_username": "octocat", "limit": 5}}
    )


class RecommendationItem(BaseModel):
    input_type: str = Field(default="url", description='항상 "url"')
    content: str = Field(description="추천 외부 글 URL")


class GitHubStarsRecommendResponse(BaseModel):
    recommendations: list[RecommendationItem] = Field(
        description="POST /ai/analyze 요청 Body로 바로 사용할 수 있는 추천 URL 목록",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recommendations": [
                    {
                        "input_type": "url",
                        "content": "https://react.dev/learn/managing-state",
                    },
                    {
                        "input_type": "url",
                        "content": "https://docs.github.com/en/actions",
                    },
                ]
            }
        }
    )
