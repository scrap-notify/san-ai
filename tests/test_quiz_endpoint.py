from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.exceptions import AIProcessingError
from app.main import app

client = TestClient(app)


# ── 입력 검증 ─────────────────────────────────────────────────────────────────
# contents 배열이 비어있으면 400 missing_contents.
def test_empty_contents_returns_400() -> None:
    response = client.post("/ai/quiz", json={"contents": [], "quiz_type": "short_answer"})
    assert response.status_code == 400
    assert response.json()["error"] == "missing_contents"


# contents 필드가 누락되면 400 missing_contents.
def test_missing_contents_field_returns_400() -> None:
    response = client.post("/ai/quiz", json={"quiz_type": "short_answer"})
    assert response.status_code == 400
    assert response.json()["error"] == "missing_contents"


# input_type이 유효하지 않으면 400 invalid_input_type.
def test_invalid_input_type_returns_400() -> None:
    response = client.post(
        "/ai/quiz",
        json={"contents": [{"input_type": "video", "content": "x"}], "quiz_type": "short_answer"},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_input_type"


# quiz_type 필드가 누락되면 400.
def test_missing_quiz_type_returns_400() -> None:
    response = client.post(
        "/ai/quiz",
        json={"contents": [{"input_type": "text", "content": "내용"}]},
    )
    assert response.status_code == 400


# ── 단답형 정상 처리 ───────────────────────────────────────────────────────────
# 콘텐츠 2개 → 단답형 문제 2개 반환.
def test_short_answer_returns_questions() -> None:
    with patch("app.services.quiz.preprocess", new=AsyncMock(side_effect=lambda t, c: c)), \
         patch("app.services.quiz.LLMClient") as llm_cls:
        llm_cls.return_value.call_json.return_value = {
            "questions": [
                {"question": "FastAPI가 사용하는 타입 검증 라이브러리는?", "answer": "Pydantic", "explanation": "Pydantic으로 요청/응답 타입을 검증한다."},
                {"question": "FastAPI를 구동하는 ASGI 서버는?", "answer": "uvicorn", "explanation": "uvicorn은 비동기 ASGI 서버다."},
            ]
        }

        response = client.post(
            "/ai/quiz",
            json={
                "contents": [
                    {"input_type": "text", "content": "FastAPI는 Pydantic으로 타입 검증을 한다."},
                    {"input_type": "text", "content": "uvicorn은 ASGI 서버다."},
                ],
                "quiz_type": "short_answer",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["quiz_type"] == "short_answer"
    assert len(body["questions"]) == 2
    assert body["questions"][0]["question"] == "FastAPI가 사용하는 타입 검증 라이브러리는?"
    assert body["questions"][0]["answer"] == "Pydantic"
    assert body["questions"][0]["explanation"] == "Pydantic으로 요청/응답 타입을 검증한다."


# explanation이 없으면 null로 반환된다.
def test_short_answer_without_explanation_returns_null() -> None:
    with patch("app.services.quiz.preprocess", new=AsyncMock(side_effect=lambda t, c: c)), \
         patch("app.services.quiz.LLMClient") as llm_cls:
        llm_cls.return_value.call_json.return_value = {
            "questions": [{"question": "질문", "answer": "정답"}]
        }

        response = client.post(
            "/ai/quiz",
            json={
                "contents": [{"input_type": "text", "content": "내용"}],
                "quiz_type": "short_answer",
            },
        )

    assert response.status_code == 200
    assert response.json()["questions"][0]["explanation"] is None


# ── AI 처리 실패 ───────────────────────────────────────────────────────────────
# LLM 호출 실패 시 422 quiz_generation_failed.
def test_llm_failure_returns_422() -> None:
    with patch("app.services.quiz.preprocess", new=AsyncMock(side_effect=lambda t, c: c)), \
         patch("app.services.quiz.LLMClient") as llm_cls:
        llm_cls.return_value.call_json.side_effect = AIProcessingError(
            code="quiz_generation_failed", message="LLM 실패"
        )

        response = client.post(
            "/ai/quiz",
            json={
                "contents": [{"input_type": "text", "content": "내용"}],
                "quiz_type": "short_answer",
            },
        )

    assert response.status_code == 422
    assert response.json()["error"] == "quiz_generation_failed"


# LLM 응답 문제 수가 콘텐츠 수와 다르면 422 quiz_generation_failed.
def test_wrong_question_count_returns_422() -> None:
    with patch("app.services.quiz.preprocess", new=AsyncMock(side_effect=lambda t, c: c)), \
         patch("app.services.quiz.LLMClient") as llm_cls:
        llm_cls.return_value.call_json.return_value = {
            "questions": [{"question": "Q1", "answer": "A1"}]
        }

        response = client.post(
            "/ai/quiz",
            json={
                "contents": [
                    {"input_type": "text", "content": "내용 A"},
                    {"input_type": "text", "content": "내용 B"},
                ],
                "quiz_type": "short_answer",
            },
        )

    assert response.status_code == 422
    assert response.json()["error"] == "quiz_generation_failed"


# LLM 응답 항목에 필수 필드(question, answer)가 누락되면 422 quiz_generation_failed.
def test_missing_required_field_returns_422() -> None:
    with patch("app.services.quiz.preprocess", new=AsyncMock(side_effect=lambda t, c: c)), \
         patch("app.services.quiz.LLMClient") as llm_cls:
        llm_cls.return_value.call_json.return_value = {
            "questions": [{"question": "질문만 있고 answer 없음"}]
        }

        response = client.post(
            "/ai/quiz",
            json={
                "contents": [{"input_type": "text", "content": "내용"}],
                "quiz_type": "short_answer",
            },
        )

    assert response.status_code == 422
    assert response.json()["error"] == "quiz_generation_failed"
