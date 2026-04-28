import json
import re

from app.core.exceptions import AIProcessingError
from app.llms.openai import create_openai_chat_model

# llm client는 LLM과의 호출과 응답 처리를 담당
class LLMClient:
    def __init__(self) -> None:
        self._model = create_openai_chat_model()

    # prompt을 LLM에 보내고 응답을 받는 메서드
    def call(self, prompt: str, error_code: str) -> str:
        try:
            response = self._model.invoke(prompt)
            return response.content
        # LLM 호출이나 응답 처리 중 발생하는 모든 예외를 AIProcessingError로 래핑하여 상위로 전달
        except Exception as e:
            raise AIProcessingError(code=error_code, message=str(e)) from e

    # LLM 응답이 JSON 형식일 때, 이를 파싱하여 dict로 반환하는 메서드
    def call_json(self, prompt: str, error_code: str) -> dict:
        # LLM 응답에서 코드 블록으로 감싸진 JSON 부분을 추출하여 파싱
        raw = self.call(prompt, error_code)
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        try:
            return json.loads(cleaned)
        # JSON 파싱 중 발생하는 예외를 AIProcessingError로 래핑하여 상위로 전달
        except json.JSONDecodeError as e:
            raise AIProcessingError(code=error_code, message=f"LLM 응답 JSON 파싱 실패: {e}") from e
