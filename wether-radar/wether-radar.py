import logging
import time

import telebot

from weather_bot.config import load_settings
from weather_bot.handlers import WeatherBotHandlers


def main():
    settings = load_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    bot = telebot.TeleBot(settings.telegram_bot_api_key)
    WeatherBotHandlers(bot, settings.openweather_api_key).register()

    while True:
        try:
            bot.polling(
                non_stop=False,
                interval=1,
                timeout=20,
                long_polling_timeout=20,
            )
        except KeyboardInterrupt:
            break
        except Exception as error:
            logging.error(
                "Ошибка опроса Telegram (%s); повтор через 5 секунд",
                type(error).__name__,
            )
            time.sleep(5)


if __name__ == "__main__":
    main()
