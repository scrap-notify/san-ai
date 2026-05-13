import base64
import os
import json as _json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from app.llms.client import LLMClient
from app.prompts import IMAGE_DESCRIBE_PROMPT
from app.main import app

load_dotenv()

client = TestClient(app)

_URL_FIXTURE = Path("tests/fixtures/test_url.txt")
_IMAGE_FIXTURE = Path("tests/fixtures/test_image.png")

skip_if_no_key = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY 없음 — 외부 API 테스트 스킵",
)

skip_if_no_url = pytest.mark.skipif(
    not _URL_FIXTURE.exists() or not _URL_FIXTURE.read_text().strip(),
    reason="tests/fixtures/test_url.txt 없거나 비어있음 — URL 통합 테스트 스킵",
)

_VALID_CATEGORIES = {"프론트엔드", "백엔드", "AI/ML", "데이터", "인프라/DevOps", "CS", "보안", "모바일", "기타"}


def _print_response(label: str, body: dict) -> None:
    display = {**body, "embedding": body.get("embedding", [])[:5]}
    print(f"\n[POST /ai/analyze ({label}) → 200]")
    print(_json.dumps(display, ensure_ascii=False, indent=2))
    print(f"  embedding 총 {len(body.get('embedding', []))}차원 (앞 5개만 표시)")


def _assert_spec(body: dict) -> None:
    assert "title" in body and isinstance(body["title"], str) and body["title"]
    assert "summary" in body and isinstance(body["summary"], str)
    assert "tags" in body and isinstance(body["tags"], list) and 1 <= len(body["tags"]) <= 5
    assert "category" in body and body["category"] in _VALID_CATEGORIES
    assert "embedding" in body and isinstance(body["embedding"], list) and len(body["embedding"]) > 0


# ── 실제 API 200 응답 검증 ──────────────────────────────────────────────────────

# text 입력으로 실제 LLM·임베딩 API를 호출해 200과 API 명세 필드를 검증.
@skip_if_no_key
def test_analyze_200_text_real_api() -> None:
    url = _URL_FIXTURE.read_text().strip()
    # URL에서 본문을 미리 크롤링해 text로 전달 (전처리 없이 분석만 검증)
    from app.services.preprocessor import _preprocess_url
    import asyncio
    text = asyncio.run(_preprocess_url(url))

    response = client.post("/ai/analyze", json={"input_type": "text", "content": text[:2000]})

    assert response.status_code == 200
    body = response.json()
    _print_response("text", body)
    _assert_spec(body)


# url 입력으로 실제 크롤링·LLM·임베딩 API를 호출해 200과 API 명세 필드를 검증.
@skip_if_no_key
@skip_if_no_url
def test_analyze_200_url_real_api() -> None:
    url = _URL_FIXTURE.read_text().strip()

    response = client.post("/ai/analyze", json={"input_type": "url", "content": url})

    assert response.status_code == 200
    body = response.json()
    _print_response("url", body)
    _assert_spec(body)


# image 입력으로 실제 Vision·LLM·임베딩 API를 호출해 200과 API 명세 필드를 검증.
# base64 크기가 100KB 미만이어야 GMS 게이트웨이를 통과함 (현재 ~59KB).
@skip_if_no_key
def test_analyze_200_image_real_api() -> None:
    image_data_url = "data:image/png;base64," + base64.b64encode(_IMAGE_FIXTURE.read_bytes()).decode()
    description = LLMClient().call_with_image(IMAGE_DESCRIBE_PROMPT, image_data_url, error_code="test_failed")

    with patch("app.services.analyzer.preprocess", return_value=description):
        response = client.post("/ai/analyze", json={"input_type": "image", "content": image_data_url})

    assert response.status_code == 200
    body = response.json()
    _print_response("image", body)
    _assert_spec(body)


# ── mock 성공 응답 검증 ─────────────────────────────────────────────────────────
# mock으로 LLM·임베딩을 대체해 HTTP 200 응답 구조만 검증.
def test_analyze_text_returns_200_with_spec_fields() -> None:
    with patch("app.services.analyzer.preprocess", return_value="본문 텍스트"):
        with patch("app.services.analyzer.LLMClient") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm
            mock_llm.call_json.return_value = {
                "title": "제목", "summary": "요약", "tags": ["tag1"], "category": "기타"
            }
            with patch("app.services.analyzer.EmbeddingClient") as mock_emb_cls:
                mock_emb = MagicMock()
                mock_emb_cls.return_value = mock_emb
                mock_emb.embed.return_value = [0.1, 0.2, 0.3]

                response = client.post("/ai/analyze", json={"input_type": "text", "content": "테스트 본문"})

    assert response.status_code == 200
    body = response.json()
    assert "title" in body and isinstance(body["title"], str)
    assert "summary" in body and isinstance(body["summary"], str)
    assert "tags" in body and isinstance(body["tags"], list)
    assert "category" in body and isinstance(body["category"], str)
    assert "embedding" in body and isinstance(body["embedding"], list)


# ── input_type 검증 ────────────────────────────────────────────────────────────
# 유효하지 않은 input_type이 전달되면 400 상태 코드와 "invalid_input_type" 오류 코드를 반환하는지 검증.
def test_invalid_input_type_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "video", "content": "hello"})
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_input_type"

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
    assert response.json()["error"] == "missing_content"

# content가 공백만 있는 경우에도 400 상태 코드와 "missing_content" 오류 코드를 반환하는지 검증.
def test_text_whitespace_content_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "text", "content": "   "})
    assert response.status_code == 400
    assert response.json()["error"] == "missing_content"


# ── url 전처리 검증 ─────────────────────────────────────────────────────────────
# content가 유효한 URL 형식이 아닌 경우 400 상태 코드와 "invalid_url" 오류 코드를 반환하는지 검증.
def test_url_invalid_format_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "url", "content": "not-a-url"})
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_url"

# URL이 http 또는 https 스킴이 아닌 경우 400 상태 코드와 "invalid_url" 오류 코드를 반환하는지 검증.
def test_url_ftp_scheme_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "url", "content": "ftp://example.com"})
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_url"

# URL이 유효하지만 요청 중 오류가 발생하는 경우 422 상태 코드와 "url_fetch_failed" 오류 코드를 반환하는지 검증.
def test_url_fetch_failure_returns_422() -> None:
    with patch("app.services.preprocessor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = Exception("connection refused")

        response = client.post("/ai/analyze", json={"input_type": "url", "content": "https://example.com"})

    assert response.status_code == 422
    assert response.json()["error"] == "url_fetch_failed"


# ── image 전처리 검증 ───────────────────────────────────────────────────────────
# content가 유효한 URL 형식이 아닌 경우 400 상태 코드와 "invalid_url" 오류 코드를 반환하는지 검증.
def test_image_invalid_url_returns_400() -> None:
    response = client.post("/ai/analyze", json={"input_type": "image", "content": "not-a-url"})
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_url"

# 이미지 URL이 유효하지만 접근할 수 없는 경우 422 상태 코드와 "image_access_failed" 오류 코드를 반환하는지 검증.
def test_image_access_failure_returns_422() -> None:
    with patch("app.services.preprocessor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.stream = MagicMock(side_effect=Exception("403 Forbidden"))

        response = client.post(
            "/ai/analyze",
            json={"input_type": "image", "content": "https://s3.amazonaws.com/bucket/image.png"},
        )

    assert response.status_code == 422
    assert response.json()["error"] == "image_access_failed"
