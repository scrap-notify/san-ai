from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings
from app.core.exceptions import AIProcessingError

# EmbeddingClient는 텍스트를 벡터로 변환하는 임베딩 모델과의 호출과 응답 처리를 담당
class EmbeddingClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._model = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout,
        )

    # 텍스트를 임베딩 벡터로 변환하는 메서드
    def embed(self, text: str) -> list[float]:
        try:
            return self._model.embed_query(text)
        except Exception as e:
            raise AIProcessingError(code="embedding_failed", message=str(e)) from e
