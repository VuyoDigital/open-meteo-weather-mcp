import json

from weather_mcp.server import get_current_weather, get_forecast


def test_get_current_weather_rejects_bad_input_without_calling_api() -> None:
    result = json.loads(get_current_weather("https://evil.example"))
    assert result["ok"] is False
    assert "error" in result


def test_get_forecast_rejects_too_many_days() -> None:
    result = json.loads(get_forecast("Johannesburg", days=30))
    assert result["ok"] is False
    assert "between" in result["error"].lower()
