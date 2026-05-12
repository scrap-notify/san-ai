from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.til import TilContent


class QuizType(StrEnum):
    short_answer = "short_answer"
    ox = "ox"


class ShortAnswerQuestion(BaseModel):
    question: str = Field(description="질문")
    answer: str = Field(description="정답 (1~3 단어 혹은 짧은 구)")
    explanation: str | None = Field(default=None, description="해설 한 문장. 없으면 null")


class OXQuestion(BaseModel):
    statement: str = Field(description="O/X 판단할 문장")
    is_correct: bool = Field(description="True = O, False = X")
    explanation: str | None = Field(default=None, description="해설 한 문장. 없으면 null")


class QuizRequest(BaseModel):
    contents: list[TilContent] = Field(
        description="퀴즈를 생성할 콘텐츠 목록. 1개 이상 필요. 콘텐츠 1개당 문제 1개가 생성됨",
    )
    quiz_type: QuizType = Field(
        description="퀴즈 유형. short_answer: 단답형, ox: O/X 퀴즈",
        examples=["short_answer"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "contents": [
                        {"input_type": "text", "content": "FastAPI는 Python 기반 비동기 웹 프레임워크로, Pydantic을 활용한 타입 검증을 지원한다."},
                        {"input_type": "text", "content": "uvicorn은 ASGI 서버로, FastAPI 애플리케이션을 구동하는 데 사용된다."},
                    ],
                    "quiz_type": "short_answer",
                },
            ]
        }
    )


class QuizResponse(BaseModel):
    quiz_type: QuizType = Field(description="생성된 퀴즈 유형")
    questions: list[ShortAnswerQuestion | OXQuestion] = Field(
        description="생성된 문제 목록. quiz_type에 따라 항목 타입이 결정됨",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "quiz_type": "short_answer",
                "questions": [
                    {
                        "question": "FastAPI가 타입 검증에 활용하는 라이브러리는?",
                        "answer": "Pydantic",
                        "explanation": "FastAPI는 Pydantic 모델을 통해 요청/응답 데이터의 타입을 자동으로 검증한다.",
                    },
                    {
                        "question": "FastAPI 애플리케이션을 구동하는 ASGI 서버는?",
                        "answer": "uvicorn",
                        "explanation": "uvicorn은 비동기 요청을 처리하는 ASGI 서버로 FastAPI와 함께 사용된다.",
                    },
                ],
            }
        }
    )
