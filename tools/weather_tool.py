"""Weather Tool - Fetches current weather using OpenWeatherMap API with retry logic."""

import os
from tools.retry_utils import safe_api_call


def get_weather(city: str) -> str:
    """Get current weather for a city with retry on API failure."""
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return "Error: WEATHER_API_KEY not set."

    response, error = safe_api_call(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": api_key, "units": "metric"},
        timeout=10
    )
    
    if error:
        return f"Error fetching weather for '{city}': {error}"
    if response.status_code == 401:
        return "Error: Invalid OpenWeatherMap API key."
    if response.status_code == 404:
        return f"City '{city}' not found."
    
    try:
        data = response.json()
        main = data.get("main", {})
        return (
            f"Weather for {data.get('name', city)}, {data.get('sys', {}).get('country', '?')}:\n"
            f"  Condition  : {data.get('weather', [{}])[0].get('description', 'N/A').title()}\n"
            f"  Temperature: {main.get('temp', 'N/A')}°C (Min: {main.get('temp_min', 'N/A')}°C, Max: {main.get('temp_max', 'N/A')}°C)\n"
            f"  Feels Like : {main.get('feels_like', 'N/A')}°C\n"
            f"  Humidity   : {main.get('humidity', 'N/A')}%\n"
            f"  Wind Speed : {data.get('wind', {}).get('speed', 'N/A')} m/s"
        )
    except Exception as e:
        return f"Error parsing weather for '{city}': {e}"
