"""
Responder Agent.
Formats and presents the final polished response to the user.
"""

from agno.agent import Agent

from llm.client import get_model
from llm.prompt import RESPONDER_PROMPT


def create_responder_agent() -> Agent:
    """
    Create and return the Responder Agent.

    The Responder Agent takes verified responses and formats them
    into a polished, user-friendly final answer.

    Returns:
        A configured Responder Agent instance.
    """
    return Agent(
        name="Responder Agent",
        role="Format and present the final response to the user",
        model=get_model(),
        instructions=RESPONDER_PROMPT,
        markdown=True,
    )
