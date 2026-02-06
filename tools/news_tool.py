"""News Tool - Fetches latest news using NewsData.io API with retry logic."""

import os
from tools.retry_utils import safe_api_call
from tools.cache_manager import cache_manager


def _get_news_uncached(topic: str) -> str:
    """Internal function to get news without caching."""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "Error: NEWS_API_KEY not set."

    response, error = safe_api_call(
        "https://newsdata.io/api/1/latest",
        params={"apikey": api_key, "q": topic, "language": "en"},
        timeout=15
    )
    
    if error:
        return f"Error fetching news for '{topic}': {error}"
    if response.status_code == 401:
        return "Error: Invalid NewsData.io API key."

    try:
        data = response.json()
        if data.get("status") != "success":
            return f"NewsData.io error: {data.get('results', {}).get('message', 'Unknown')}"

        articles = data.get("results", [])
        if not articles:
            return f"No news found for '{topic}'."

        headlines = []
        for i, a in enumerate(articles[:5], 1):
            desc = a.get("description", "")
            if desc and len(desc) > 120:
                desc = desc[:120] + "..."
            headlines.append(
                f"  {i}. {a.get('title', 'No title')}\n"
                f"     Source: {a.get('source_id', '?')} | {a.get('pubDate', '?')}"
                + (f"\n     Summary: {desc}" if desc else "")
            )
        return f"Top News for '{topic}':\n" + "\n".join(headlines)
    except Exception as e:
        return f"Error parsing news for '{topic}': {e}"


def get_news(topic: str) -> str:
    """Get latest news headlines on a topic with caching and retry on API failure."""
    return cache_manager.cache_call(_get_news_uncached, "news", topic)
