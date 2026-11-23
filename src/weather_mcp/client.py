"""Talks only to the free Open-Meteo weather APIs (no API key)."""

from __future__ import annotations

from typing import Any

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DEFAULT_TIMEOUT_SECONDS = 10.0
USER_AGENT = "open-meteo-mcp/0.1.0 (agentic-associate-take-home)"


class WeatherApiError(RuntimeError):
    """Raised when Open-Meteo cannot fulfil a request."""


class WeatherClient:
    """Small HTTP client locked to Open-Meteo only."""

    def __init__(
        self,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            timeout=timeout_seconds,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            transport=transport,
            follow_redirects=False,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "WeatherClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def resolve_location(self, location_name: str) -> dict[str, Any]:
        try:
            response = self._client.get(
                GEOCODING_URL,
                params={
                    "name": location_name,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise WeatherApiError(
                "Weather lookup timed out. Please try again shortly."
            ) from exc
        except httpx.HTTPError as exc:
            raise WeatherApiError(
                "Weather lookup failed because the weather service was unavailable."
            ) from exc

        payload = response.json()
        results = payload.get("results") or []
        if not results:
            raise WeatherApiError(
                f"No matching place found for '{location_name}'. "
                "Try a clearer city or town name."
            )

        place = results[0]
        return {
            "name": place.get("name"),
            "country": place.get("country"),
            "region": place.get("admin1"),
            "latitude": place.get("latitude"),
            "longitude": place.get("longitude"),
            "timezone": place.get("timezone"),
        }

    def fetch_forecast(
        self,
        *,
        latitude: float,
        longitude: float,
        days: int,
    ) -> dict[str, Any]:
        try:
            response = self._client.get(
                FORECAST_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": (
                        "temperature_2m,relative_humidity_2m,"
                        "weather_code,wind_speed_10m"
                    ),
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                    "forecast_days": days,
                    "timezone": "auto",
                },
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise WeatherApiError(
                "Weather forecast timed out. Please try again shortly."
            ) from exc
        except httpx.HTTPError as exc:
            raise WeatherApiError(
                "Weather forecast failed because the weather service was unavailable."
            ) from exc

        return response.json()

    def current_weather(self, location_name: str) -> dict[str, Any]:
        place = self.resolve_location(location_name)
        forecast = self.fetch_forecast(
            latitude=place["latitude"],
            longitude=place["longitude"],
            days=1,
        )
        current = forecast.get("current") or {}
        return {
            "location": place,
            "current": {
                "time": current.get("time"),
                "temperature_c": current.get("temperature_2m"),
                "relative_humidity_percent": current.get("relative_humidity_2m"),
                "weather_code": current.get("weather_code"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
            },
            "source": "Open-Meteo (https://open-meteo.com)",
        }

    def forecast(self, location_name: str, days: int) -> dict[str, Any]:
        place = self.resolve_location(location_name)
        forecast = self.fetch_forecast(
            latitude=place["latitude"],
            longitude=place["longitude"],
            days=days,
        )
        daily = forecast.get("daily") or {}
        dates = daily.get("time") or []
        days_out: list[dict[str, Any]] = []
        for index, date in enumerate(dates):
            days_out.append(
                {
                    "date": date,
                    "weather_code": (daily.get("weather_code") or [None])[index],
                    "temperature_max_c": (daily.get("temperature_2m_max") or [None])[
                        index
                    ],
                    "temperature_min_c": (daily.get("temperature_2m_min") or [None])[
                        index
                    ],
                }
            )

        return {
            "location": place,
            "forecast_days": days_out,
            "source": "Open-Meteo (https://open-meteo.com)",
        }
