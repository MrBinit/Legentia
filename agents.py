# agent_builder.py
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_adapter import get_model_client
from model_prompt.clause_extractor import prompt


async def main():
    model_client = await get_model_client()

    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        system_message=prompt,
    )
    result = await agent.run(task="What is the capital of France?")
    print("Agent Response:")
    print(result.messages[-1].content)

if __name__ == "__main__":
    asyncio.run(main())
