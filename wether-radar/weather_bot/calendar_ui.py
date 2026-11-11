import calendar
from datetime import date, timedelta

import telebot

from weather_bot.constants import (
    CURRENT_WEATHER_BUTTON,
    FAVORITES_BUTTON,
    FIRST_ARCHIVE_DATE,
    HISTORY_BUTTON,
    MAX_FORECAST_DAYS,
)


MAIN_KEYBOARD = telebot.types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    is_persistent=True,
)
MAIN_KEYBOARD.row(
    telebot.types.KeyboardButton(CURRENT_WEATHER_BUTTON),
    telebot.types.KeyboardButton(HISTORY_BUTTON),
)
MAIN_KEYBOARD.add(telebot.types.KeyboardButton(FAVORITES_BUTTON))


def build_favorites_keyboard(favorites):
    markup = telebot.types.InlineKeyboardMarkup()
    for favorite_id, city in favorites:
        markup.row(
            telebot.types.InlineKeyboardButton(
                f"🌤 {city}",
                callback_data=f"fav:weather:{favorite_id}",
            ),
            telebot.types.InlineKeyboardButton(
                "✖",
                callback_data=f"fav:remove:{favorite_id}",
            ),
        )
    markup.add(
        telebot.types.InlineKeyboardButton(
            "➕ Добавить город",
            callback_data="fav:add",
        )
    )
    return markup


def build_history_calendar(year, month):
    markup = telebot.types.InlineKeyboardMarkup()
    last_forecast_date = date.today() + timedelta(days=MAX_FORECAST_DAYS - 1)
    last_forecast_month = last_forecast_date.replace(day=1)
    previous_month = (
        date(year - 1, 12, 1) if month == 1 else date(year, month - 1, 1)
    )
    next_month = (
        date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    )
    previous_data = (
        f"hn:{previous_month.year}-{previous_month.month}"
        if previous_month >= FIRST_ARCHIVE_DATE.replace(day=1)
        else "hn:disabled"
    )
    next_data = (
        f"hn:{next_month.year}-{next_month.month}"
        if next_month <= last_forecast_month
        else "hn:disabled"
    )
    month_names = (
        "январь", "февраль", "март", "апрель", "май", "июнь",
        "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
    )
    markup.row(
        telebot.types.InlineKeyboardButton("‹", callback_data=previous_data),
        telebot.types.InlineKeyboardButton(
            f"{month_names[month - 1]} {year}", callback_data="hn:disabled"
        ),
        telebot.types.InlineKeyboardButton("›", callback_data=next_data),
    )
    markup.row(
        *(
            telebot.types.InlineKeyboardButton(day, callback_data="hn:disabled")
            for day in ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
        )
    )

    for week in calendar.monthcalendar(year, month):
        buttons = []
        for day in week:
            if not day:
                buttons.append(
                    telebot.types.InlineKeyboardButton(
                        " ", callback_data="hn:disabled"
                    )
                )
                continue

            selected_date = date(year, month, day)
            callback_data = (
                f"hd:{selected_date.isoformat()}"
                if FIRST_ARCHIVE_DATE <= selected_date <= last_forecast_date
                else "hd:disabled"
            )
            buttons.append(
                telebot.types.InlineKeyboardButton(
                    str(day), callback_data=callback_data
                )
            )
        markup.row(*buttons)

    return markup
