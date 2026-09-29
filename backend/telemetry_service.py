"""
Sensorless Telemetry Ingestion
==============================
Fetches soil moisture (0-7cm), soil temperature, and weather data from
Open-Meteo — a free, keyless API — as a stand-in for physical soil sensors.
Includes a robust fallback so a live demo never crashes on stage.
"""

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

FALLBACK_TELEMETRY = {
    "soil_moisture": 0.24,
    "soil_temp": 27.5,
    "air_temp": 29.0,
    "windspeed": 8.0,
    "weathercode": 1,
    "trend": [],
    "source": "fallback",
}

_TELEMETRY_CACHE = {}


def fetch_soil_telemetry(lat: float, lon: float) -> dict:
    """
    Fetch zero-sensor soil moisture / temperature and short-term weather
    trends from Open-Meteo for the given coordinates.

    Returns a dict with keys:
        soil_moisture, soil_temp, air_temp, windspeed, weathercode,
        trend (list of 3-hour steps), source ("open-meteo" or "fallback")
    """
    cache_key = (round(lat, 3), round(lon, 3))
    if cache_key in _TELEMETRY_CACHE:
        return dict(_TELEMETRY_CACHE[cache_key])

    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "hourly": "soil_moisture_0_to_7cm,soil_temperature_0cm,temperature_2m",
            "forecast_days": 2,
            "timezone": "auto",
        }
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=3)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current_weather", {}) or {}
        hourly = data.get("hourly", {}) or {}

        soil_moisture_list = hourly.get("soil_moisture_0_to_7cm", []) or []
        soil_temp_list = hourly.get("soil_temperature_0cm", []) or []
        air_temp_list = hourly.get("temperature_2m", []) or []
        time_list = hourly.get("time", []) or []

        soil_moisture = soil_moisture_list[0] if soil_moisture_list else None
        soil_temp = soil_temp_list[0] if soil_temp_list else None

        trend = []
        for i in range(0, min(24, len(time_list)), 3):
            trend.append(
                {
                    "time": time_list[i] if i < len(time_list) else "",
                    "air_temp_c": air_temp_list[i] if i < len(air_temp_list) else None,
                    "soil_moisture_m3m3": soil_moisture_list[i] if i < len(soil_moisture_list) else None,
                }
            )

        if soil_moisture is None and soil_temp is None:
            return dict(FALLBACK_TELEMETRY)

        result = {
            "soil_moisture": soil_moisture if soil_moisture is not None else FALLBACK_TELEMETRY["soil_moisture"],
            "soil_temp": soil_temp if soil_temp is not None else FALLBACK_TELEMETRY["soil_temp"],
            "air_temp": current.get("temperature", FALLBACK_TELEMETRY["air_temp"]),
            "windspeed": current.get("windspeed", FALLBACK_TELEMETRY["windspeed"]),
            "weathercode": current.get("weathercode", FALLBACK_TELEMETRY["weathercode"]),
            "trend": trend,
            "source": "open-meteo",
        }
        _TELEMETRY_CACHE[cache_key] = result
        return dict(result)
    except Exception as e:
        fallback_with_error = dict(FALLBACK_TELEMETRY)
        fallback_with_error["error"] = str(e)
        return fallback_with_error
