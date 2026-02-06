"""
LLM Client module.
Provides configured Groq model instances for use across all agents.
"""

import os
from dotenv import load_dotenv
from agno.models.groq import Groq

load_dotenv()


def get_model(model_id: str = "llama-3.3-70b-versatile") -> Groq:
    """
    Returns a configured Groq model instance for general use.

    Args:
        model_id: The Groq model identifier to use.

    Returns:
        A configured Groq model instance.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is not set. "
            "Get your key from https://console.groq.com/keys"
        )
    return Groq(id=model_id, api_key=api_key)


def get_tool_model() -> Groq:
    """
    Returns a Groq model specifically optimized for tool calling.

    Uses qwen/qwen3-32b which has excellent tool calling support.

    Returns:
        A configured Groq model for tool calling.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is not set. "
            "Get your key from https://console.groq.com/keys"
        )
    return Groq(id="qwen/qwen3-32b", api_key=api_key)
