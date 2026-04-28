from app.llms.embeddings import EmbeddingClient


def test_embed_returns_float_list() -> None:
    client = EmbeddingClient()
    result = client.embed("테스트 텍스트")

    print(f"\n[임베딩 차원] {len(result)}")
    print(f"[앞 5개 값] {result[:5]}")

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(v, float) for v in result)


def test_embed_same_text_same_vector() -> None:
    client = EmbeddingClient()
    result1 = client.embed("동일한 텍스트")
    result2 = client.embed("동일한 텍스트")

    print(f"\n[1회 앞 3개] {result1[:3]}")
    print(f"[2회 앞 3개] {result2[:3]}")

    assert result1 == result2


def test_embed_different_text_different_vector() -> None:
    client = EmbeddingClient()
    result1 = client.embed("리액트 상태관리")
    result2 = client.embed("파이썬 비동기 처리")

    print(f"\n['리액트 상태관리' 앞 3개] {result1[:3]}")
    print(f"['파이썬 비동기 처리' 앞 3개] {result2[:3]}")

    assert result1 != result2
