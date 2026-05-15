from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.exceptions import AIProcessingError
from app.main import app

client = TestClient(app)


# ── 입력 검증 ─────────────────────────────────────────────────────────────────
def test_missing_content_field_returns_400() -> None:
    response = client.post("/ai/card", json={})
    assert response.status_code == 400


def test_invalid_input_type_returns_400() -> None:
    response = client.post(
        "/ai/card",
        json={"content": {"input_type": "video", "content": "x"}},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_input_type"


# ── 정상 처리 ─────────────────────────────────────────────────────────────────
# acall_json → title + card_markdown 반환, embed는 preprocessed 텍스트를 입력으로 받는다.
def test_card_detail_returns_markdown_and_embedding() -> None:
    with patch("app.services.card.preprocess", new=AsyncMock(return_value="전처리된 원문")), \
         patch("app.services.card.LLMClient") as llm_cls, \
         patch("app.services.card.EmbeddingClient") as emb_cls:
        llm_cls.return_value.acall_json = AsyncMock(return_value={
            "title": "FastAPI 비동기 처리",
            "card_markdown": "## 비동기 처리\n\nFastAPI는 async/await를 사용한다.",
        })
        emb_cls.return_value.embed.return_value = [0.1, 0.2, 0.3]

        response = client.post(
            "/ai/card",
            json={"content": {"input_type": "text", "content": "FastAPI async 원문"}},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "FastAPI 비동기 처리"
    assert body["card_markdown"] == "## 비동기 처리\n\nFastAPI는 async/await를 사용한다."
    assert body["embedding"] == [0.1, 0.2, 0.3]
    # 임베딩은 preprocessed 텍스트를 입력으로 받는다 (card_markdown 아님).
    emb_cls.return_value.embed.assert_called_once_with("전처리된 원문")


# ── AI 처리 실패 ───────────────────────────────────────────────────────────────
# acall_json 실패 → 422 card_detail_failed
def test_llm_failure_returns_422() -> None:
    with patch("app.services.card.preprocess", new=AsyncMock(return_value="원문")), \
         patch("app.services.card.LLMClient") as llm_cls, \
         patch("app.services.card.EmbeddingClient"):
        llm_cls.return_value.acall_json = AsyncMock(side_effect=AIProcessingError(
            code="card_detail_failed", message="LLM 실패"
        ))

        response = client.post(
            "/ai/card",
            json={"content": {"input_type": "text", "content": "원문"}},
        )

    assert response.status_code == 422
    assert response.json()["error"] == "card_detail_failed"


# acall_json 응답에 필수 필드(title, card_markdown) 누락 → 422 card_detail_failed
def test_llm_missing_required_field_returns_422() -> None:
    with patch("app.services.card.preprocess", new=AsyncMock(return_value="원문")), \
         patch("app.services.card.LLMClient") as llm_cls, \
         patch("app.services.card.EmbeddingClient"):
        llm_cls.return_value.acall_json = AsyncMock(return_value={"title": "제목"})  # card_markdown 누락

        response = client.post(
            "/ai/card",
            json={"content": {"input_type": "text", "content": "원문"}},
        )

    assert response.status_code == 422
    assert response.json()["error"] == "card_detail_failed"


# 임베딩 실패 → 422 embedding_failed
def test_embedding_failure_returns_422() -> None:
    with patch("app.services.card.preprocess", new=AsyncMock(return_value="원문")), \
         patch("app.services.card.LLMClient") as llm_cls, \
         patch("app.services.card.EmbeddingClient") as emb_cls:
        llm_cls.return_value.acall_json = AsyncMock(return_value={
            "title": "제목",
            "card_markdown": "## 내용",
        })
        emb_cls.return_value.embed.side_effect = AIProcessingError(
            code="embedding_failed", message="임베딩 실패"
        )

        response = client.post(
            "/ai/card",
            json={"content": {"input_type": "text", "content": "원문"}},
        )

    assert response.status_code == 422
    assert response.json()["error"] == "embedding_failed"
