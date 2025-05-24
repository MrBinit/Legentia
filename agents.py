# agent_builder.py
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_adapter import get_model_client
from model_prompt.prompt_agents import prompt_ClauseExtractorAgent, prompt_RiskAnalysisAgent
from markdown_loader import task
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import SelectorGroupChat

async def main():
    model_client = await get_model_client()

    clause_extractor  = AssistantAgent(
        name="ClauseExtractorAgent",
        model_client=model_client,
        system_message=prompt_ClauseExtractorAgent,
    )


    risk_analysis = AssistantAgent(
        name="RiskAnalysisAgent",
        model_client=model_client,
        system_message=prompt_RiskAnalysisAgent,
    )
    # risk_analysis = AssistantAgent(
    #     name="SummarizerAgent",
    #     model_client=model_client,
    #     system_message=prompt_RiskAnalysisAgent,
    # )

    team = SelectorGroupChat([clause_extractor, risk_analysis], model_client= model_client)
    stream = team.run_stream(task=task)
    async for message in stream:
        print(message)



if __name__ == "__main__":
    asyncio.run(main())


