import asyncio

from app.core.exceptions import AIProcessingError, ContentValidationError
from app.llms import EmbeddingClient, LLMClient
from app.prompts import TIL_GENERATE_PROMPT
from app.schemas.til import TilRequest, TilResponse
from app.services.preprocessor import preprocess

# 전처리된 콘텐츠 블록을 LLM 입력용 텍스트로 합칠 때 사이에 넣는 구분자.
_BLOCK_SEPARATOR = "\n\n---\n\n"

_REQUIRED_KEYS = {"title", "til_markdown"}


# /ai/til 엔드포인트의 핵심 로직. 입력 콘텐츠들을 전처리한 뒤, 옵션에 따라 TIL 마크다운 문서와 임베딩 벡터를 생성한다.
async def generate_til(request: TilRequest) -> TilResponse:
    if not request.contents:
        raise ContentValidationError(code="missing_contents", message="contents는 비어있을 수 없습니다.")

    preprocessed = await asyncio.gather(
        *(preprocess(item.input_type, item.content) for item in request.contents)
    )
    joined = _BLOCK_SEPARATOR.join(preprocessed)

    title: str | None = None
    til_markdown: str | None = None
    if request.generate_til:
        prompt = f"{TIL_GENERATE_PROMPT}\n\n[입력 콘텐츠]\n{joined}"
        result = LLMClient().call_json(prompt=prompt, error_code="til_generation_failed")
        if not _REQUIRED_KEYS.issubset(result):
            missing = _REQUIRED_KEYS - result.keys()
            raise AIProcessingError(
                code="til_generation_failed",
                message=f"LLM 응답에 필수 필드 누락: {missing}",
            )
        title = result["title"]
        til_markdown = result["til_markdown"]

    # generate_til=True이면 생성된 TIL 마크다운 자체를, 아니면 전처리된 원문 통합본을 임베딩한다.
    embedding_input = til_markdown if til_markdown is not None else joined
    embedding = EmbeddingClient().embed(embedding_input)

    return TilResponse(title=title, til_markdown=til_markdown, embedding=embedding)
