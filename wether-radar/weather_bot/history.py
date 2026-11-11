import logging

import requests

from weather_bot.constants import (
    ARCHIVE_URL,
    CYRILLIC_TRANSLITERATION,
    FORECAST_URL,
    GEOCODING_URL,
    WEATHER_CODES,
)


class CityNotFoundError(Exception):
    pass


class NoWeatherDataError(Exception):
    pass


def describe_weather_code(code):
    return WEATHER_CODES.get(code, ("🌡️", "Погодные условия неизвестны"))


def find_location(city):
    response = requests.get(
        GEOCODING_URL,
        params={
            "name": city,
            "count": 1,
            "language": "ru",
            "format": "json",
        },
        timeout=10,
    )
    response.raise_for_status()
    locations = response.json().get("results", [])

    if not locations:
        response = requests.get(
            GEOCODING_URL,
            params={
                "name": city.translate(CYRILLIC_TRANSLITERATION),
                "count": 1,
                "language": "ru",
                "format": "json",
            },
            timeout=10,
        )
        response.raise_for_status()
        locations = response.json().get("results", [])

    if not locations:
        raise CityNotFoundError(city)

    return locations[0]


def get_historical_weather(city, requested_date):
    location = find_location(city)
    response = requests.get(
        ARCHIVE_URL,
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "start_date": requested_date.isoformat(),
            "end_date": requested_date.isoformat(),
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_sum,wind_speed_10m_max"
            ),
            "hourly": "relative_humidity_2m",
            "timezone": location.get("timezone", "auto"),
        },
        timeout=15,
    )
    response.raise_for_status()
    archive_data = response.json()
    daily = archive_data["daily"]
    if not daily["time"]:
        raise NoWeatherDataError(requested_date)

    emoji, description = describe_weather_code(daily["weather_code"][0])
    humidity_values = archive_data.get("hourly", {}).get(
        "relative_humidity_2m", []
    )
    humidity_values = [
        value for value in humidity_values if isinstance(value, (int, float))
    ]
    humidity_text = (
        f"{round(sum(humidity_values) / len(humidity_values))}%"
        if humidity_values
        else "нет данных"
    )
    place = ", ".join(
        value for value in (location["name"], location.get("country")) if value
    )

    return (
        f"{emoji} Погода в городе {place} за {requested_date.isoformat()}\n"
        f"🌥️ {description}\n"
        f"🌡️ Температура: {round(daily['temperature_2m_min'][0])}…"
        f"{round(daily['temperature_2m_max'][0])} °C\n"
        f"💧 Средняя влажность: {humidity_text}\n"
        f"🌧️ Осадки: {daily['precipitation_sum'][0]} мм\n"
        f"💨 Максимальный ветер: {daily['wind_speed_10m_max'][0]} км/ч"
    )


def get_forecast_weather(city, requested_date):
    location = find_location(city)
    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_sum,wind_speed_10m_max,"
                "relative_humidity_2m_mean"
            ),
            "forecast_days": 16,
            "timezone": location.get("timezone", "auto"),
        },
        timeout=15,
    )
    response.raise_for_status()
    daily = response.json()["daily"]

    try:
        day_index = daily["time"].index(requested_date.isoformat())
    except ValueError as error:
        raise NoWeatherDataError(requested_date) from error

    emoji, description = describe_weather_code(daily["weather_code"][day_index])
    humidity_values = daily.get("relative_humidity_2m_mean", [])
    humidity = (
        humidity_values[day_index]
        if day_index < len(humidity_values)
        else None
    )
    humidity_text = f"{round(humidity)}%" if humidity is not None else "нет данных"
    place = ", ".join(
        value for value in (location["name"], location.get("country")) if value
    )

    return (
        f"🔮 Прогноз погоды в городе {place} на {requested_date.isoformat()}\n"
        f"{emoji} {description}\n"
        f"🌡️ Температура: "
        f"{round(daily['temperature_2m_min'][day_index])}…"
        f"{round(daily['temperature_2m_max'][day_index])} °C\n"
        f"💧 Средняя влажность: {humidity_text}\n"
        f"🌧️ Осадки: {daily['precipitation_sum'][day_index]} мм\n"
        f"💨 Максимальный ветер: "
        f"{daily['wind_speed_10m_max'][day_index]} км/ч"
    )


def log_history_error(error):
    if isinstance(error, requests.HTTPError):
        status_code = error.response.status_code if error.response is not None else None
        logging.error("Open-Meteo вернул HTTP %s", status_code)
    else:
        logging.error("Ошибка запроса архива погоды (%s)", type(error).__name__)
