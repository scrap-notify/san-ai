import asyncio
import logging

from app.core.exceptions import AIProcessingError
from app.llms.client import LLMClient
from app.llms.embeddings import EmbeddingClient
from app.prompts.analyze import ANALYZE_PROMPT_TEMPLATE
from app.schemas.analyze import AnalyzeResponse
from app.schemas.common import InputType
from app.services.preprocessor import preprocess

_REQUIRED_KEYS = {"title", "summary", "tags", "category"}
_MAX_TITLE_LENGTH = 20
_MAX_SUMMARY_SENTENCES = 3
_MAX_SUMMARY_SENTENCE_LENGTH = 27

logger = logging.getLogger(__name__)


def _log_length_warnings(title: str, summary: str) -> None:
    if len(title) > _MAX_TITLE_LENGTH:
        logger.warning(
            "analyze title length exceeded: length=%s max=%s",
            len(title),
            _MAX_TITLE_LENGTH,
        )

    summary_lines = [line.strip() for line in summary.splitlines() if line.strip()]
    if len(summary_lines) > _MAX_SUMMARY_SENTENCES:
        logger.warning(
            "analyze summary sentence count exceeded: count=%s max=%s",
            len(summary_lines),
            _MAX_SUMMARY_SENTENCES,
        )

    for index, line in enumerate(summary_lines, start=1):
        if len(line) > _MAX_SUMMARY_SENTENCE_LENGTH:
            logger.warning(
                "analyze summary sentence length exceeded: index=%s length=%s max=%s",
                index,
                len(line),
                _MAX_SUMMARY_SENTENCE_LENGTH,
            )


# LLM을 활용하여 텍스트를 분석
async def analyze(input_type: InputType, content: str) -> AnalyzeResponse:
    text = await preprocess(input_type, content)

    llm = LLMClient()
    prompt = ANALYZE_PROMPT_TEMPLATE.format(text=text)
    result = await asyncio.to_thread(llm.call_json, prompt, "analyze_failed")

    # LLM 응답에 필수 필드가 모두 포함되어 있는지 검증
    if not _REQUIRED_KEYS.issubset(result):
        missing = _REQUIRED_KEYS - result.keys()
        raise AIProcessingError(
            code="analyze_failed",
            message=f"LLM 응답에 필수 필드 누락: {missing}",
        )

    _log_length_warnings(result["title"], result["summary"])

    # 텍스트 임베딩 생성
    embedding_client = EmbeddingClient()
    embeddings = await asyncio.to_thread(embedding_client.embed, text)

    return AnalyzeResponse(
        title=result["title"],
        summary=result["summary"],
        tags=result["tags"][:5],
        category=result["category"],
        embedding=embeddings,
    )
