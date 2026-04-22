import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


def main() -> None:
    load_dotenv()

    model = ChatOpenAI(
        model="gpt-5.2",
        base_url=os.getenv("OPENAI_BASE_URL"),
    )

    agent = create_agent(
        model=model,
        tools=[get_weather],
        system_prompt="You are a helpful assistant",
    )

    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": "What's the weather in San Francisco?"}
            ]
        }
    )
    print(result["messages"][-1].content_blocks)


if __name__ == "__main__":
    main()
