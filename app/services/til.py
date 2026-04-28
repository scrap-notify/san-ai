from datetime import date

from app.chains.til import build_til_chain
from app.core.exceptions import (
    EmbeddingError,
    InvalidInputTypeError,
    MissingContentsError,
    TilGenerationError,
)
from app.llms.stub import create_stub_chat_model, create_stub_embedding_model
from app.schemas.common import InputType
from app.schemas.til import TilContent, TilRequest, TilResponse
from app.utils.url import extract_url_content


_CARD_SEPARATOR = "\n\n---\n\n"


async def _preprocess_content(item: TilContent) -> str:
    if item.input_type == InputType.image:
        raise InvalidInputTypeError("image 타입은 아직 지원하지 않습니다.")
    if item.input_type == InputType.url:
        extracted = await extract_url_content(item.content)
        if not extracted:
            # TODO(S14P31A309-76): URL 본문 추출 실패를 til_generation_failed로 묶어 처리 중.
            # 외부 의존 실패 / 클라이언트 잘못된 URL / 추출기가 본문을 못 찾는 경우가 섞여있어
            # 별도 에러 코드(url_fetch_failed 등)나 카드 스킵 정책으로 분리할지 후속 검토 필요.
            raise TilGenerationError(f"URL 본문 추출 실패: {item.content}")
        return extracted
    return item.content


async def generate_til(request: TilRequest) -> TilResponse:
    if not request.contents:
        raise MissingContentsError()

    cards = [await _preprocess_content(c) for c in request.contents]
    cards_text = _CARD_SEPARATOR.join(cards)

    til_markdown: str | None = None
    if request.generate_til:
        chain = build_til_chain(create_stub_chat_model())
        try:
            til_markdown = await chain.ainvoke(
                {
                    "today": date.today().strftime("%Y.%m.%d"),
                    "cards": cards_text,
                }
            )
        except Exception as e:
            raise TilGenerationError(str(e)) from e

    try:
        embeddings = await create_stub_embedding_model().aembed_query(cards_text)
    except Exception as e:
        raise EmbeddingError(str(e)) from e

    return TilResponse(til_markdown=til_markdown, embeddings=embeddings)
