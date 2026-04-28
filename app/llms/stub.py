"""임시 stub LLM/embedding 팩토리.

실제 공통 LLM/embedding 모듈이 다른 브랜치에서 작업 중이며,
해당 모듈이 머지되면 이 파일을 제거하고 service의 import만 교체한다.
"""

from langchain_core.embeddings import Embeddings
from langchain_core.embeddings.fake import DeterministicFakeEmbedding
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel


_FIXED_TIL_MARKDOWN = """# TIL

## React 상태 관리

- 상태는 컴포넌트의 데이터를 시간에 따라 관리한다.

## 클로저

- 함수가 선언될 당시의 외부 변수를 기억한다.
"""


def create_stub_chat_model() -> BaseChatModel:
    return FakeListChatModel(responses=[_FIXED_TIL_MARKDOWN])


def create_stub_embedding_model() -> Embeddings:
    # OpenAI text-embedding-3-small과 동일한 차원 (실제 모듈 교체 시 응답 형태 일치)
    return DeterministicFakeEmbedding(size=1536)
