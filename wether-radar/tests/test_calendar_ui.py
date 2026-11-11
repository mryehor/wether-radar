import calendar
import unittest
from datetime import timedelta

from weather_bot.calendar_ui import build_favorites_keyboard, build_history_calendar
from weather_bot.constants import FIRST_ARCHIVE_DATE, last_forecast_date


class CalendarUiTests(unittest.TestCase):
    def test_calendar_contains_valid_leap_day(self):
        markup = build_history_calendar(2024, 2)

        day_buttons = [
            button
            for row in markup.keyboard
            for button in row
            if button.callback_data.startswith("hd:")
        ]

        self.assertIn("hd:2024-02-29", [button.callback_data for button in day_buttons])
        self.assertEqual(len(day_buttons), calendar.monthrange(2024, 2)[1])

    def test_calendar_disables_dates_outside_supported_range(self):
        first_month = build_history_calendar(
            FIRST_ARCHIVE_DATE.year,
            FIRST_ARCHIVE_DATE.month,
        )
        first_month_buttons = [
            button
            for row in first_month.keyboard
            for button in row
        ]
        self.assertTrue(
            all(
                button.callback_data != "hn:1939-12"
                for button in first_month_buttons
            )
        )

        last_date = last_forecast_date()
        last_month = build_history_calendar(last_date.year, last_date.month)
        last_month_buttons = [
            button
            for row in last_month.keyboard
            for button in row
        ]
        after_forecast = last_date + timedelta(days=1)
        self.assertTrue(
            all(
                button.callback_data != f"hd:{after_forecast.isoformat()}"
                for button in last_month_buttons
            )
        )
        self.assertTrue(
            all(
                not button.callback_data.startswith("hn:")
                or button.callback_data == "hn:disabled"
                for button in last_month_buttons
                if button.text == "›"
            )
        )

    def test_favorites_keyboard_has_weather_remove_and_add_actions(self):
        markup = build_favorites_keyboard([(12, "Sumy")])

        self.assertEqual(markup.keyboard[0][0].callback_data, "fav:weather:12")
        self.assertEqual(markup.keyboard[0][1].callback_data, "fav:remove:12")
        self.assertEqual(markup.keyboard[1][0].callback_data, "fav:add")


if __name__ == "__main__":
    unittest.main()
