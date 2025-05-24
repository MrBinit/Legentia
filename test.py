import asyncio
from autogen_agentchat.agents import AssistantAgent
from model_adapter import get_model_client
from model_prompt.clause_extractor import prompt

# Step 1: Load the Markdown document
def load_markdown(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

async def main():
    model_client = await get_model_client()

    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        system_message=prompt,  # e.g., "You are a legal clause extractor..."
    )

    # Step 2: Load the document
    markdown_doc = load_markdown("/home/binit/Legentia/legal_document_parsed/pdf_document/pdf_output_1.md")

    # Step 3: Send the doc as a task
    task = f"""
Extract the following clauses from this contract:
- Termination
- Payment
- Confidentiality
- Liability

Document:
{markdown_doc}
    """
    result = await agent.run(task=task)

    print("🔹 Agent Response:")
    print(result.messages[-1].content)

if __name__ == "__main__":
    asyncio.run(main())
