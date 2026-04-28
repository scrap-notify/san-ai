import os
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv

from app.core.exceptions import AIProcessingError
from app.llms.client import LLMClient

load_dotenv()

skip_if_no_key = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY 없음 — 외부 API 테스트 스킵",
)


@skip_if_no_key
def test_call_returns_string() -> None:
    client = LLMClient()
    result = client.call("'hello'라고만 답해줘.", error_code="analyze_failed")

    print(f"\n[LLM 응답] {result}")

    assert isinstance(result, str)
    assert len(result) > 0


@skip_if_no_key
def test_call_json_returns_dict() -> None:
    client = LLMClient()
    result = client.call_json(
        "다음 JSON만 반환해줘. 다른 텍스트 없이. {\"status\": \"ok\"}",
        error_code="analyze_failed",
    )

    print(f"\n[LLM JSON 응답] {result}")

    assert isinstance(result, dict)


def test_call_json_raises_on_invalid_json() -> None:
    client = LLMClient()

    mock_response = MagicMock()
    mock_response.content = "not json"
    client._model = MagicMock()
    client._model.invoke.return_value = mock_response

    with pytest.raises(AIProcessingError) as exc_info:
        client.call_json("ignored", error_code="analyze_failed")

    print(f"\n[예외 code] {exc_info.value.code}")
    print(f"[예외 message] {exc_info.value.message}")

    assert exc_info.value.code == "analyze_failed"
