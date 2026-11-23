# Open-Meteo MCP Server

A small MCP server that lets an AI agent look up real weather through the free [Open-Meteo](https://open-meteo.com/) API.

Built as a focused take-home: one useful capability, implemented carefully, with clear safety boundaries. No API key required, and no secrets belong in this repo.

## What it does

Two tools are exposed:

| Tool | Purpose |
| --- | --- |
| `get_current_weather` | Current temperature, humidity, wind, and weather code for a city or town |
| `get_forecast` | Short daily forecast for 1–7 days |

## Why this scope

Open-Meteo was a practical choice: useful data, free access, and no account setup for reviewers.

The surface area is intentionally narrow. For agent-facing tools, a small interface with strong validation is usually safer than a broad one with unclear side effects. The goal here was correct behaviour and predictable failure modes, not feature count.

## How MCP fits in

MCP (Model Context Protocol) is a standard way for AI hosts such as Claude or Cursor to call tools provided by a local server.

Typical flow:

1. A user asks about the weather  
2. The AI host calls one of these tools  
3. This server validates the input  
4. This server calls Open-Meteo  
5. The host receives a structured result and responds to the user  

## Project layout

```text
src/weather_mcp/
  validation.py   # reject bad or unsafe input early
  client.py       # Open-Meteo-only HTTP access
  server.py       # MCP tool wiring
tests/            # unit checks
scripts/          # live smoke check
```

## Install

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

## Run

```bash
python -m weather_mcp.server
```

Or:

```bash
open-meteo-mcp
```

Transport is **stdio**, which is the normal pattern for local MCP servers. The host launches the process and communicates over stdin/stdout.

### Example host config

```json
{
  "mcpServers": {
    "open-meteo-weather": {
      "command": "python",
      "args": ["-m", "weather_mcp.server"],
      "cwd": "/absolute/path/to/open-meteo-mcp",
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

If the package is installed editable, `command` can point to `open-meteo-mcp` instead.

## Examples

### Current weather

```text
get_current_weather(location="Johannesburg")
```

Example success payload:

```json
{
  "ok": true,
  "data": {
    "location": {
      "name": "Johannesburg",
      "country": "South Africa",
      "region": "Gauteng"
    },
    "current": {
      "temperature_c": 22.5,
      "relative_humidity_percent": 40,
      "wind_speed_kmh": 12.0
    },
    "source": "Open-Meteo (https://open-meteo.com)"
  }
}
```

### Short forecast

```text
get_forecast(location="Cape Town", days=3)
```

Returns up to three daily high/low values.

### Rejected input

```text
get_current_weather(location="https://evil.example")
```

```json
{
  "ok": false,
  "error": "location may only contain letters, numbers, spaces, commas, periods, apostrophes, and hyphens"
}
```

## Tests and checks

```bash
pytest -q
```

Live check against Open-Meteo (internet required, still no API key):

```bash
python scripts/smoke_check.py
```

### Quick verification path

```bash
pip install -r requirements.txt
pip install -e .
pytest -q
python scripts/smoke_check.py
```

If both succeed, core behaviour and the live API path are working.

## What can go wrong when an AI agent uses this?

Agent-facing tools need explicit limits. These were the main failure cases considered.

### Bad input
An agent may pass URLs, code fragments, or other non-location text.  
Location values are validated for length and allowed characters before any network call. Invalid input fails fast with a clear error.

### Upstream API failure
Open-Meteo can time out or return errors.  
Requests use timeouts, redirects are not followed, and failures are returned as `{ "ok": false, "error": "..." }` instead of crashing or inventing weather values.

### Unintended tool use
Possible misuse includes oversized forecast windows, repeated noisy calls, or treating the server as a generic web fetcher.

Controls in place:
- forecast days limited to **1–7**
- HTTP client allowlisted to **Open-Meteo hosts only**
- tool descriptions that define valid input
- structured errors that push the agent to retry or clarify, not guess

### Ambiguous place names
Names like “Springfield” can match multiple places.  
The server uses Open-Meteo’s best match and returns the resolved location details. If nothing matches, it returns a clear not-found error.

## Design notes

- Prefer a small working tool over a large incomplete one  
- Avoid secrets so the demo stays easy to run  
- Validate before calling the network  
- Keep success/failure responses structured for hosts and agents  

## Possible next steps

- Per-process rate limiting for noisy agents  
- Optional lat/lon tools with the same validation rules  
- Contract tests that freeze tool schemas for review  

## License

MIT
