import asyncio
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion, OllamaChatPromptExecutionSettings
from semantic_kernel.memory.null_memory import NullMemory
from dotenv import load_dotenv
import os

load_dotenv()

async def get_model_client():
    """This is the model from ollama which would be use in a agent."""
    sk_client = OllamaChatCompletion(
        ai_model_id="llama3.2-vision:11b",
    )
    ollama_settings = OllamaChatPromptExecutionSettings(
        options={"temperature": 0.1},
    )

    model_client = SKChatCompletionAdapter(
        sk_client, kernel=Kernel(memory=NullMemory()), prompt_settings=ollama_settings
    )
    return model_client