"""Retry utilities for API calls with exponential backoff."""

import time
import requests

RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.HTTPError,
)


def safe_api_call(
    url: str,
    method: str = "GET",
    params: dict = None,
    headers: dict = None,
    timeout: int = 10,
    max_retries: int = 3,
    base_delay: float = 0.5,
) -> tuple[requests.Response | None, str | None]:
    """Make an API call with retry logic. Returns (response, error_message)."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, json=params, headers=headers, timeout=timeout)
            else:
                response = requests.request(method, url, params=params, headers=headers, timeout=timeout)
            
            if response.status_code == 429:  # Rate limited - retry
                raise requests.exceptions.HTTPError("Rate limited (429)")
            return response, None
            
        except RETRYABLE_EXCEPTIONS as e:
            last_error = str(e)
            if attempt < max_retries:
                time.sleep(min(base_delay * (2 ** attempt), 10.0))
    
    return None, f"Request failed after {max_retries + 1} attempts: {last_error}"
