import asyncio
from autogen_agentchat.agents import AssistantAgent
from model_adapter import get_model_client
from model_prompt.prompt_agents import (
    prompt_ClauseExtractorAgent,
    prompt_RiskAnalysisAgent,
    prompt_SummarizerAgent,
    prompt_TranslationAgent,
)
from markdown_loader import (get_clause_extraction_task,
                            get_risk_analysis_task,
                            get_summary_task,)
from autogen_core.tools import FunctionTool
from legal_risky_keywords import RISK_KEYWORDS
from translation_model.pipeline import run_translation_pipeline
from parse import parse_document

async def process_legal_document(document_path: str, language= str) -> str:
    """
    Processes a legal document through a multi-agent pipeline to extract clauses, analyze risks,
    summarize the content, and optionally translate the final output based on the desired language.

    Steps:
    1. Parses the document and normalizes its text (e.g., translates Nepali to English if detected).
    2. Extracts essential legal clauses using ClauseExtractorAgent.
    3. Checks for risk-related keywords; if found, triggers RiskAnalysisAgent.
    4. Summarizes the combined clause and risk content using SummarizerAgent.
    5. If the desired output language is 'nepali', translates the summary using TranslationAgent.

    Parameters:
        document_path (str): The file path to the legal document (PDF, DOCX, image, etc.).
        language (str): The desired output language ("english" or "nepali"). Defaults to "english".

    Returns:
        str: The final summarized content, optionally translated to Nepali.
    """

    normalized_text = parse_document(document_path)

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
    translation_agent = AssistantAgent(
        name= "TranslationAgent",
        model_client=model_client,
        system_message=prompt_TranslationAgent,

    )

    # Run ClauseExtractor
    clause_task_input = get_clause_extraction_task(normalized_text)
    clause_extraction_result = await clause_extractor.run(task=clause_task_input)
    clause_text = clause_extraction_result.messages[-1].content

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


    #Run translation for nepali.
    if language.lower() == "nepali":
        print("\n--- Translating Summary to Nepali ---\n")
        translation_result = await translation_agent.run(task=summary_text)
        translated_summary = translation_result.messages[-1].content
        return translated_summary
    else:
        return summary_text
