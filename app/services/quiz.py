import asyncio

from app.core.exceptions import AIProcessingError, ContentValidationError
from app.llms import LLMClient
from app.prompts.quiz import get_quiz_prompt
from app.schemas.quiz import OXQuestion, QuizRequest, QuizResponse, QuizType, ShortAnswerQuestion
from app.services.preprocessor import preprocess

_BLOCK_SEPARATOR = "\n\n---\n\n"
_SHORT_ANSWER_REQUIRED_KEYS = {"question", "answer"}
_OX_REQUIRED_KEYS = {"statement", "is_correct"}


async def generate_quiz(request: QuizRequest) -> QuizResponse:
    if not request.contents:
        raise ContentValidationError(code="missing_contents", message="contents는 비어있을 수 없습니다.")

    preprocessed = await asyncio.gather(
        *(preprocess(item.input_type, item.content) for item in request.contents)
    )
    num_questions = len(request.contents)
    joined = _BLOCK_SEPARATOR.join(preprocessed)

    prompt = get_quiz_prompt(request.quiz_type, joined, num_questions)
    result = LLMClient().call_json(prompt=prompt, error_code="quiz_generation_failed")

    raw_questions = result.get("questions")
    if not isinstance(raw_questions, list) or len(raw_questions) != num_questions:
        actual = len(raw_questions) if isinstance(raw_questions, list) else "없음"
        raise AIProcessingError(
            code="quiz_generation_failed",
            message=f"LLM 응답의 questions 배열이 올바르지 않습니다. 기대: {num_questions}개, 실제: {actual}",
        )

    questions: list[ShortAnswerQuestion | OXQuestion] = []
    if request.quiz_type == QuizType.short_answer:
        for item in raw_questions:
            if not _SHORT_ANSWER_REQUIRED_KEYS.issubset(item):
                missing = _SHORT_ANSWER_REQUIRED_KEYS - item.keys()
                raise AIProcessingError(
                    code="quiz_generation_failed",
                    message=f"LLM 응답 문제 항목에 필수 필드 누락: {missing}",
                )
            questions.append(ShortAnswerQuestion(
                question=item["question"],
                answer=item["answer"],
                explanation=item.get("explanation"),
            ))
    elif request.quiz_type == QuizType.ox:
        for item in raw_questions:
            if not _OX_REQUIRED_KEYS.issubset(item):
                missing = _OX_REQUIRED_KEYS - item.keys()
                raise AIProcessingError(
                    code="quiz_generation_failed",
                    message=f"LLM 응답 문제 항목에 필수 필드 누락: {missing}",
                )
            questions.append(OXQuestion(
                statement=item["statement"],
                is_correct=item["is_correct"],
                explanation=item.get("explanation"),
            ))

    return QuizResponse(quiz_type=request.quiz_type, questions=questions)
