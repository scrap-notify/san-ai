from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.exceptions import AIProcessingError
from app.main import app

client = TestClient(app)


# ── 정상 응답 ───────────────────────────────────────────────────────────────────
# 정상 query가 입력되면 200 상태 코드와 임베딩 벡터 리스트를 반환하는지 검증.
def test_valid_query_returns_embedding() -> None:
    fake_embedding = [0.023, -0.341, 0.756]
    with patch("app.api.v1.endpoints.search.EmbeddingClient") as mock_cls:
        mock_cls.return_value.embed.return_value = fake_embedding

        response = client.post("/ai/search", json={"query": "리액트 상태관리 개념 정리"})

    assert response.status_code == 200
    assert response.json() == {"embedding": fake_embedding}


# ── query 검증 ─────────────────────────────────────────────────────────────────
# query 필드가 누락된 경우 400 상태 코드를 반환하는지 검증.
def test_missing_query_field_returns_400() -> None:
    response = client.post("/ai/search", json={})
    assert response.status_code == 400


# query가 빈 문자열인 경우 400 상태 코드와 "missing_query" 오류 코드를 반환하는지 검증.
def test_empty_query_returns_400() -> None:
    response = client.post("/ai/search", json={"query": ""})
    assert response.status_code == 400
    assert response.json()["error"] == "missing_query"


# query가 공백만 있는 경우에도 400 상태 코드와 "missing_query" 오류 코드를 반환하는지 검증.
def test_whitespace_query_returns_400() -> None:
    response = client.post("/ai/search", json={"query": "   "})
    assert response.status_code == 400
    assert response.json()["error"] == "missing_query"


# ── 임베딩 실패 ────────────────────────────────────────────────────────────────
# 임베딩 생성 실패 시 422 상태 코드와 "embedding_failed" 오류 코드를 반환하는지 검증.
def test_embedding_failure_returns_422() -> None:
    with patch("app.api.v1.endpoints.search.EmbeddingClient") as mock_cls:
        mock_cls.return_value.embed.side_effect = AIProcessingError(
            code="embedding_failed", message="임베딩 실패"
        )

        response = client.post("/ai/search", json={"query": "리액트"})

    assert response.status_code == 422
    assert response.json()["error"] == "embedding_failed"
