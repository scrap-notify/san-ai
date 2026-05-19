from app.schemas.quiz import QuizType

SHORT_ANSWER_QUIZ_PROMPT = """
너는 학습 콘텐츠를 바탕으로 단답형 퀴즈를 출제하는 선생님이다.

입력은 `---`으로 구분된 콘텐츠 섹션 {num_questions}개로 주어진다.

출제 기준:
- 각 섹션에서 정확히 1문제씩 출제한다. 총 {num_questions}개의 문제를 만든다.
- 해당 섹션에서 가장 중요한 개념이나 원리를 묻는 질문을 만든다. 독자가 이 콘텐츠에서 반드시 이해해야 할 핵심이 무엇인지 스스로에게 물어보고 선택한다.
- URL, 경로, 포트 번호, 명령어, 파일명 등 지엽적인 사실은 출제하지 않는다.
- 정답은 누가 봐도 동일하게 쓸 수 있는 고유한 용어나 단어 하나여야 한다. "A와 B", "X 및 Y" 처럼 복수 정답을 요구하거나 표현 방식에 따라 달라질 수 있는 구문은 정답으로 쓰지 않는다.
- 질문·정답·해설은 반드시 한국어로 작성한다. 단, OpenAPI·Docker 등 고유 명사나 기술 용어는 원문 표기를 그대로 사용한다.
- 해설은 1문장으로 작성한다.

출력 형식:
- 응답은 반드시 아래 구조의 JSON 객체만 출력한다. 다른 텍스트나 설명은 절대 포함하지 않는다.
  {{"questions": [{{"question": "...", "answer": "...", "explanation": "..."}}, ...]}}

[입력 콘텐츠]
{content}
"""

OX_QUIZ_PROMPT = """
너는 학습 콘텐츠를 바탕으로 O/X 퀴즈를 출제하는 선생님이다.

입력은 `---`으로 구분된 콘텐츠 섹션 {num_questions}개로 주어진다.

출제 기준:
- 각 섹션에서 정확히 1문제씩 출제한다. 총 {num_questions}개의 문제를 만든다.
- 해당 섹션에서 가장 중요한 개념이나 원리에 대해 참/거짓을 판단할 수 있는 명확한 문장을 만든다.
- URL, 경로, 포트 번호, 명령어, 파일명 등 지엽적인 사실은 출제하지 않는다.
- {ox_instruction}
- 문장·해설은 반드시 한국어로 작성한다. 단, OpenAPI·Docker 등 고유 명사나 기술 용어는 원문 표기를 그대로 사용한다.
- 해설은 1문장으로 작성한다.

출력 형식:
- 응답은 반드시 아래 구조의 JSON 객체만 출력한다. 다른 텍스트나 설명은 절대 포함하지 않는다.
  {{"questions": [{{"statement": "...", "explanation": "..."}}, ...]}}

[입력 콘텐츠]
{content}
"""

_OX_TRUE_INSTRUCTION = "이 문장은 반드시 참(O)이어야 한다. 콘텐츠의 핵심 내용을 정확하게 서술하는 문장을 만들어라."
_OX_FALSE_INSTRUCTION = "이 문장은 반드시 거짓(X)이어야 한다. 콘텐츠의 핵심 내용에서 개념, 관계, 순서 등을 미세하게 바꿔 틀린 문장을 만들어라. 너무 뻔하게 틀리지 않도록 한다."


def get_quiz_prompt(quiz_type: QuizType, content: str, num_questions: int, is_correct: bool | None = None) -> str:
    if quiz_type == QuizType.short_answer:
        return SHORT_ANSWER_QUIZ_PROMPT.format(content=content, num_questions=num_questions)
    if quiz_type == QuizType.ox:
        ox_instruction = _OX_TRUE_INSTRUCTION if is_correct else _OX_FALSE_INSTRUCTION
        return OX_QUIZ_PROMPT.format(content=content, num_questions=num_questions, ox_instruction=ox_instruction)
    raise ValueError(f"Unsupported quiz_type: {quiz_type}")
