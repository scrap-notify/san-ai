from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

URL = "/api/v1/ai/til"


def test_empty_contents_returns_400_missing_contents() -> None:
    response = client.post(URL, json={"contents": [], "generate_til": True})

    assert response.status_code == 400
    assert response.json()["code"] == "missing_contents"


def test_image_input_type_returns_400_invalid_input_type() -> None:
    response = client.post(
        URL,
        json={
            "contents": [{"input_type": "image", "content": "x"}],
            "generate_til": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_input_type"


def test_generate_til_true_returns_markdown() -> None:
    response = client.post(
        URL,
        json={
            "contents": [{"input_type": "text", "content": "메모"}],
            "generate_til": True,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert isinstance(body["til_markdown"], str)
    assert len(body["til_markdown"]) > 0


def test_generate_til_false_returns_null_markdown() -> None:
    response = client.post(
        URL,
        json={
            "contents": [{"input_type": "text", "content": "메모"}],
            "generate_til": False,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["til_markdown"] is None
    assert isinstance(body["embeddings"], list) and len(body["embeddings"]) > 0


def test_til_is_structured_by_topic_not_flat_list() -> None:
    response = client.post(
        URL,
        json={
            "contents": [
                {"input_type": "text", "content": "클로저는 외부 변수를 기억한다."},
                {"input_type": "text", "content": "React 상태는 시간에 따라 관리된다."},
            ],
            "generate_til": True,
        },
    )

    markdown: str = response.json()["til_markdown"]
    # 카드 단순 나열이 아니라 주제별 구조라면 ## 헤더가 2개 이상 존재해야 한다.
    section_headers = sum(1 for line in markdown.splitlines() if line.startswith("## "))
    assert section_headers >= 2


def test_til_generation_failure_returns_422(monkeypatch) -> None:
    class _FailingChain:
        async def ainvoke(self, *args, **kwargs):
            raise RuntimeError("LLM 실패 시뮬레이션")

    monkeypatch.setattr("app.services.til.build_til_chain", lambda model: _FailingChain())

    response = client.post(
        URL,
        json={
            "contents": [{"input_type": "text", "content": "메모"}],
            "generate_til": True,
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "til_generation_failed"


def test_embedding_failure_returns_422(monkeypatch) -> None:
    class _FailingEmbeddings:
        async def aembed_query(self, text: str):
            raise RuntimeError("임베딩 실패 시뮬레이션")

    monkeypatch.setattr(
        "app.services.til.create_stub_embedding_model", lambda: _FailingEmbeddings()
    )

    # generate_til=False로 LLM 경로를 건너뛰어 임베딩 실패만 격리해 검증한다.
    response = client.post(
        URL,
        json={
            "contents": [{"input_type": "text", "content": "메모"}],
            "generate_til": False,
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "embedding_failed"
