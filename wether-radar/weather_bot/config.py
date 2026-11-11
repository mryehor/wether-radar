import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_api_key: str
    openweather_api_key: str


def load_settings():
    load_dotenv()

    telegram_bot_api_key = os.getenv("TELEGRAM_BOT_API_KEY")
    openweather_api_key = os.getenv("OPENWEATHER_API_KEY")

    if not telegram_bot_api_key:
        raise RuntimeError("Добавьте TELEGRAM_BOT_API_KEY в файл .env")
    if not openweather_api_key:
        raise RuntimeError("Добавьте OPENWEATHER_API_KEY в файл .env")

    return Settings(
        telegram_bot_api_key=telegram_bot_api_key,
        openweather_api_key=openweather_api_key,
    )
