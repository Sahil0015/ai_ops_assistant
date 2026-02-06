"""
News Tool.
Fetches latest news headlines using the NewsData.io API.
"""

import os
import requests


def get_news(topic: str) -> str:
    """
    Get the latest news headlines on a given topic using NewsData.io.

    Args:
        topic: The topic to search news for.

    Returns:
        A string with the latest news headlines on the topic.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "Error: NEWS_API_KEY environment variable is not set."

    try:
        url = "https://newsdata.io/api/1/latest"
        params = {
            "apikey": api_key,
            "q": topic,
            "language": "en",
        }
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 401:
            return "Error: Invalid NewsData.io API key."

        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            msg = data.get("results", {}).get("message", "Unknown error")
            return f"NewsData.io error: {msg}"

        articles = data.get("results", [])
        if not articles:
            return f"No news articles found for '{topic}'."

        headlines = []
        for i, article in enumerate(articles[:5], 1):
            title = article.get("title", "No title")
            source = article.get("source_id", "Unknown source")
            pub_date = article.get("pubDate", "Unknown date")
            link = article.get("link", "")
            description = article.get("description", "")
            if description and len(description) > 120:
                description = description[:120] + "..."
            headlines.append(
                f"  {i}. {title}\n"
                f"     Source: {source} | Date: {pub_date}"
                + (f"\n     Summary: {description}" if description else "")
            )

        return f"Top News for '{topic}':\n" + "\n".join(headlines)

    except requests.RequestException as e:
        return f"Error fetching news for '{topic}': {e}"
    except Exception as e:
        return f"Error parsing news for '{topic}': {e}"
