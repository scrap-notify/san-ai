from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── input_type 검증 ────────────────────────────────────────────────────────────
# 유효하지 않은 input_type이 전달되면 400 상태 코드와 "invalid_input_type" 오류 코드를 반환하는지 검증.
def test_invalid_input_type_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "video", "content": "hello"})
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_input_type"

# input_type이 누락된 경우 400 상태 코드를 반환하는지 검증.
def test_missing_input_type_returns_400() -> None:
    response = client.post("/ai/analyze", json={"content": "hello"})
    assert response.status_code == 400

# content 필드가 누락된 경우 400 상태 코드를 반환하는지 검증.
def test_missing_content_field_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "text"})
    assert response.status_code == 400


# ── text 전처리 검증 ────────────────────────────────────────────────────────────
# content가 비어있거나 공백만 있는 경우 400 상태 코드와 "missing_content" 오류 코드를 반환하는지 검증.
def test_text_empty_content_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "text", "content": ""})
    assert response.status_code == 400
    assert response.json()["code"] == "missing_content"

# content가 공백만 있는 경우에도 400 상태 코드와 "missing_content" 오류 코드를 반환하는지 검증.
def test_text_whitespace_content_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "text", "content": "   "})
    assert response.status_code == 400
    assert response.json()["code"] == "missing_content"


# ── url 전처리 검증 ─────────────────────────────────────────────────────────────
# content가 유효한 URL 형식이 아닌 경우 400 상태 코드와 "invalid_url" 오류 코드를 반환하는지 검증.
def test_url_invalid_format_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "url", "content": "not-a-url"})
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_url"

# URL이 http 또는 https 스킴이 아닌 경우 400 상태 코드와 "invalid_url" 오류 코드를 반환하는지 검증.
def test_url_ftp_scheme_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "url", "content": "ftp://example.com"})
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_url"

# URL이 유효하지만 요청 중 오류가 발생하는 경우 422 상태 코드와 "url_fetch_failed" 오류 코드를 반환하는지 검증.
def test_url_fetch_failure_returns_422() -> None:
    with patch("app.services.preprocessor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = Exception("connection refused")

        response = client.post("/ai/analyze", json={"input_type": "url", "content": "https://example.com"})

    assert response.status_code == 422
    assert response.json()["code"] == "url_fetch_failed"


# ── image 전처리 검증 ───────────────────────────────────────────────────────────
# content가 유효한 URL 형식이 아닌 경우 400 상태 코드와 "invalid_url" 오류 코드를 반환하는지 검증.
def test_image_invalid_url_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "image", "content": "not-a-url"})
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_url"

# 이미지 URL이 유효하지만 접근할 수 없는 경우 422 상태 코드와 "image_access_failed" 오류 코드를 반환하는지 검증.
def test_image_access_failure_returns_422() -> None:
    with patch("app.services.preprocessor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.head.side_effect = Exception("403 Forbidden")

        response = client.post(
            "/ai/analyze",
            json={"input_type": "image", "content": "https://s3.amazonaws.com/bucket/image.png"},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "image_access_failed"
