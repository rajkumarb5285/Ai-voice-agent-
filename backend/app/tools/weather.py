\"\"\"
Weather Tool
Retrieves weather data from Open-Meteo (free, no API key required) or OpenWeatherMap.
\"\"\"
import httpx
from app.config import settings
from app.utils.logger import logger

async def get_weather(location: str) -> str:
    \"\"\"
    Gets current weather for a location (e.g., 'San Francisco' or 'London, UK').
    Attempts Open-Meteo (free) or falls back/uses OpenWeatherMap if configured.
    \"\"\"
    # If OpenWeatherMap API key is provided, we can use it, but Open-Meteo is a great, free alternative
    if settings.openweather_api_key:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={settings.openweather_api_key}&units=metric"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    temp = data["main"]["temp"]
                    desc = data["weather"][0]["description"]
                    humidity = data["main"]["humidity"]
                    wind = data["wind"]["speed"]
                    return f"Weather in {location}: {temp}°C, {desc.capitalize()}. Humidity: {humidity}%, Wind: {wind} m/s."
        except Exception as e:
            logger.warning("openweather_failed_falling_back_to_open_meteo", error=str(e))

    # Free Open-Meteo Geocoding + Weather API
    try:
        # 1. Geocode location to lat/lon
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en"
        async with httpx.AsyncClient(timeout=10.0) as client:
            geo_resp = await client.get(geocode_url)
            if geo_resp.status_code != 200:
                return f"Could not find location: {location}."
            
            geo_data = geo_resp.json()
            if not geo_data.get("results"):
                return f"Location not found: {location}."
            
            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            name = result.get("name", location)
            country = result.get("country", "")
            fullname = f"{name}, {country}" if country else name

            # 2. Get current weather
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            weather_resp = await client.get(weather_url)
            if weather_resp.status_code != 200:
                return f"Failed to retrieve weather details for {fullname}."
            
            w_data = weather_resp.json()
            curr = w_data.get("current_weather", {})
            if not curr:
                return f"Weather data empty for {fullname}."
            
            temp = curr.get("temperature")
            wind = curr.get("windspeed")
            code = curr.get("weathercode", 0)

            # Basic weather code mappings
            w_codes = {
                0: "Clear sky",
                1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
                77: "Snow grains",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                85: "Slight snow showers", 86: "Heavy snow showers",
                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }
            desc = w_codes.get(code, "Unknown weather condition")
            return f"Weather in {fullname}: {temp}°C, {desc}. Wind speed: {wind} km/h."

    except Exception as e:
        logger.error("weather_lookup_failed", location=location, error=str(e))
        return f"Error: Could not retrieve weather for '{location}'. {str(e)}"
