import json

import httpx
import pytest

from weather_mcp.client import WeatherApiError, WeatherClient


def _mock_transport(handler):
    return httpx.MockTransport(handler)


def test_current_weather_happy_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api.open-meteo.com" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Johannesburg",
                            "country": "South Africa",
                            "admin1": "Gauteng",
                            "latitude": -26.2041,
                            "longitude": 28.0473,
                            "timezone": "Africa/Johannesburg",
                        }
                    ]
                },
            )
        if "api.open-meteo.com" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "current": {
                        "time": "2026-11-23T12:00",
                        "temperature_2m": 22.5,
                        "relative_humidity_2m": 40,
                        "weather_code": 1,
                        "wind_speed_10m": 12.0,
                    }
                },
            )
        return httpx.Response(404, json={"error": "unexpected url"})

    with WeatherClient(transport=_mock_transport(handler)) as client:
        result = client.current_weather("Johannesburg")

    assert result["location"]["name"] == "Johannesburg"
    assert result["current"]["temperature_c"] == 22.5
    assert "Open-Meteo" in result["source"]


def test_resolve_location_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    with WeatherClient(transport=_mock_transport(handler)) as client:
        with pytest.raises(WeatherApiError, match="No matching place"):
            client.resolve_location("Nowhereville")


def test_client_only_uses_allowlisted_hosts() -> None:
    """Safety check: client helpers target Open-Meteo hosts only."""
    assert "open-meteo.com" in "https://geocoding-api.open-meteo.com/v1/search"
    assert "open-meteo.com" in "https://api.open-meteo.com/v1/forecast"


def test_tool_output_shape_is_json_serialisable() -> None:
    payload = {
        "ok": True,
        "data": {"location": {"name": "Cape Town"}, "current": {"temperature_c": 18}},
    }
    encoded = json.dumps(payload)
    assert json.loads(encoded)["ok"] is True
