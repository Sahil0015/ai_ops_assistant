"""
Weather Tool.
Fetches current weather data for a given city using the OpenWeatherMap API.
"""

import os
import requests


def get_weather(city: str) -> str:
    """
    Get the current weather for a given city using OpenWeatherMap.

    Args:
        city: The name of the city to get weather for.

    Returns:
        A string with weather information for the city.
    """
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return "Error: WEATHER_API_KEY environment variable is not set."

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 401:
            return "Error: Invalid OpenWeatherMap API key."
        if response.status_code == 404:
            return f"City '{city}' not found."

        response.raise_for_status()
        data = response.json()

        city_name = data.get("name", city)
        country = data.get("sys", {}).get("country", "Unknown")
        temp = data.get("main", {}).get("temp", "N/A")
        feels_like = data.get("main", {}).get("feels_like", "N/A")
        humidity = data.get("main", {}).get("humidity", "N/A")
        description = data.get("weather", [{}])[0].get("description", "N/A").title()
        wind_speed = data.get("wind", {}).get("speed", "N/A")
        temp_min = data.get("main", {}).get("temp_min", "N/A")
        temp_max = data.get("main", {}).get("temp_max", "N/A")

        return (
            f"Weather for {city_name}, {country}:\n"
            f"  Condition  : {description}\n"
            f"  Temperature: {temp}°C (Min: {temp_min}°C, Max: {temp_max}°C)\n"
            f"  Feels Like : {feels_like}°C\n"
            f"  Humidity   : {humidity}%\n"
            f"  Wind Speed : {wind_speed} m/s"
        )
    except requests.RequestException as e:
        return f"Error fetching weather for '{city}': {e}"
