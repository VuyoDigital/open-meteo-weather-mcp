import pytest

from weather_mcp.validation import (
    ValidationError,
    validate_forecast_days,
    validate_location,
)


def test_validate_location_accepts_normal_city() -> None:
    result = validate_location("  Johannesburg  ")
    assert result.name == "Johannesburg"


def test_validate_location_rejects_empty() -> None:
    with pytest.raises(ValidationError, match="empty"):
        validate_location("   ")


def test_validate_location_rejects_unsafe_characters() -> None:
    with pytest.raises(ValidationError, match="only contain"):
        validate_location("Johannesburg; DROP TABLE")


def test_validate_location_rejects_urls() -> None:
    with pytest.raises(ValidationError, match="only contain"):
        validate_location("https://evil.example")


def test_validate_forecast_days_bounds() -> None:
    assert validate_forecast_days(1) == 1
    assert validate_forecast_days(7) == 7
    with pytest.raises(ValidationError, match="between"):
        validate_forecast_days(0)
    with pytest.raises(ValidationError, match="between"):
        validate_forecast_days(30)
