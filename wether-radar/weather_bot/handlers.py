import logging
import sqlite3
from datetime import date

import requests

from weather_bot.calendar_ui import (
    MAIN_KEYBOARD,
    build_favorites_keyboard,
    build_history_calendar,
)
from weather_bot.constants import (
    CURRENT_WEATHER_BUTTON,
    FAVORITES_BUTTON,
    FIRST_ARCHIVE_DATE,
    HISTORY_BUTTON,
    START_TEXT,
    last_forecast_date,
)
from weather_bot.current_weather import get_current_weather
from weather_bot.favorites import (
    add_favorite,
    get_favorite,
    get_favorites,
    remove_favorite,
)
from weather_bot.history import (
    CityNotFoundError,
    NoWeatherDataError,
    get_forecast_weather,
    get_historical_weather,
    log_history_error,
)


class WeatherBotHandlers:
    def __init__(self, bot, openweather_api_key):
        self.bot = bot
        self.openweather_api_key = openweather_api_key
        self.history_cities = {}
        self.input_modes = {}

    def register(self):
        self.bot.message_handler(commands=["start"])(self.start)
        self.bot.callback_query_handler(
            func=lambda call: (call.data or "").startswith(
                ("hn:", "hd:", "fav:")
            )
        )(self.handle_history_calendar)
        self.bot.message_handler(content_types=["text"])(self.handle_text)

    def start(self, message):
        self.bot.send_message(
            message.chat.id,
            START_TEXT,
            reply_markup=MAIN_KEYBOARD,
        )

    def handle_history_calendar(self, call):
        if call.message is None:
            self.bot.answer_callback_query(call.id)
            return

        chat_id = call.message.chat.id
        key = (chat_id, call.from_user.id)
        action, value = call.data.split(":", 1)
        if action == "fav":
            self._handle_favorite_callback(call, key, value)
            return

        if key not in self.history_cities:
            self.bot.answer_callback_query(
                call.id,
                "Сначала нажмите «История».",
                show_alert=True,
            )
            return

        if value == "disabled":
            self.bot.answer_callback_query(call.id)
            return

        if action == "hn":
            self._change_calendar_month(call, chat_id, value)
            return

        try:
            requested_date = date.fromisoformat(value)
        except ValueError:
            self.bot.answer_callback_query(call.id, "Неверная дата.")
            return

        if not FIRST_ARCHIVE_DATE <= requested_date <= last_forecast_date():
            self.bot.answer_callback_query(
                call.id,
                "Выберите дату в доступном диапазоне.",
            )
            return

        city = self.history_cities.pop(key)
        self.bot.answer_callback_query(call.id)
        weather_type = "прогноз" if requested_date > date.today() else "архив"
        self.bot.edit_message_text(
            f"Загружаю {weather_type} погоды для города {city} "
            f"за {requested_date.isoformat()}…",
            chat_id,
            call.message.message_id,
        )
        self._send_weather_for_date(chat_id, city, requested_date)

    def _change_calendar_month(self, call, chat_id, value):
        try:
            year, month = (int(part) for part in value.split("-", 1))
            if not 1 <= month <= 12:
                raise ValueError
            shown_month = date(year, month, 1)
        except ValueError:
            self.bot.answer_callback_query(
                call.id,
                "Не удалось открыть этот месяц.",
            )
            return

        if (
            shown_month < FIRST_ARCHIVE_DATE.replace(day=1)
            or shown_month > last_forecast_date().replace(day=1)
        ):
            self.bot.answer_callback_query(call.id, "Этот месяц недоступен.")
            return

        self.bot.answer_callback_query(call.id)
        self.bot.edit_message_reply_markup(
            chat_id,
            call.message.message_id,
            reply_markup=build_history_calendar(year, month),
        )

    def handle_text(self, message):
        city = (message.text or "").strip()
        key = (message.chat.id, message.from_user.id)

        if city == CURRENT_WEATHER_BUTTON:
            self.input_modes[key] = "current"
            self.bot.send_message(
                message.chat.id,
                "Введите название города для текущего прогноза:",
                reply_markup=MAIN_KEYBOARD,
            )
            return

        if city == HISTORY_BUTTON:
            self.input_modes[key] = "date"
            self.history_cities.pop(key, None)
            self.bot.send_message(
                message.chat.id,
                "Введите название города, чтобы выбрать дату в прошлом или будущем:",
                reply_markup=MAIN_KEYBOARD,
            )
            return

        if city == FAVORITES_BUTTON:
            self.input_modes.pop(key, None)
            self._send_favorites(message.chat.id, message.from_user.id)
            return

        input_mode = self.input_modes.pop(key, None)
        if input_mode == "date":
            self._request_history_date(message, city, key)
            return
        if input_mode == "favorite_add":
            self._add_favorite_city(message, city)
            return
        if input_mode == "current":
            if not city:
                self.bot.send_message(
                    message.chat.id,
                    "Название города пустое. Введите город ещё раз.",
                    reply_markup=MAIN_KEYBOARD,
                )
                return
            self._send_current_weather(message.chat.id, city)
            return

        if not city:
            self.bot.send_message(
                message.chat.id,
                "Напишите название города.",
                reply_markup=MAIN_KEYBOARD,
            )
            return

        self._send_current_weather(message.chat.id, city)

    def _request_history_date(self, message, city, key):
        if not city:
            self.bot.send_message(
                message.chat.id,
                "Название города пустое. Нажмите «📅 История», чтобы начать заново.",
                reply_markup=MAIN_KEYBOARD,
            )
            return

        self.history_cities[key] = city
        today = date.today()
        self.bot.send_message(
            message.chat.id,
            f"Выберите дату для города {city} "
            "(будущий прогноз доступен максимум на 16 дней):",
            reply_markup=build_history_calendar(today.year, today.month),
        )

    def _send_weather_for_date(self, chat_id, city, requested_date):
        try:
            if requested_date > date.today():
                weather_text = get_forecast_weather(city, requested_date)
            else:
                weather_text = get_historical_weather(city, requested_date)
        except CityNotFoundError:
            self.bot.send_message(
                chat_id,
                f"Город «{city}» не найден.",
                reply_markup=MAIN_KEYBOARD,
            )
            return
        except NoWeatherDataError:
            self.bot.send_message(
                chat_id,
                "Для этой даты нет данных о погоде. Выберите другую дату.",
                reply_markup=MAIN_KEYBOARD,
            )
            return
        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            log_history_error(error)
            self.bot.send_message(
                chat_id,
                "Не удалось получить архив погоды. Проверьте город и попробуйте позже.",
                reply_markup=MAIN_KEYBOARD,
            )
            return

        self.bot.send_message(
            chat_id,
            weather_text,
            reply_markup=MAIN_KEYBOARD,
        )

    def _send_current_weather(self, chat_id, city):
        try:
            weather_text = get_current_weather(city, self.openweather_api_key)
        except requests.HTTPError as error:
            self._handle_current_weather_http_error(chat_id, city, error)
            return
        except (requests.RequestException, ValueError, KeyError, TypeError) as error:
            logging.error("Ошибка запроса погоды (%s)", type(error).__name__)
            self.bot.send_message(
                chat_id,
                "Не удалось получить погоду. "
                "Проверьте название города и попробуйте позже.",
                reply_markup=MAIN_KEYBOARD,
            )
            return

        self.bot.send_message(
            chat_id,
            weather_text,
            reply_markup=MAIN_KEYBOARD,
        )

    def _handle_current_weather_http_error(self, chat_id, city, error):
        status_code = (
            error.response.status_code
            if error.response is not None
            else None
        )
        if status_code is None:
            logging.error("OpenWeather вернул HTTP-ошибку без кода ответа")
            text = (
                "Не удалось определить причину ошибки погоды. "
                "Проверьте интернет-соединение и API-ключ в файле .env."
            )
        elif status_code == 404:
            text = f"Город «{city}» не найден."
        elif status_code in (401, 403):
            logging.error("OpenWeather API отклонил запрос (HTTP %s)", status_code)
            text = (
                "OpenWeather отклонил API-ключ. Проверьте его в файле .env "
                "и убедитесь, что ключ активирован."
            )
        elif status_code == 429:
            logging.warning("Превышен лимит запросов OpenWeather (HTTP 429)")
            text = "Превышен лимит запросов к сервису погоды. Попробуйте позже."
        else:
            logging.error("OpenWeather API вернул HTTP %s", status_code)
            text = "Не удалось получить погоду. Попробуйте позже."

        self.bot.send_message(
            chat_id,
            text,
            reply_markup=MAIN_KEYBOARD,
        )

    def _handle_favorite_callback(self, call, key, value):
        if value == "add":
            self.input_modes[key] = "favorite_add"
            self.bot.answer_callback_query(call.id)
            self.bot.send_message(
                call.message.chat.id,
                "Введите название города, который нужно добавить в избранное:",
                reply_markup=MAIN_KEYBOARD,
            )
            return

        try:
            action, favorite_id_text = value.split(":", 1)
            favorite_id = int(favorite_id_text)
        except ValueError:
            self.bot.answer_callback_query(call.id, "Некорректная команда.")
            return

        try:
            if action == "weather":
                favorite = get_favorite(call.from_user.id, favorite_id)
                if favorite is None:
                    self.bot.answer_callback_query(
                        call.id,
                        "Город уже удалён из избранного.",
                        show_alert=True,
                    )
                    return
                self.bot.answer_callback_query(call.id)
                self._send_current_weather(call.message.chat.id, favorite[0])
                return

            if action == "remove":
                removed = remove_favorite(call.from_user.id, favorite_id)
                if not removed:
                    self.bot.answer_callback_query(
                        call.id,
                        "Город уже удалён из избранного.",
                    )
                    return
                self.bot.answer_callback_query(call.id, "Удалено из избранного.")
                self._send_favorites(
                    call.message.chat.id,
                    call.from_user.id,
                    message_id=call.message.message_id,
                )
                return
        except sqlite3.Error:
            logging.exception("Не удалось обновить список избранных городов")
            self.bot.answer_callback_query(
                call.id,
                "Не удалось открыть избранное. Попробуйте позже.",
                show_alert=True,
            )

    def _send_favorites(self, chat_id, user_id, message_id=None):
        try:
            favorites = get_favorites(user_id)
        except sqlite3.Error:
            logging.exception("Не удалось прочитать список избранных городов")
            self.bot.send_message(
                chat_id,
                "Не удалось открыть избранное. Попробуйте позже.",
                reply_markup=MAIN_KEYBOARD,
            )
            return

        text = (
            "Ваши избранные города:"
            if favorites
            else "В избранном пока нет городов. Добавьте первый город:"
        )
        markup = build_favorites_keyboard(favorites)
        if message_id is None:
            self.bot.send_message(
                chat_id,
                text,
                reply_markup=markup,
            )
        else:
            self.bot.edit_message_text(
                text,
                chat_id,
                message_id,
                reply_markup=markup,
            )

    def _add_favorite_city(self, message, city):
        if not city:
            self.bot.send_message(
                message.chat.id,
                "Название города пустое. Нажмите «⭐ Избранное» и попробуйте снова.",
                reply_markup=MAIN_KEYBOARD,
            )
            return

        try:
            added = add_favorite(message.from_user.id, city)
        except sqlite3.Error:
            logging.exception("Не удалось сохранить избранный город")
            self.bot.send_message(
                message.chat.id,
                "Не удалось сохранить город. Попробуйте позже.",
                reply_markup=MAIN_KEYBOARD,
            )
            return

        response = (
            f"Город «{city}» добавлен в избранное."
            if added
            else f"Город «{city}» уже есть в избранном."
        )
        self.bot.send_message(
            message.chat.id,
            response,
            reply_markup=MAIN_KEYBOARD,
        )
        self._send_favorites(message.chat.id, message.from_user.id)
