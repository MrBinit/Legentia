# markdown_loader.py

def load_markdown(path: str) -> str:
    """
    Loads the contents of a markdown (.md) file from the given file path.

    Parameters:
        path (str): The path to the markdown file.

    Returns:
        str: The raw text content of the markdown file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_clause_extraction_task(document_text: str) -> str:
    """
    Generates a prompt for the ClauseExtractorAgent to extract key legal clauses
    from the provided document text.

    The agent is instructed to return only the exact text of each clause without
    summaries, interpretations, or extra formatting.

    Parameters:
        document_text (str): The full legal document content in text format.

    Returns:
        str: A formatted prompt string instructing clause extraction.
    """

    return f"""
You are a legal clause extractor.

Your job is to extract the following essential clauses from the legal document.
Return only the exact text of each clause — no summaries, interpretations, or commentary.

Clauses to extract:
- Parties involved
- Effective date and term
- Purpose / Scope
- Payment / Compensation
- Confidentiality / Non-Disclosure
- Termination
- Governing law and jurisdiction
- Liability
- Representations and warranties
- Force majeure
- Dispute resolution
- Assignment
- Amendment / Modification
- Entire agreement
- Severability
- Notices
- Signatures and execution

Document:
{document_text}
"""

def get_risk_analysis_task(extracted_clauses: str) -> str:
    """
    Generates a prompt for the RiskAnalysisAgent to analyze extracted legal clauses
    and identify potential risks based on predefined risk keywords.

    Parameters:
        extracted_clauses (str): The raw text of clauses extracted from the document.

    Returns:
        str: A formatted prompt string instructing risk evaluation in bullet-point form.
    """
    return f"""
You are a legal risk analysis agent.

Analyze the following legal clauses and identify potential risks based on dangerous or vague terms such as:
- Termination
- Penalty
- Indemnify
- Liability
- Compensation
- Damages

Return your analysis in short bullet points.

Clauses:
{extracted_clauses}
"""

def get_summary_task(content: str) -> str:
    """
    Generates a prompt for the SummarizerAgent to summarize the combined legal clauses
    and risk analysis in simple, plain English for a non-lawyer audience.

    Parameters:
        content (str): Combined text of clauses and risk analysis.

    Returns:
        str: A formatted prompt string instructing summarization.
    """
    return f"""
You are a legal summarizer.

Summarize the following legal clauses and risk notes in simple, plain English for a non-lawyer audience. Avoid legal jargon.

Content:
{content}
"""
