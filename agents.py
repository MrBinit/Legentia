import asyncio
from autogen_agentchat.agents import AssistantAgent
from model_adapter import get_model_client
from model_prompt.prompt_agents import (
    prompt_ClauseExtractorAgent,
    prompt_RiskAnalysisAgent,
    prompt_SummarizerAgent,
    prompt_TranslationAgent,
)
from markdown_loader import (clause_extraction_task,
                            get_risk_analysis_task,
                            get_summary_task,)
from autogen_core.tools import FunctionTool
from legal_risky_keywords import RISK_KEYWORDS
from translation_model.pipeline import run_translation_pipeline


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
        run_translation_pipeline,
        description="Translate English legal text to Nepali while preserving formal tone."
    )
    translation_agent = AssistantAgent(
        name= "TranslationAgent",
        model_client=model_client,
        system_message=prompt_TranslationAgent,

    )

    # Run ClauseExtractor
    clause_result = await clause_extractor.run(task=clause_extraction_task)
    clause_text = clause_result.messages[-1].content

    #Check for risky terms
    risky = any(term.lower() in clause_text.lower() for term in RISK_KEYWORDS)

    #If risky → run RiskAnalysisAgent
    if risky:
        risk_task = get_risk_analysis_task(clause_text)
        risk_result = await risk_analysis.run(task=risk_task)
        risk_text = risk_result.messages[-1].content
        print("\n--- Risk Analysis ---\n", risk_text)
    else:
        risk_text = ""

    # Run SummarizerAgent
    summary_task = get_summary_task(clause_text + "\n" + risk_text)
    summary_result = await summarizer_agent.run(task=summary_task)
    summary_text = summary_result.messages[-1].content


    # #Run translation for nepali.
    language = "english"
    if language.lower() == "nepali":
        print("\n--- Translating Summary to Nepali ---\n")
        translation_result = await translation_agent.run(task=summary_text)
        translated_summary = translation_result.messages[-1].content
        print("\n--- Translated Summary (Nepali) ---\n", translated_summary)
    else:
        print("\n--- Final Summary (English) ---\n", summary_text)


if __name__ == "__main__":
    asyncio.run(main())
