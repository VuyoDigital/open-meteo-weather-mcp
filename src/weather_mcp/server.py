"""MCP server that exposes safe weather tools to AI agents."""

from __future__ import annotations

import json
from typing import Any

from mcp.server import MCPServer

from weather_mcp.client import WeatherApiError, WeatherClient
from weather_mcp.validation import ValidationError, validate_forecast_request, validate_location

mcp = MCPServer(
    "open-meteo-weather",
    instructions=(
        "Use these tools to look up real weather data from Open-Meteo. "
        "Pass a clear city or town name. Forecast days must be between 1 and 7. "
        "Do not invent weather values if a tool returns an error."
    ),
)


def _json_result(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=True)


def _error_result(message: str) -> str:
    return _json_result({"ok": False, "error": message})


@mcp.tool()
def get_current_weather(location: str) -> str:
    """Get the current weather for a city or town.

    Args:
        location: City or town name, for example "Johannesburg" or "Cape Town".
    """
    try:
        validated = validate_location(location)
        with WeatherClient() as client:
            data = client.current_weather(validated.name)
        return _json_result({"ok": True, "data": data})
    except ValidationError as exc:
        return _error_result(str(exc))
    except WeatherApiError as exc:
        return _error_result(str(exc))


@mcp.tool()
def get_forecast(location: str, days: int = 3) -> str:
    """Get a short daily weather forecast for a city or town.

    Args:
        location: City or town name, for example "Johannesburg".
        days: Number of forecast days to return. Must be between 1 and 7.
    """
    try:
        validated = validate_forecast_request(location, days)
        with WeatherClient() as client:
            data = client.forecast(validated.location.name, validated.days)
        return _json_result({"ok": True, "data": data})
    except ValidationError as exc:
        return _error_result(str(exc))
    except WeatherApiError as exc:
        return _error_result(str(exc))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
