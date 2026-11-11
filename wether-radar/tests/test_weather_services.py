import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from weather_bot.current_weather import format_current_weather
from weather_bot.history import (
    CityNotFoundError,
    find_location,
    get_forecast_weather,
    get_historical_weather,
)


def make_response(data):
    return SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: data,
    )


class CurrentWeatherTests(unittest.TestCase):
    def test_current_weather_format_includes_weather_details(self):
        text = format_current_weather(
            "Sumy",
            {
                "main": {"temp": 12.4, "feels_like": 10.6, "humidity": 65},
                "weather": [{"main": "Rain", "description": "light rain"}],
                "wind": {"speed": 3.2},
            },
        )

        self.assertIn("Sumy", text)
        self.assertIn("12 °C", text)
        self.assertIn("11 °C", text)
        self.assertIn("65%", text)
        self.assertIn("3.2 м/с", text)


class HistoryWeatherTests(unittest.TestCase):
    def setUp(self):
        self.location = {
            "name": "Sumy",
            "country": "Ukraine",
            "latitude": 50.9,
            "longitude": 34.8,
            "timezone": "Europe/Kyiv",
        }

    @patch("weather_bot.history.requests.get")
    def test_city_lookup_retries_with_transliterated_name(self, get):
        get.side_effect = [
            make_response({}),
            make_response({"results": [self.location]}),
        ]

        result = find_location("Сумы")

        self.assertEqual(result, self.location)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args_list[1].kwargs["params"]["name"], "Sumy")

    @patch("weather_bot.history.requests.get")
    def test_historical_weather_formats_archive_response(self, get):
        requested_date = date(2024, 10, 29)
        get.side_effect = [
            make_response({"results": [self.location]}),
            make_response(
                {
                    "daily": {
                        "time": [requested_date.isoformat()],
                        "weather_code": [3],
                        "temperature_2m_min": [5.1],
                        "temperature_2m_max": [12.4],
                        "precipitation_sum": [0.2],
                        "wind_speed_10m_max": [14.2],
                    },
                    "hourly": {"relative_humidity_2m": [60, 80]},
                }
            ),
        ]

        text = get_historical_weather("Sumy", requested_date)

        self.assertIn("2024-10-29", text)
        self.assertIn("70%", text)
        self.assertIn("14.2 км/ч", text)

    @patch("weather_bot.history.requests.get")
    def test_forecast_uses_selected_future_date(self, get):
        today = date.today()
        requested_date = today + timedelta(days=1)
        get.side_effect = [
            make_response({"results": [self.location]}),
            make_response(
                {
                    "daily": {
                        "time": [today.isoformat(), requested_date.isoformat()],
                        "weather_code": [0, 61],
                        "temperature_2m_min": [5.0, 6.1],
                        "temperature_2m_max": [12.0, 14.8],
                        "precipitation_sum": [0.0, 1.2],
                        "wind_speed_10m_max": [10.0, 18.4],
                        "relative_humidity_2m_mean": [60.0, 72.0],
                    }
                }
            ),
        ]

        text = get_forecast_weather("Sumy", requested_date)

        self.assertIn("Прогноз погоды", text)
        self.assertIn(requested_date.isoformat(), text)
        self.assertIn("72%", text)
        self.assertIn("18.4 км/ч", text)
        self.assertEqual(get.call_args.kwargs["params"]["forecast_days"], 16)

    @patch("weather_bot.history.requests.get")
    def test_city_lookup_raises_when_no_match_is_found(self, get):
        get.return_value = make_response({})

        with self.assertRaises(CityNotFoundError):
            find_location("No Such City")


if __name__ == "__main__":
    unittest.main()
