from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ClientInputError(Exception):
    """요청 도메인 검증 단계에서 발생하는 오류. 400으로 응답한다."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message


class AIProcessingError(Exception):
    """LLM 호출, 임베딩 생성 등 AI 처리 단계에서 발생하는 오류. 422로 응답한다."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message


class MissingContentsError(ClientInputError):
    def __init__(self, message: str = "contents가 비어 있습니다."):
        super().__init__("missing_contents", message)


class InvalidInputTypeError(ClientInputError):
    def __init__(self, message: str = "지원하지 않는 input_type입니다."):
        super().__init__("invalid_input_type", message)


class TilGenerationError(AIProcessingError):
    def __init__(self, message: str = "TIL 생성에 실패했습니다."):
        super().__init__("til_generation_failed", message)


class EmbeddingError(AIProcessingError):
    def __init__(self, message: str = "임베딩 생성에 실패했습니다."):
        super().__init__("embedding_failed", message)


def register_exception_handlers(app: FastAPI) -> None:
    # FastAPI 기본 동작은 RequestValidationError를 422로 반환하지만,
    # 요청값 형식 오류는 클라이언트 잘못이므로 400으로 재정의한다.
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"code": "INVALID_INPUT", "message": str(exc.errors()[0]["msg"])},
        )

    @app.exception_handler(ClientInputError)
    async def client_input_exception_handler(request: Request, exc: ClientInputError):
        return JSONResponse(
            status_code=400,
            content={"code": exc.code, "message": exc.message},
        )

    @app.exception_handler(AIProcessingError)
    async def ai_processing_exception_handler(request: Request, exc: AIProcessingError):
        return JSONResponse(
            status_code=422,
            content={"code": exc.code, "message": exc.message},
        )

    # 명시적으로 처리되지 않은 예외를 잡는 최후의 핸들러. 내부 오류를 외부에 노출하지 않는다.
    @app.exception_handler(Exception)
    async def internal_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_SERVER_ERROR", "message": "서버 내부 오류가 발생했습니다."},
        )
