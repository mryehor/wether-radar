import requests

from weather_bot.constants import WEATHER_URL


def format_current_weather(city, weather_data):
    main = weather_data["main"]
    condition = weather_data["weather"][0]
    wind = weather_data["wind"]
    description = condition["description"].capitalize()
    emoji = {
        "Clear": "☀️",
        "Clouds": "☁️",
        "Drizzle": "🌦️",
        "Rain": "🌧️",
        "Thunderstorm": "⛈️",
        "Snow": "❄️",
        "Mist": "🌫️",
        "Smoke": "🌫️",
        "Haze": "🌫️",
        "Dust": "🌫️",
        "Fog": "🌫️",
        "Sand": "🌫️",
        "Ash": "🌫️",
        "Squall": "💨",
        "Tornado": "🌪️",
    }.get(condition["main"], "🌡️")

    return (
        f"{emoji} Погода в городе {city}\n"
        f"🌥️ {description}\n"
        f"🌡️ Температура: {round(main['temp'])} °C\n"
        f"🤗 Ощущается как: {round(main['feels_like'])} °C\n"
        f"💧 Влажность: {main['humidity']}%\n"
        f"💨 Ветер: {wind['speed']} м/с"
    )


def get_current_weather(city, api_key):
    response = requests.get(
        WEATHER_URL,
        params={
            "q": city,
            "units": "metric",
            "lang": "ru",
            "appid": api_key,
        },
        timeout=10,
    )
    response.raise_for_status()
    return format_current_weather(city, response.json())
