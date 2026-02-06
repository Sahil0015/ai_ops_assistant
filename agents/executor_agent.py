"""
Executor Agent.
Executes the plan created by the Planner Agent using available tools.
"""

from agno.agent import Agent

from llm.client import get_tool_model
from llm.prompt import EXECUTOR_PROMPT
from tools.weather_tool import get_weather
from tools.news_tool import get_news
from tools.github_tool import (
    get_github_user,
    search_github_users,
    search_github_repos,
    get_github_repo,
)


def create_executor_agent() -> Agent:
    """
    Create and return the Executor Agent.

    The Executor Agent has access to weather, news, and GitHub tools.
    It executes the plan by calling the appropriate tools and combining results.
    Uses a tool-optimized model for reliable function calling.

    Returns:
        A configured Executor Agent instance.
    """
    return Agent(
        name="Executor Agent",
        role="Execute plans by calling tools and gathering information",
        model=get_tool_model(),
        instructions=EXECUTOR_PROMPT,
        tools=[
            get_weather,
            get_news,
            get_github_user,
            search_github_users,
            search_github_repos,
            get_github_repo,
        ],
        markdown=True,
    )
