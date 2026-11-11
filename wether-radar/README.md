# Weather Radar

A Telegram weather bot that provides current conditions, historical weather, and
short-term forecasts. It also lets each Telegram user keep a personal list of
favorite cities.

## Features

- Current temperature, feels-like temperature, humidity, wind speed, and a
  weather description.
- Date picker for historical weather and forecasts up to 16 days ahead.
- Favorite cities stored per Telegram user in a local SQLite database.
- Russian-language bot messages and city lookup.
- API keys loaded from a local `.env` file.

## Requirements

- Python 3.10 or later.
- A Telegram bot token from [@BotFather](https://t.me/BotFather).
- An OpenWeather API key for current weather.
- Internet access to Open-Meteo for city lookup, historical data, and forecasts.

## Setup

Clone the repository and change into the project directory.

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Edit `.env` and replace the placeholders:

```dotenv
TELEGRAM_BOT_API_KEY=your_telegram_bot_token
OPENWEATHER_API_KEY=your_openweather_api_key
```

Keep `.env` private. It is excluded by `.gitignore`; only `.env.example`, which
contains placeholders, belongs in the repository.

## Run

```bash
python wether-radar.py
```

Open the bot in Telegram and send `/start`. Use the menu buttons to request
current weather, select a date, or manage favorite cities. You can also send a
city name directly for current weather.

Only run one polling instance of a bot token at a time. Running multiple copies
can cause Telegram's `409 Conflict` polling error.

## Historical weather and forecasts

Open-Meteo provides historical weather and forecasts without an additional API
key. Select a past date to request historical data, or a future date to request
a forecast. Forecast availability is limited to 16 days including today;
historical availability depends on the selected location and data source.

## Favorites and local data

Favorite cities are stored in `favorites.sqlite3` in the project directory.
The database is created automatically and is ignored by Git. It is local to
this installation; back it up separately if you need to preserve it.

## Run tests

The test suite uses Python's standard library and does not call Telegram or
weather APIs:

```bash
python -m unittest discover -s tests -v
```

## Project layout

```text
wether-radar.py           Application entry point
weather_bot/
  calendar_ui.py          Telegram keyboards and date calendar
  config.py               Environment-based settings
  constants.py            Shared labels and API endpoints
  current_weather.py      Current weather API and formatting
  favorites.py            Per-user SQLite favorites
  handlers.py             Telegram message and callback handlers
  history.py              Geocoding, history, and forecast services
tests/                    Network-free automated tests
```
