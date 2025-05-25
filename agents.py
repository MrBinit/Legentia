import asyncio
from autogen_agentchat.agents import AssistantAgent
from model_adapter import get_model_client
from model_prompt.prompt_agents import (
    prompt_ClauseExtractorAgent,
    prompt_RiskAnalysisAgent,
    prompt_SummarizerAgent,
    prompt_TranslationAgent,
)
from markdown_loader import task
from autogen_core.tools import FunctionTool

# Risky terms to trigger the risk agent
RISK_KEYWORDS = ["termination", "penalty", "indemnify", "liability", "compensation", "damages"]


async def main():
    model_client = await get_model_client()

    clause_extractor = AssistantAgent(
        name="ClauseExtractorAgent",
        model_client=model_client,
        system_message=prompt_ClauseExtractorAgent,
    )

    risk_analysis = AssistantAgent(
        name="RiskAnalysisAgent",
        model_client=model_client,
        system_message=prompt_RiskAnalysisAgent,
    )

    summarizer_agent = AssistantAgent(
        name="SummarizerAgent",
        model_client=model_client,
        system_message=prompt_SummarizerAgent,
    )

    translate_tool = FunctionTool(
        translate_to_nepali,
        description="Translate English legal text to Nepali while preserving formal tone."
    )
    translation_agent = AssistantAgent(
        name= "TranslationAgent",
        model_client=model_client,
        system_message=prompt_TranslationAgent,


    )

    # Run ClauseExtractor
    clause_result = await clause_extractor.run(task=task)
    clause_text = clause_result.messages[-1].content

    #Check for risky terms
    risky = any(term.lower() in clause_text.lower() for term in RISK_KEYWORDS)

    #If risky → run RiskAnalysisAgent
    if risky:
        risk_result = await risk_analysis.run(task=clause_text)
        risk_text = risk_result.messages[-1].content
        print("\n--- Risk Analysis ---\n", risk_text)
    else:
        risk_text = ""

    # Run SummarizerAgent
    summary_input = clause_text + "\n" + risk_text
    summary_result = await summarizer_agent.run(task=summary_input)
    summary_text = summary_result.messages[-1].content
    print("\n--- Summary ---\n", summary_text)


if __name__ == "__main__":
    asyncio.run(main())
