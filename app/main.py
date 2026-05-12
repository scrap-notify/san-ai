import uvicorn
from fastapi import FastAPI

from app.api.endpoints.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    tags_metadata = [
        {
            "name": "analyze",
            "description": "스크랩 원본 데이터를 해석해 지식카드 저장에 필요한 메타데이터를 일괄 생성한다.",
        },
        {
            "name": "til",
            "description": "오늘 저장한 지식 카드 원문들을 GitHub 업로드용 마크다운 문서로 정리한다. 리콜 TIL 페이지에서 활용한다.",
        },
        {
            "name": "search",
            "description": "사용자의 자연어 질의를 임베딩 벡터로 변환한다. 벡터 DB 조회는 백엔드가 담당한다.",
        },
        {
            "name": "quiz",
            "description": "스크랩된 콘텐츠를 기반으로 단답형·O/X 퀴즈를 생성한다.",
        },
        {
            "name": "health",
            "description": "서버 상태 확인",
        },
    ]

    app = FastAPI(
        title="SAN AI Server",
        description="학습 카드 콘텐츠를 분석·요약·검색·퀴즈 생성하는 AI 서버. 백엔드는 `/ai/analyze`, `/ai/til`, `/ai/search`, `/ai/quiz` 엔드포인트를 사용한다.",
        version="1.0.0",
        openapi_tags=tags_metadata,
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router, prefix="/ai")

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
