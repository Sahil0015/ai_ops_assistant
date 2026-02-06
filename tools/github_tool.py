"""
GitHub Tool - Fetch GitHub user profiles, search users/repos, and get repository info.
"""

import os
from tools.retry_utils import safe_api_call
from tools.cache_manager import cache_manager


def _get_headers() -> dict:
    """Get headers for GitHub API requests."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    api_key = os.getenv("GITHUB_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _fetch_readme(owner: str, repo: str, max_length: int = 1500) -> str | None:
    """Fetch the decoded README content for a repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {**_get_headers(), "Accept": "application/vnd.github.v3.raw"}
    response, error = safe_api_call(url, headers=headers, max_retries=2)
    if error or not response:
        return None
    content = response.text.strip()
    if not content:
        return None
    if len(content) > max_length:
        content = content[:max_length] + "\n... (truncated)"
    return content


def _get_github_user_uncached(username: str) -> str:
    """Internal function to get GitHub user without caching."""
    url = f"https://api.github.com/users/{username}"
    response, error = safe_api_call(url, headers=_get_headers())
    
    if error:
        return f"Error fetching GitHub profile for '{username}': {error}"
    if response.status_code == 404:
        return f"GitHub user '{username}' not found."
    
    data = response.json()
    profile = (
        f"GitHub Profile for @{username}:\n"
        f"  Name        : {data.get('name', 'N/A')}\n"
        f"  Bio         : {data.get('bio', 'N/A')}\n"
        f"  Company     : {data.get('company', 'N/A')}\n"
        f"  Location    : {data.get('location', 'N/A')}\n"
        f"  Public Repos: {data.get('public_repos', 0)}\n"
        f"  Followers   : {data.get('followers', 0)}\n"
        f"  Following   : {data.get('following', 0)}\n"
        f"  Blog/Website: {data.get('blog', 'N/A')}\n"
        f"  Profile URL : {data.get('html_url', 'N/A')}\n"
        f"  Joined      : {data.get('created_at', 'N/A')}"
    )
    readme = _fetch_readme(username, username)
    if readme:
        profile += f"\n\n--- Profile README ---\n{readme}"
    return profile


def get_github_user(username: str) -> str:
    """Get the GitHub profile information for a given username with caching."""
    return cache_manager.cache_call(_get_github_user_uncached, "github", username)


def _search_github_users_uncached(query: str, max_results: int = 5) -> str:
    """Internal function to search GitHub users without caching."""
    max_results = min(max(1, max_results), 10)
    url = f"https://api.github.com/search/users?q={query}&per_page={max_results}"
    response, error = safe_api_call(url, headers=_get_headers())
    
    if error:
        return f"Error searching GitHub users for '{query}': {error}"
    
    data = response.json()
    items = data.get("items", [])
    if not items:
        return f"No GitHub users found matching '{query}'."
    
    result_lines = [f"GitHub User Search Results for '{query}' ({data.get('total_count', 0)} total matches):"]
    for i, user in enumerate(items, 1):
        result_lines.append(f"  {i}. @{user.get('login', 'N/A')} - {user.get('html_url', 'N/A')}")
    return "\n".join(result_lines)


def search_github_users(query: str, max_results: int = 5) -> str:
    """Search for GitHub users matching a query with caching."""
    return cache_manager.cache_call(_search_github_users_uncached, "github", query, max_results)


def _search_github_repos_uncached(query: str, max_results: int = 5) -> str:
    """Internal function to search GitHub repos without caching."""
    max_results = min(max(1, max_results), 10)
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={max_results}"
    response, error = safe_api_call(url, headers=_get_headers())
    
    if error:
        return f"Error searching GitHub repos for '{query}': {error}"
    
    data = response.json()
    items = data.get("items", [])
    if not items:
        return f"No GitHub repositories found matching '{query}'."
    
    result_lines = [f"GitHub Repository Search Results for '{query}' ({data.get('total_count', 0)} total matches):"]
    for i, repo in enumerate(items, 1):
        desc = repo.get("description", "No description") or "No description"
        result_lines.append(f"  {i}. {repo.get('full_name', 'N/A')}")
        result_lines.append(f"     ⭐ {repo.get('stargazers_count', 0):,} | 🔤 {repo.get('language', 'N/A')}")
        result_lines.append(f"     📝 {desc[:100]}{'...' if len(desc) > 100 else ''}")
        result_lines.append(f"     🔗 {repo.get('html_url', 'N/A')}")
    return "\n".join(result_lines)


def search_github_repos(query: str, max_results: int = 5) -> str:
    """Search for GitHub repositories matching a query with caching."""
    return cache_manager.cache_call(_search_github_repos_uncached, "github", query, max_results)


def _get_github_repo_uncached(owner: str, repo: str) -> str:
    """Internal function to get GitHub repo without caching."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response, error = safe_api_call(url, headers=_get_headers())
    
    if error:
        return f"Error fetching repository '{owner}/{repo}': {error}"
    if response.status_code == 404:
        return f"Repository '{owner}/{repo}' not found."
    
    data = response.json()
    license_info = data.get("license")
    topics = data.get("topics", [])
    
    repo_info = (
        f"GitHub Repository: {data.get('full_name', 'N/A')}\n"
        f"  Description   : {data.get('description', 'No description')}\n"
        f"  ⭐ Stars      : {data.get('stargazers_count', 0):,}\n"
        f"  🍴 Forks      : {data.get('forks_count', 0):,}\n"
        f"  👀 Watchers   : {data.get('watchers_count', 0):,}\n"
        f"  🐛 Open Issues: {data.get('open_issues_count', 0):,}\n"
        f"  🔤 Language   : {data.get('language', 'N/A')}\n"
        f"  📜 License    : {license_info.get('name', 'N/A') if license_info else 'N/A'}\n"
        f"  🏷️ Topics     : {', '.join(topics) if topics else 'None'}\n"
        f"  🌿 Default Br.: {data.get('default_branch', 'N/A')}\n"
        f"  📅 Created    : {data.get('created_at', 'N/A')}\n"
        f"  🔄 Updated    : {data.get('updated_at', 'N/A')}\n"
        f"  🔗 URL        : {data.get('html_url', 'N/A')}"
    )
    readme = _fetch_readme(owner, repo)
    if readme:
        repo_info += f"\n\n--- Repository README ---\n{readme}"
    return repo_info


def get_github_repo(owner: str, repo: str) -> str:
    """Get detailed information about a specific GitHub repository with caching."""
    return cache_manager.cache_call(_get_github_repo_uncached, "github", owner, repo)

