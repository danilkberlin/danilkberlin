"""Current weather + sunrise/sunset from Open-Meteo (free, no API key)."""
from __future__ import annotations

import logging
from datetime import datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from ..model import Weather
from .http import get_json

log = logging.getLogger(__name__)


def kind_for(code: int) -> str:
    """Collapse WMO weather codes into the handful of scenes the hero can draw."""
    if code in (0, 1):
        return "clear"
    if code in (2, 3):
        return "cloudy"
    if code in (45, 48):
        return "fog"
    if 51 <= code <= 57:
        return "drizzle"
    if 61 <= code <= 67 or 80 <= code <= 82:
        return "rain"
    if 71 <= code <= 77 or code in (85, 86):
        return "snow"
    if code >= 95:
        return "storm"
    return "cloudy"


def fetch(latitude: float, longitude: float, tz: str) -> Weather | None:
    query = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code,wind_speed_10m,is_day",
            "daily": "sunrise,sunset",
            "forecast_days": 2,
            "timezone": tz,
        }
    )
    try:
        payload = get_json(f"https://api.open-meteo.com/v1/forecast?{query}")
    except Exception as error:  # weather is decoration: never fail the build for it
        log.warning("weather unavailable: %s", error)
        return None
    zone = ZoneInfo(tz)
    current = payload["current"]
    daily = payload["daily"]
    now = datetime.now(zone)
    # The build runs at night, so "next sunrise" is the interesting one.
    sunrises = [datetime.fromisoformat(s).replace(tzinfo=zone) for s in daily["sunrise"]]
    sunsets = [datetime.fromisoformat(s).replace(tzinfo=zone) for s in daily["sunset"]]
    sunrise = next((s for s in sunrises if s > now), sunrises[-1])
    sunset = next((s for s in sunsets if s > now), sunsets[-1])
    code = int(current["weather_code"])
    return Weather(
        temp_c=float(current["temperature_2m"]),
        code=code,
        kind=kind_for(code),
        wind_kmh=float(current.get("wind_speed_10m") or 0),
        is_day=bool(current.get("is_day")),
        sunrise=sunrise,
        sunset=sunset,
    )
