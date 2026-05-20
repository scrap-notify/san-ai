import asyncio
import re

from app.core.exceptions import AIProcessingError, ContentValidationError
from app.llms import EmbeddingClient, LLMClient
from app.prompts import TIL_GROUP_PROMPT, TIL_SUMMARY_PROMPT
from app.schemas.til import TilRequest, TilResponse
from app.services.preprocessor import preprocess

_BLOCK_SEPARATOR = "\n\n---\n\n"
_BATCH_SIZE = 3
_REQUIRED_KEYS = {"title", "til_markdown"}

# CommonMark에서 닫는 **앞이 구두점이고 뒤가 한글이면 closing delimiter로 인식 실패
# ex) **미사용("Slow pipes")**과 → **미사용("Slow pipes")** 과
_BOLD_CLOSE_RE = re.compile(r'(["\)\'\.\,\!\?])\*\*([가-힣])')


def _fix_bold_closing(text: str) -> str:
    return _BOLD_CLOSE_RE.sub(r'\1** \2', text)


async def _summarize(llm: LLMClient, preprocessed: str) -> str:
    return await llm.acall(
        prompt=f"{TIL_SUMMARY_PROMPT}\n\n[입력 콘텐츠]\n{preprocessed}",
        error_code="til_summarize_failed",
    )


async def _reduce(llm: LLMClient, texts: list[str]) -> dict:
    joined = _BLOCK_SEPARATOR.join(texts)
    result = await llm.acall_json(
        prompt=f"{TIL_GROUP_PROMPT}\n\n[요약 콘텐츠]\n{joined}",
        error_code="til_generation_failed",
    )
    if not _REQUIRED_KEYS.issubset(result):
        missing = _REQUIRED_KEYS - result.keys()
        raise AIProcessingError(
            code="til_generation_failed",
            message=f"LLM 응답에 필수 필드 누락: {missing}",
        )
    return result


async def generate_til(request: TilRequest) -> TilResponse:
    if not request.contents:
        raise ContentValidationError(code="missing_contents", message="contents는 비어있을 수 없습니다.")

    preprocessed_list = await asyncio.gather(
        *(preprocess(item.input_type, item.content) for item in request.contents)
    )

    title: str | None = None
    til_markdown: str | None = None

    if request.generate_til:
        llm = LLMClient()

        # Step 1: 카드별 개별 요약 (병렬)
        summaries = list(await asyncio.gather(
            *(_summarize(llm, p) for p in preprocessed_list)
        ))

        if len(summaries) <= _BATCH_SIZE:
            # 카드 수가 배치 크기 이하면 바로 최종 TIL 생성
            result = await _reduce(llm, summaries)
        else:
            # Step 2: 3개씩 묶어 중간 TIL 생성 (배치 간 병렬)
            batches = [summaries[i:i + _BATCH_SIZE] for i in range(0, len(summaries), _BATCH_SIZE)]
            intermediate = await asyncio.gather(
                *(_reduce(llm, batch) for batch in batches)
            )
            # Step 3: 중간 TIL들을 합쳐 최종 TIL 생성
            result = await _reduce(llm, [r["til_markdown"] for r in intermediate])

        title = result["title"]
        til_markdown = _fix_bold_closing(result["til_markdown"])

    embedding_input = til_markdown if til_markdown is not None else _BLOCK_SEPARATOR.join(preprocessed_list)
    embedding = EmbeddingClient().embed(embedding_input)

    return TilResponse(title=title, til_markdown=til_markdown, embedding=embedding)
