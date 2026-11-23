"""Input validation and safety limits for agent-facing weather tools."""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_LOCATION_LENGTH = 80
MAX_FORECAST_DAYS = 7
MIN_FORECAST_DAYS = 1

# Allow common place-name characters only (blocks URL/path/injection-like input).
_LOCATION_PATTERN = re.compile(r"^[A-Za-z0-9 ,.'\-]{1,80}$")


class ValidationError(ValueError):
    """Raised when tool input is unsafe or outside supported bounds."""


@dataclass(frozen=True)
class ValidatedLocation:
    name: str


@dataclass(frozen=True)
class ValidatedForecastRequest:
    location: ValidatedLocation
    days: int


def validate_location(location: str) -> ValidatedLocation:
    if location is None:
        raise ValidationError("location is required")

    cleaned = " ".join(str(location).strip().split())
    if not cleaned:
        raise ValidationError("location must not be empty")
    if len(cleaned) > MAX_LOCATION_LENGTH:
        raise ValidationError(
            f"location must be at most {MAX_LOCATION_LENGTH} characters"
        )
    if not _LOCATION_PATTERN.fullmatch(cleaned):
        raise ValidationError(
            "location may only contain letters, numbers, spaces, commas, "
            "periods, apostrophes, and hyphens"
        )
    return ValidatedLocation(name=cleaned)


def validate_forecast_days(days: int) -> int:
    try:
        value = int(days)
    except (TypeError, ValueError) as exc:
        raise ValidationError("days must be an integer") from exc

    if value < MIN_FORECAST_DAYS or value > MAX_FORECAST_DAYS:
        raise ValidationError(
            f"days must be between {MIN_FORECAST_DAYS} and {MAX_FORECAST_DAYS}"
        )
    return value


def validate_forecast_request(location: str, days: int) -> ValidatedForecastRequest:
    return ValidatedForecastRequest(
        location=validate_location(location),
        days=validate_forecast_days(days),
    )
