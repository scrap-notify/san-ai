from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from app.prompts.til import til_prompt


def build_til_chain(model: BaseChatModel) -> Runnable:
    return til_prompt | model | StrOutputParser()
