from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AIProcessingError(Exception):
    """LLM 호출, 임베딩 생성 등 AI 처리 단계에서 발생하는 오류. 422로 응답한다."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message


class ContentValidationError(Exception):
    """입력값 검증 실패(빈 값, 잘못된 URL 등) 시 발생하는 오류. 400으로 응답한다."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message


def register_exception_handlers(app: FastAPI) -> None:
    # ContentValidationError는 400 상태 코드로 반환한다.
    @app.exception_handler(ContentValidationError)
    async def content_validation_exception_handler(request: Request, exc: ContentValidationError):
        return JSONResponse(
            status_code=400,
            content={"error": exc.code, "message": exc.message},
        )

    # RequestValidationError는 FastAPI의 요청 검증 실패 시 발생하는 예외로, 400 상태 코드와 함께 적절한 오류 코드를 반환한다.
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        error = exc.errors()[0]
        loc = error.get("loc", ())
        if "input_type" in loc:
            code = "invalid_input_type"
        elif loc and loc[-1] == "contents":
            code = "missing_contents"
        else:
            code = "INVALID_INPUT"
        return JSONResponse(
            status_code=400,
            content={"error": code, "message": str(error["msg"])},
        )
    
    # AIProcessingError는 422 상태 코드로 반환한다.
    @app.exception_handler(AIProcessingError)
    async def ai_processing_exception_handler(request: Request, exc: AIProcessingError):
        return JSONResponse(
            status_code=422,
            content={"error": exc.code, "message": exc.message},
        )

    # 명시적으로 처리되지 않은 예외는 500 상태 코드로 반환한다.
    @app.exception_handler(Exception)
    async def internal_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_SERVER_ERROR", "message": "서버 내부 오류가 발생했습니다."},
        )
