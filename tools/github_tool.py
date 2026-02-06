"""
GitHub Tool - Fetch GitHub user profiles, search users/repos, and get repository info.
"""

import os
import requests


def _get_headers() -> dict:
    """Get headers for GitHub API requests."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    api_key = os.getenv("GITHUB_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _fetch_readme(owner: str, repo: str, max_length: int = 1500) -> str | None:
    """
    Fetch the decoded README content for a repository.

    Args:
        owner: The repository owner.
        repo: The repository name.
        max_length: Maximum characters to include (default 1500).

    Returns:
        The README text (truncated if needed), or None if unavailable.
    """
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        response = requests.get(url, headers={**_get_headers(), "Accept": "application/vnd.github.v3.raw"}, timeout=10)
        if response.status_code != 200:
            return None
        content = response.text.strip()
        if not content:
            return None
        if len(content) > max_length:
            content = content[:max_length] + "\n... (truncated)"
        return content
    except requests.RequestException:
        return None


def get_github_user(username: str) -> str:
    """
    Get the GitHub profile information for a given username.

    Args:
        username: The GitHub username to look up.

    Returns:
        A string with the GitHub user's profile information.
    """
    try:
        url = f"https://api.github.com/users/{username}"
        response = requests.get(url, headers=_get_headers(), timeout=10)

        if response.status_code == 404:
            return f"GitHub user '{username}' not found."

        response.raise_for_status()
        data = response.json()

        name = data.get("name", "N/A")
        bio = data.get("bio", "N/A")
        public_repos = data.get("public_repos", 0)
        followers = data.get("followers", 0)
        following = data.get("following", 0)
        location = data.get("location", "N/A")
        company = data.get("company", "N/A")
        blog = data.get("blog", "N/A")
        profile_url = data.get("html_url", "N/A")
        created_at = data.get("created_at", "N/A")

        profile = (
            f"GitHub Profile for @{username}:\n"
            f"  Name        : {name}\n"
            f"  Bio         : {bio}\n"
            f"  Company     : {company}\n"
            f"  Location    : {location}\n"
            f"  Public Repos: {public_repos}\n"
            f"  Followers   : {followers}\n"
            f"  Following   : {following}\n"
            f"  Blog/Website: {blog}\n"
            f"  Profile URL : {profile_url}\n"
            f"  Joined      : {created_at}"
        )

        # Enrich with the user's profile README (username/username repo)
        readme = _fetch_readme(username, username)
        if readme:
            profile += f"\n\n--- Profile README ---\n{readme}"

        return profile
    except requests.RequestException as e:
        return f"Error fetching GitHub profile for '{username}': {e}"


def search_github_users(query: str, max_results: int = 5) -> str:
    """
    Search for GitHub users matching a query.

    Args:
        query: The search query string (e.g., "machine learning", "python developer").
        max_results: Maximum number of results to return (default 5, max 10).

    Returns:
        A string with the list of matching GitHub users.
    """
    try:
        max_results = min(max(1, max_results), 10)
        url = f"https://api.github.com/search/users?q={query}&per_page={max_results}"
        response = requests.get(url, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()

        total_count = data.get("total_count", 0)
        items = data.get("items", [])

        if not items:
            return f"No GitHub users found matching '{query}'."

        result_lines = [f"GitHub User Search Results for '{query}' ({total_count} total matches):"]
        for i, user in enumerate(items, 1):
            login = user.get("login", "N/A")
            profile_url = user.get("html_url", "N/A")
            result_lines.append(f"  {i}. @{login} - {profile_url}")

        return "\n".join(result_lines)
    except requests.RequestException as e:
        return f"Error searching GitHub users for '{query}': {e}"


def search_github_repos(query: str, max_results: int = 5) -> str:
    """
    Search for GitHub repositories matching a query.

    Args:
        query: The search query string (e.g., "react framework", "python web scraping").
        max_results: Maximum number of results to return (default 5, max 10).

    Returns:
        A string with the list of matching GitHub repositories.
    """
    try:
        max_results = min(max(1, max_results), 10)
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={max_results}"
        response = requests.get(url, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()

        total_count = data.get("total_count", 0)
        items = data.get("items", [])

        if not items:
            return f"No GitHub repositories found matching '{query}'."

        result_lines = [f"GitHub Repository Search Results for '{query}' ({total_count} total matches):"]
        for i, repo in enumerate(items, 1):
            full_name = repo.get("full_name", "N/A")
            description = repo.get("description", "No description")
            stars = repo.get("stargazers_count", 0)
            language = repo.get("language", "N/A")
            url = repo.get("html_url", "N/A")
            result_lines.append(f"  {i}. {full_name}")
            result_lines.append(f"     ⭐ {stars:,} | 🔤 {language}")
            result_lines.append(f"     📝 {description[:100]}{'...' if description and len(description) > 100 else ''}")
            result_lines.append(f"     🔗 {url}")

        return "\n".join(result_lines)
    except requests.RequestException as e:
        return f"Error searching GitHub repos for '{query}': {e}"


def get_github_repo(owner: str, repo: str) -> str:
    """
    Get detailed information about a specific GitHub repository.

    Args:
        owner: The repository owner's username (e.g., "facebook").
        repo: The repository name (e.g., "react").

    Returns:
        A string with detailed repository information including stars, forks, description, etc.
    """
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(url, headers=_get_headers(), timeout=10)

        if response.status_code == 404:
            return f"Repository '{owner}/{repo}' not found."

        response.raise_for_status()
        data = response.json()

        full_name = data.get("full_name", "N/A")
        description = data.get("description", "No description")
        stars = data.get("stargazers_count", 0)
        forks = data.get("forks_count", 0)
        watchers = data.get("watchers_count", 0)
        open_issues = data.get("open_issues_count", 0)
        language = data.get("language", "N/A")
        license_info = data.get("license")
        license_name = license_info.get("name", "N/A") if license_info else "N/A"
        topics = data.get("topics", [])
        html_url = data.get("html_url", "N/A")
        created_at = data.get("created_at", "N/A")
        updated_at = data.get("updated_at", "N/A")
        default_branch = data.get("default_branch", "N/A")

        repo_info = (
            f"GitHub Repository: {full_name}\n"
            f"  Description   : {description}\n"
            f"  ⭐ Stars      : {stars:,}\n"
            f"  🍴 Forks      : {forks:,}\n"
            f"  👀 Watchers   : {watchers:,}\n"
            f"  🐛 Open Issues: {open_issues:,}\n"
            f"  🔤 Language   : {language}\n"
            f"  📜 License    : {license_name}\n"
            f"  🏷️ Topics     : {', '.join(topics) if topics else 'None'}\n"
            f"  🌿 Default Br.: {default_branch}\n"
            f"  📅 Created    : {created_at}\n"
            f"  🔄 Updated    : {updated_at}\n"
            f"  🔗 URL        : {html_url}"
        )

        # Enrich with the repository's README
        readme = _fetch_readme(owner, repo)
        if readme:
            repo_info += f"\n\n--- Repository README ---\n{readme}"

        return repo_info
    except requests.RequestException as e:
        return f"Error fetching repository '{owner}/{repo}': {e}"
