"""
Verifier Agent.
Reviews and verifies the Executor's response for quality and completeness.
"""

from agno.agent import Agent

from llm.client import get_model
from llm.prompt import VERIFIER_PROMPT


def create_verifier_agent() -> Agent:
    """
    Create and return the Verifier Agent.

    The Verifier Agent reviews the Executor's output for completeness,
    accuracy, clarity, and correct tool usage.

    Returns:
        A configured Verifier Agent instance.
    """
    return Agent(
        name="Verifier Agent",
        role="Review and verify responses for quality and completeness",
        model=get_model(),
        instructions=VERIFIER_PROMPT,
        markdown=True,
    )
