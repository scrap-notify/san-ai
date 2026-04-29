import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AIProcessingError, ContentValidationError
from app.schemas.common import InputType
from app.services.preprocessor import preprocess


# ── text ──────────────────────────────────────────────────────────────────────
# content가 비어있거나 공백만 있는 경우 400 상태 코드와 "missing_content" 오류 코드를 반환하는지 검증.
def test_text_empty_raises_missing_content() -> None:
    with pytest.raises(ContentValidationError) as exc:
        asyncio.run(preprocess(InputType.text, ""))
    assert exc.value.code == "missing_content"

# content가 공백만 있는 경우 400 상태 코드와 "missing_content" 오류 코드를 반환하는지 검증.
def test_text_whitespace_only_raises_missing_content() -> None:
    with pytest.raises(ContentValidationError) as exc:
        asyncio.run(preprocess(InputType.text, "   "))
    assert exc.value.code == "missing_content"

# content가 유효한 경우 공백이 제거된 텍스트를 반환하는지 검증.
def test_text_returns_stripped() -> None:
    result = asyncio.run(preprocess(InputType.text, "  hello world  "))
    assert result == "hello world"

# content가 유효한 경우 원본 텍스트에서 공백만 제거된 형태로 반환하는지 검증.
def test_text_valid_returns_as_is() -> None:
    result = asyncio.run(preprocess(InputType.text, "파이썬은 동적 타입 언어다."))
    assert result == "파이썬은 동적 타입 언어다."


# ── url ───────────────────────────────────────────────────────────────────────
# ftp:// 같은 유효하지 않은 URL이 입력된 경우 400 상태 코드와 "invalid_url" 오류 코드를 반환하는지 검증.
def test_url_invalid_scheme_raises_invalid_url() -> None:
    with pytest.raises(ContentValidationError) as exc:
        asyncio.run(preprocess(InputType.url, "ftp://example.com"))
    assert exc.value.code == "invalid_url"

# URL이 유효하지만 스킴이 없는 경우 400 상태 코드와 "invalid_url" 오류 코드를 반환하는지 검증.
def test_url_no_scheme_raises_invalid_url() -> None:
    with pytest.raises(ContentValidationError) as exc:
        asyncio.run(preprocess(InputType.url, "example.com/article"))
    assert exc.value.code == "invalid_url"

# URL이 유효하지만 접근할 수 없는 경우 422 상태 코드와 "url_fetch_failed" 오류 코드를 반환하는지 검증.
def test_url_empty_raises_missing_content() -> None:
    with pytest.raises(ContentValidationError) as exc:
        asyncio.run(preprocess(InputType.url, ""))
    assert exc.value.code == "missing_content"

# URL이 유효하지만 요청 중 오류가 발생하는 경우 422 상태 코드와 "url_fetch_failed" 오류 코드를 반환하는지 검증.
def test_url_fetch_failure_raises_url_fetch_failed() -> None:
    with patch("app.services.preprocessor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = Exception("connection refused")

        with pytest.raises(AIProcessingError) as exc:
            asyncio.run(preprocess(InputType.url, "https://example.com/article"))
    assert exc.value.code == "url_fetch_failed"

# URL이 유효하지만 본문 추출에 실패하는 경우 422 상태 코드와 "url_content_empty" 오류 코드를 반환하는지 검증.
def test_url_empty_body_raises_url_content_empty() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.text = "<html></html>"

    with patch("app.services.preprocessor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response

        with patch("app.services.preprocessor.trafilatura.extract", return_value=None):
            with pytest.raises(AIProcessingError) as exc:
                asyncio.run(preprocess(InputType.url, "https://example.com/article"))
    assert exc.value.code == "url_content_empty"

# URL이 유효하고 본문 추출에 성공하는 경우 추출된 본문 텍스트를 반환하는지 검증.
def test_url_success_returns_body() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.text = "<html><body><p>본문 텍스트</p></body></html>"

    with patch("app.services.preprocessor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response

        with patch("app.services.preprocessor.trafilatura.extract", return_value="본문 텍스트"):
            result = asyncio.run(preprocess(InputType.url, "https://example.com/article"))

    assert result == "본문 텍스트"


# ── image ─────────────────────────────────────────────────────────────────────
# 이미지 URL 형식 오류
def test_image_invalid_url_raises_invalid_url() -> None:
    with pytest.raises(ContentValidationError) as exc:
        asyncio.run(preprocess(InputType.image, "not-a-url"))
    assert exc.value.code == "invalid_url"

# 빈 이미지 URL
def test_image_empty_raises_missing_content() -> None:
    with pytest.raises(ContentValidationError) as exc:
        asyncio.run(preprocess(InputType.image, ""))
    assert exc.value.code == "missing_content"

# 이미지 접근 실패
def test_image_access_failure_raises_image_access_failed() -> None:
    with patch("app.services.preprocessor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.head.side_effect = Exception("403 Forbidden")

        with pytest.raises(AIProcessingError) as exc:
            asyncio.run(preprocess(InputType.image, "https://s3.amazonaws.com/bucket/image.png"))
    assert exc.value.code == "image_access_failed"

# 이미지 분석 실패
def test_image_analysis_failure_raises_image_analysis_failed() -> None:
    mock_head = MagicMock()
    mock_head.raise_for_status = MagicMock()

    with patch("app.services.preprocessor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.head.return_value = mock_head

        with patch("app.services.preprocessor.LLMClient") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm
            mock_llm.call_with_image.side_effect = AIProcessingError(
                code="image_analysis_failed", message="분석 실패"
            )

            with pytest.raises(AIProcessingError) as exc:
                asyncio.run(preprocess(InputType.image, "https://s3.amazonaws.com/bucket/image.png"))
    assert exc.value.code == "image_analysis_failed"

# 이미지 분석 성공
def test_image_success_returns_description() -> None:
    mock_head = MagicMock()
    mock_head.raise_for_status = MagicMock()

    with patch("app.services.preprocessor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.head.return_value = mock_head

        with patch("app.services.preprocessor.LLMClient") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm
            mock_llm.call_with_image.return_value = "이미지에는 파이썬 코드가 포함되어 있습니다."

            result = asyncio.run(preprocess(InputType.image, "https://s3.amazonaws.com/bucket/image.png"))

    assert result == "이미지에는 파이썬 코드가 포함되어 있습니다."
