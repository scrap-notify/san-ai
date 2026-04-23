import uvicorn
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="SAN AI Server")
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(api_router)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
