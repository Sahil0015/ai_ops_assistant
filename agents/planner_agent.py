"""
Planner Agent.
Analyzes user queries and creates a step-by-step execution plan.
"""

from agno.agent import Agent

from llm.client import get_model
from llm.prompt import PLANNER_PROMPT


def create_planner_agent() -> Agent:
    """
    Create and return the Planner Agent.

    The Planner Agent analyzes the user's query and creates a step-by-step plan
    identifying which tools are needed.

    Returns:
        A configured Planner Agent instance.
    """
    return Agent(
        name="Planner Agent",
        role="Analyze user queries and create step-by-step execution plans",
        model=get_model(),
        instructions=PLANNER_PROMPT,
        markdown=True,
    )
