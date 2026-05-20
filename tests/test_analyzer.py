import asyncio
import base64
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from app.core.exceptions import AIProcessingError
from app.llms.client import LLMClient
from app.prompts import IMAGE_DESCRIBE_PROMPT
from app.schemas.analyze import AnalyzeResponse
from app.schemas.common import InputType
from app.services.analyzer import analyze

load_dotenv()

_URL_FIXTURE = Path("tests/fixtures/test_url.txt")
_IMAGE_FIXTURE = Path("tests/fixtures/test_image.png")

_VALID_CATEGORIES = {"프론트엔드", "백엔드", "프로그래밍 언어", "AI/ML", "데이터 엔지니어링", "데이터베이스", "인프라/DevOps", "CS", "보안", "모바일", "아키텍처/설계", "테스트/QA", "기타"}

skip_if_no_key = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY 없음 — 외부 API 테스트 스킵",
)

skip_if_no_url = pytest.mark.skipif(
    not _URL_FIXTURE.exists() or not _URL_FIXTURE.read_text().strip(),
    reason="tests/fixtures/test_url.txt 없거나 비어있음 — URL 통합 테스트 스킵",
)

# 분석결과가 AnalyzeResponse 스키마를 준수하고, 각 필드가 유효한 값인지 검증하는 함수
def _assert_valid_response(result: AnalyzeResponse) -> None:
    assert isinstance(result, AnalyzeResponse)
    assert result.title and len(result.title) <= 50
    lines = result.summary.split("\n")
    assert 1 <= len(lines) <= 3
    assert 1 <= len(result.tags) <= 5
    assert result.category in _VALID_CATEGORIES
    assert len(result.embedding) > 0


# ── text 통합 테스트 ────────────────────────────────────────────────────────────

# test_image.png 이미지 본문 기반 텍스트로 실제 API 분석 결과를 검증
@skip_if_no_key
def test_analyze_text_success() -> None:
    text = (
        "DevOps는 개발(Development)과 운영(Operation)을 결합해 탄생한 개발 방법론입니다. "
        "시스템 개발자와 운영을 담당하는 정보기술 전문가 사이의 소통, 협업, 통합 및 자동화를 강조하는 "
        "소프트웨어 개발 방법론입니다. 주요 단계는 Plan, Build, Test, Deploy, Operate, Observe이며 "
        "지속적인 피드백(Continuous Feedback)을 통해 개선합니다."
    )

    result = asyncio.run(analyze(InputType.text, text))

    print("\n[analyze - text]")
    print(f"  title   : {result.title}")
    print(f"  summary : {result.summary}")
    print(f"  tags    : {result.tags}")
    print(f"  category: {result.category}")
    print(f"  embed   : {len(result.embedding)}차원")

    _assert_valid_response(result)


# ── url 통합 테스트 ─────────────────────────────────────────────────────────────

# test_url.txt의 URL로 실제 페이지를 크롤링하고 분석 결과를 검증
@skip_if_no_key
@skip_if_no_url
def test_analyze_url_success() -> None:
    url = _URL_FIXTURE.read_text().strip()

    result = asyncio.run(analyze(InputType.url, url))

    print(f"\n[analyze - url ({url})]")
    print(f"  title   : {result.title}")
    print(f"  summary : {result.summary}")
    print(f"  tags    : {result.tags}")
    print(f"  category: {result.category}")
    print(f"  embed   : {len(result.embedding)}차원")

    _assert_valid_response(result)


# ── image 통합 테스트 ───────────────────────────────────────────────────────────

# test_image.png를 base64 data URL로 변환해 실제 Vision API로 이미지 설명을 생성하고,
# 그 결과로 LLM 분석·임베딩까지 실제 API로 검증.
@skip_if_no_key
def test_analyze_image_success() -> None:
    image_data_url = "data:image/png;base64," + base64.b64encode(_IMAGE_FIXTURE.read_bytes()).decode()

    # 1단계: 실제 Vision API로 이미지 → 텍스트 설명 생성 (프로덕션과 동일한 IMAGE_DESCRIBE_PROMPT 사용)
    # base64 크기가 100KB 미만이어야 GMS 게이트웨이를 통과함 (현재 ~59KB)
    description = LLMClient().call_with_image(
        IMAGE_DESCRIBE_PROMPT, image_data_url, error_code="test_failed"
    )

    # 2단계: 설명 텍스트를 주입하고 LLM 분석·임베딩은 실제 API 호출
    with patch("app.services.analyzer.preprocess", return_value=description):
        result = asyncio.run(analyze(InputType.image, image_data_url))

    print(f"\n[analyze - image ({_IMAGE_FIXTURE.name})]")
    print(f"  description: {description[:100]}...")
    print(f"  title   : {result.title}")
    print(f"  summary : {result.summary}")
    print(f"  tags    : {result.tags}")
    print(f"  category: {result.category}")
    print(f"  embed   : {len(result.embedding)}차원")

    _assert_valid_response(result)


# ── analyzer 로직 검증 ──────────────────────────────────────────────────────────

# LLM 응답에 필수 필드가 누락된 경우 AIProcessingError(code="analyze_failed")가 발생하는지 검증
def test_analyze_missing_required_field_raises_error() -> None:
    with patch("app.services.analyzer.preprocess", return_value="본문 텍스트"):
        with patch("app.services.analyzer.LLMClient") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm
            mock_llm.call_json.return_value = {"title": "제목만 있음"}

            with pytest.raises(AIProcessingError) as exc:
                asyncio.run(analyze(InputType.text, "아무 텍스트"))

    assert exc.value.code == "analyze_failed"  # AIProcessingError 내부 코드, HTTP 응답 키는 "error"


# LLM이 태그를 5개 초과 반환해도 최대 5개만 저장하는지 검증
def test_analyze_tags_truncated_to_5() -> None:
    llm_response = {
        "title": "제목",
        "summary": "요약",
        "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7"],
        "category": "기타",
    }

    with patch("app.services.analyzer.preprocess", return_value="본문 텍스트"):
        with patch("app.services.analyzer.LLMClient") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm
            mock_llm.call_json.return_value = llm_response

            with patch("app.services.analyzer.EmbeddingClient") as mock_embed_cls:
                mock_embed = MagicMock()
                mock_embed_cls.return_value = mock_embed
                mock_embed.embed.return_value = [0.1] * 1536

                result = asyncio.run(analyze(InputType.text, "아무 텍스트"))

    assert len(result.tags) == 5
    assert result.tags == ["tag1", "tag2", "tag3", "tag4", "tag5"]
