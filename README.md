# Open-Meteo MCP Server

A small **MCP server** that lets an AI agent look up real weather using the free [Open-Meteo](https://open-meteo.com/) API.

This was built as a focused take-home for an **Agentic Associate** style role: one useful tool, done carefully, with safety in mind.

## What it does

The server exposes two tools:

| Tool | Purpose |
| --- | --- |
| `get_current_weather` | Current temperature, humidity, wind, and weather code for a city/town |
| `get_forecast` | Short daily forecast (1–7 days) for a city/town |

No API key is required. No secrets belong in this repo.

## Why I scoped it this way

I chose Open-Meteo because it is useful, free, and needs no API key — so reviewers can run the project without account setup or secret handling. I deliberately kept the surface area small: two tools, strict input checks, and clear failure behaviour. For agent-facing work, I would rather ship a narrow tool with strong boundaries than a broad tool with unclear side effects.

## Why MCP?

MCP (Model Context Protocol) is a standard way for AI apps (like Claude or Cursor) to call tools you build.

Simple flow:

1. User asks an AI about the weather  
2. AI calls one of these tools  
3. This server checks the input  
4. This server calls Open-Meteo  
5. The AI gets a clean result and answers the user  

## Project layout

```text
src/weather_mcp/
  validation.py   # reject bad or unsafe input
  client.py       # talk only to Open-Meteo
  server.py       # expose tools over MCP
tests/            # automated checks
scripts/          # simple live smoke check
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

## Run the MCP server

```bash
python -m weather_mcp.server
```

Or:

```bash
open-meteo-mcp
```

The server uses **stdio** (standard for local MCP tools). A host app starts it and talks to it.

### Example Cursor / Claude Desktop style config

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

If you installed the package with `pip install -e .`, you can point `command` at `open-meteo-mcp` instead.

## Examples

### Example 1 — current weather

Tool call:

```text
get_current_weather(location="Johannesburg")
```

Example successful shape:

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

### Example 2 — short forecast

Tool call:

```text
get_forecast(location="Cape Town", days=3)
```

Returns up to 3 daily high/low values.

### Example 3 — rejected bad input

```text
get_current_weather(location="https://evil.example")
```

Returns:

```json
{
  "ok": false,
  "error": "location may only contain letters, numbers, spaces, commas, periods, apostrophes, and hyphens"
}
```

## Tests and checks

Run unit tests:

```bash
pytest -q
```

Run a live smoke check (needs internet, still no API key):

```bash
python scripts/smoke_check.py
```

### Quick reviewer path (about 60 seconds)

```bash
pip install -r requirements.txt
pip install -e .
pytest -q
python scripts/smoke_check.py
```

If both succeed, the core behaviour and live Open-Meteo path are working.

## What could go wrong when an AI agent uses this tool?

This section is intentional. Tools used by agents need clear limits.

### 1) Bad input
**Risk:** An agent might pass URLs, code, or nonsense instead of a place name.  
**What I did:** Strict validation on location text (length + allowed characters). Invalid input fails fast with a clear error and never reaches Open-Meteo.

### 2) The API failing
**Risk:** Open-Meteo could time out or return an error.  
**What I did:** HTTP timeouts, no redirect following, and friendly error messages. The tool returns `{ "ok": false, "error": "..." }` instead of crashing or inventing weather.

### 3) The agent calling it in a way I didn’t intend
**Risks:**
- asking for a huge forecast window
- hammering the API with repeated calls
- trying to turn this into a general web-fetch tool

**What I did:**
- forecast days capped to **1–7**
- client allowlisted to **Open-Meteo hosts only** (no arbitrary URLs)
- tool descriptions tell the agent what valid input looks like
- errors tell the agent to retry or clarify, not to guess weather values

### 4) Ambiguous place names
**Risk:** “Springfield” could match many places.  
**What I did:** Use Open-Meteo’s best single match and return the resolved place details so the agent/user can see which location was used. If nothing matches, return a clear “not found” error.

## Design choices (short)

- **Small and correct** over large and unfinished  
- **No API keys** so the demo is easy to run and safe to publish  
- **Validation before network** so unsafe agent input fails cheaply  
- **JSON responses with `ok`/`error`** so hosts/agents can handle failure cleanly  

## What I’d improve next

- Add a tiny per-process rate limit for noisy agents  
- Add optional lat/lon tools with the same strict bounds  
- Add contract tests that freeze tool schemas for review  

## License

MIT — feel free to reuse for learning and demos.
