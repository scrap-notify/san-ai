from app.core.exceptions import AIProcessingError
from app.llms import EmbeddingClient, LLMClient
from app.prompts import CARD_DETAIL_PROMPT
from app.schemas.card import CardRequest, CardResponse
from app.services.preprocessor import preprocess

_REQUIRED_KEYS = {"title", "card_markdown"}


async def generate_card_detail(request: CardRequest) -> CardResponse:
    preprocessed = await preprocess(request.content.input_type, request.content.content)

    llm = LLMClient()
    result = await llm.acall_json(
        prompt=f"{CARD_DETAIL_PROMPT}\n\n[입력 콘텐츠]\n{preprocessed}",
        error_code="card_detail_failed",
    )

    if not _REQUIRED_KEYS.issubset(result):
        missing = _REQUIRED_KEYS - result.keys()
        raise AIProcessingError(
            code="card_detail_failed",
            message=f"LLM 응답에 필수 필드 누락: {missing}",
        )

    embedding = EmbeddingClient().embed(preprocessed)

    return CardResponse(
        title=result["title"],
        card_markdown=result["card_markdown"],
        embedding=embedding,
    )
