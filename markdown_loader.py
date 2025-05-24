def load_markdown(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


markdown_doc = load_markdown("/home/binit/Legentia/legal_document_parsed/pdf_document/pdf_output_1.md")

task = f"""
You are a legal clause extractor. Your job is to extract the following essential clauses from the given legal document. Return only the text of each clause exactly as it appears in the document. Do not summarize or add commentary.

Extract the following clauses from this contract:
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

After extraction, check the clauses for any of the following high-risk legal terms: "termination", "penalty", "indemnify", "liability", "compensation", "damages".
If such terms are found, **trigger the RiskAnalysisAgent** to perform a risk assessment based on those clauses.

Document:
{markdown_doc}
"""
