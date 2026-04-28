from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import AIProcessingError, register_exception_handlers

_app = FastAPI()
register_exception_handlers(_app)


@_app.get("/test-error/{code}")
async def trigger_error(code: str) -> None:
    raise AIProcessingError(code=code, message="테스트 오류")


client = TestClient(_app)

# AIProcessingError가 발생하면 422 Unprocessable Entity 상태 코드가 반환되는지 테스트
def test_ai_processing_error_returns_422() -> None:
    response = client.get("/test-error/analyze_failed")

    assert response.status_code == 422

# AIProcessingError의 code가 응답 본문에 포함되어 반환되는지 테스트
def test_ai_processing_error_code_in_body() -> None:
    response = client.get("/test-error/analyze_failed")

    assert response.json()["code"] == "analyze_failed"

# AIProcessingError의 code가 다양한 값으로 설정되어도 올바르게 반환되는지 테스트
def test_ai_processing_error_different_codes() -> None:
    for code in ("analyze_failed", "til_generation_failed", "embedding_failed"):
        response = client.get(f"/test-error/{code}")

        assert response.json()["code"] == code
