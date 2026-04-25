import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL  = "https://api.open-meteo.com/v1/forecast"

WEEKDAYS_UK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
MONTHS_UK   = [
    "січ", "лют", "бер", "квіт", "трав", "черв",
    "лип", "серп", "вер", "жовт", "лист", "груд",
]

WMO_DESCRIPTIONS: dict[int, str] = {
    0:  "☀️ Ясно",
    1:  "🌤 Майже ясно",
    2:  "⛅ Мінлива хмарність",
    3:  "☁️ Похмуро",
    45: "🌫 Туман",
    48: "🌫 Крижаний туман",
    51: "🌦 Легка мряка",
    53: "🌦 Мряка",
    55: "🌧 Сильна мряка",
    61: "🌧 Невеликий дощ",
    63: "🌧 Дощ",
    65: "🌧 Сильний дощ",
    71: "🌨 Невеликий сніг",
    73: "🌨 Сніг",
    75: "❄️ Сильний сніг",
    77: "🌨 Снігова крупа",
    80: "🌦 Злива",
    81: "🌦 Сильна злива",
    82: "🌧 Шторм",
    85: "🌨 Сніговий дощ",
    86: "🌨 Сильний сніговий дощ",
    95: "⛈ Гроза",
    96: "⛈ Гроза з градом",
    99: "⛈ Сильна гроза з градом",
}


def _geocode(city: str) -> tuple[float, float]:
    resp = requests.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "uk"},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        raise ValueError(f"City not found: {city}")
    return results[0]["latitude"], results[0]["longitude"]


def _fetch_forecast(lat: float, lon: float) -> dict:
    resp = requests.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "weather_code",
                "wind_speed_10m_max",
                "precipitation_probability_max",
            ]),
            "hourly": "relative_humidity_2m",
            "forecast_days": 7,
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def _daily_avg_humidity(hourly: dict, day_index: int) -> int:
    start  = day_index * 24
    end    = start + 24
    values = hourly["relative_humidity_2m"][start:end]
    valid  = [v for v in values if v is not None]
    return round(sum(valid) / len(valid)) if valid else 0


def build_weather_html(cities: list[str]) -> str:
    """Fetch 7-day forecast for each city and return a full-width HTML section."""
    city_forecasts: list[dict] = []
    for city in cities:
        try:
            lat, lon = _geocode(city)
            data = _fetch_forecast(lat, lon)
            city_forecasts.append({"city": city, "data": data})
            logger.info(f"Weather fetched for {city}")
        except Exception as exc:
            logger.warning(f"Weather fetch failed for {city}: {exc}")
            city_forecasts.append({"city": city, "data": None})

    first = next((c for c in city_forecasts if c["data"]), None)
    if not first:
        return ""

    dates = first["data"]["daily"]["time"]
    if len(dates) < 7:
        logger.warning(f"Expected 7 forecast days, got {len(dates)} — table may be incomplete.")

    # Column headers
    header_cells = '<th class="wt-city">Місто</th>'
    for d in dates:
        dt      = datetime.strptime(d, "%Y-%m-%d")
        weekday = WEEKDAYS_UK[dt.weekday()]
        month   = MONTHS_UK[dt.month - 1]
        header_cells += f'<th class="wt-day">{weekday}<br><span class="wt-date">{dt.day} {month}</span></th>'

    # Data rows
    rows_html = ""
    for entry in city_forecasts:
        city = entry["city"]
        data = entry["data"]

        cells = f'<td class="wt-city-name">{city}</td>'

        if data is None:
            for _ in dates:
                cells += '<td class="wt-cell">—</td>'
        else:
            daily  = data["daily"]
            hourly = data["hourly"]
            for i in range(len(dates)):
                code     = daily["weather_code"][i]
                cond     = WMO_DESCRIPTIONS.get(code, f"Код {code}")
                t_max    = round(daily["temperature_2m_max"][i])
                t_min    = round(daily["temperature_2m_min"][i])
                wind     = round(daily["wind_speed_10m_max"][i])
                precip   = int(daily["precipitation_probability_max"][i] or 0)
                humidity = _daily_avg_humidity(hourly, i)
                cells += (
                    f'<td class="wt-cell">'
                    f'<div class="wt-cond">{cond}</div>'
                    f'<div class="wt-temp">🌡 {t_max}° / {t_min}°</div>'
                    f'<div class="wt-meta">💧 {humidity}%&nbsp;&nbsp;💨 {wind} км/год</div>'
                    f'<div class="wt-precip">☔ {precip}%</div>'
                    f'</td>'
                )

        rows_html += f"<tr>{cells}</tr>\n        "

    return f"""
    <section class="weather-section">
      <h2 class="weather-title">Прогноз погоди на 7 днів</h2>
      <div class="weather-table-wrap">
        <table class="weather-table">
          <thead><tr>{header_cells}</tr></thead>
          <tbody>
        {rows_html}</tbody>
        </table>
      </div>
    </section>
"""
