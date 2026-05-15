import json
import re

from langchain_core.messages import HumanMessage

from app.core.exceptions import AIProcessingError
from app.llms.openai import create_openai_chat_model

# LLMClient는 OpenAI API를 호출하여 텍스트 및 이미지 응답을 처리하는 클래스입니다.
class LLMClient:
    def __init__(self) -> None:
        self._model = create_openai_chat_model()

    # prompt을 입력받아 LLM에서 텍스트 응답을 반환하는 메서드입니다. 예외 발생 시 AIProcessingError로 래핑하여 전달합니다.
    def call(self, prompt: str, error_code: str) -> str:
        try:
            response = self._model.invoke(prompt)
            return response.content
        except Exception as e:
            raise AIProcessingError(code=error_code, message=str(e)) from e

    # prompt을 입력받아 LLM에서 JSON 응답을 반환하는 메서드입니다. 응답에서 코드 블록을 제거하고 JSON으로 파싱합니다. 예외 발생 시 AIProcessingError로 래핑하여 전달합니다.
    def call_json(self, prompt: str, error_code: str) -> dict:
        raw = self.call(prompt, error_code)
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise AIProcessingError(code=error_code, message=f"LLM 응답 JSON 파싱 실패: {e}") from e

    async def acall(self, prompt: str, error_code: str) -> str:
        try:
            response = await self._model.ainvoke(prompt)
            return response.content
        except Exception as e:
            raise AIProcessingError(code=error_code, message=str(e)) from e

    async def acall_json(self, prompt: str, error_code: str) -> dict:
        raw = await self.acall(prompt, error_code)
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise AIProcessingError(code=error_code, message=f"LLM 응답 JSON 파싱 실패: {e}") from e

    # prompt과 이미지 URL을 입력받아 LLM에서 텍스트 응답을 반환하는 메서드입니다. 예외 발생 시 AIProcessingError로 래핑하여 전달합니다.
    def call_with_image(self, prompt: str, image_url: str, error_code: str) -> str:
        try:
            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ])
            response = self._model.invoke([message])
            return response.content
        except Exception as e:
            raise AIProcessingError(code=error_code, message=str(e)) from e
