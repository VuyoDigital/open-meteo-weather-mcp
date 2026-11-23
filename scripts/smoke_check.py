"""Simple live check against Open-Meteo (no API key required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from weather_mcp.server import get_current_weather  # noqa: E402


def main() -> int:
    raw = get_current_weather("Johannesburg")
    payload = json.loads(raw)
    print(raw)
    if not payload.get("ok"):
        print("Smoke check failed:", payload.get("error"), file=sys.stderr)
        return 1
    temp = payload["data"]["current"]["temperature_c"]
    print(f"\nSmoke check passed. Johannesburg temperature_c={temp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
