import asyncio
from urllib.parse import urlparse

import httpx
import trafilatura

from app.core.exceptions import AIProcessingError, ContentValidationError
from app.llms import LLMClient
from app.prompts import IMAGE_DESCRIBE_PROMPT
from app.schemas.common import InputType

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# 전처리 모듈은 입력된 콘텐츠 유형에 따라 텍스트, URL, 이미지에 대한 전처리를 수행. URL의 경우 본문을 추출, 이미지의 경우 LLM을 활용하여 설명 텍스트로 변환.
def _validate_url(content: str) -> None:
    parsed = urlparse(content)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ContentValidationError(code="invalid_url", message="유효하지 않은 URL입니다.")

# 텍스트 콘텐츠는 공백을 제거한 후 비어있지 않은지 확인. 유효하지 않은 경우 ContentValidationError를 발생.
def _preprocess_text(content: str) -> str:
    text = content.strip()
    if not text:
        raise ContentValidationError(code="missing_content", message="content는 비어있을 수 없습니다.")
    return text

# URL 콘텐츠는 유효한 URL인지 검증한 후 HTTP GET 요청을 통해 페이지를 가져와 trafilatura로 본문을 추출. 실패 시 AIProcessingError를 발생.
async def _preprocess_url(content: str) -> str:
    _validate_url(content)

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=_HEADERS) as client:
            response = await client.get(content)
            response.raise_for_status()
    except ContentValidationError:
        raise
    except Exception as e:
        raise AIProcessingError(code="url_fetch_failed", message=f"URL 요청 실패: {e}") from e

    body = trafilatura.extract(
        response.text,
        include_tables=True,
        no_fallback=False,
        favor_recall=True,
    )
    if not body:
        raise AIProcessingError(code="url_content_empty", message="URL에서 본문을 추출할 수 없습니다.")

    return body

# 이미지 콘텐츠는 유효한 URL인지 검증한 후 HTTP HEAD 요청으로 접근 가능 여부를 확인. 이후 LLMClient의 call_with_image 메서드를 사용하여 이미지 설명 텍스트를 생성. 실패 시 AIProcessingError를 발생.
async def _preprocess_image(content: str) -> str:
    _validate_url(content)

    try:
        async with httpx.AsyncClient(timeout=10.0, headers=_HEADERS) as client:
            head = await client.head(content, follow_redirects=True)
            head.raise_for_status()
    except ContentValidationError:
        raise
    except Exception as e:
        raise AIProcessingError(code="image_access_failed", message=f"이미지 URL 접근 실패: {e}") from e

    llm = LLMClient()
    return await asyncio.to_thread(
        llm.call_with_image,
        prompt=IMAGE_DESCRIBE_PROMPT,
        image_url=content,
        error_code="image_analysis_failed",
    )

# preprocess 함수는 입력된 콘텐츠 유형에 따라 적절한 전처리 함수를 호출하여 텍스트, URL, 이미지에 대한 전처리를 수행. 콘텐츠가 유효하지 않거나 처리 중 오류가 발생하면 예외를 발생시킴.
async def preprocess(input_type: InputType, content: str) -> str:
    if not content or not content.strip():
        raise ContentValidationError(code="missing_content", message="content는 비어있을 수 없습니다.")

    if input_type == InputType.text:
        return _preprocess_text(content)
    if input_type == InputType.url:
        return await _preprocess_url(content)
    return await _preprocess_image(content)
