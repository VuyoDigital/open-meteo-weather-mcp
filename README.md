# Open-Meteo MCP Server

Hi — I’m Vuyolwethu. This is a small MCP server I built so an AI agent can look up real weather using the free [Open-Meteo](https://open-meteo.com/) API.

I kept it intentionally small. One useful thing, done carefully, with safety in mind. That’s the kind of work I want to show for an Agentic Associate-style role.

## What it does

It exposes two tools an AI can call:

| Tool | Purpose |
| --- | --- |
| `get_current_weather` | Current temperature, humidity, wind, and weather code for a city/town |
| `get_forecast` | Short daily forecast (1–7 days) for a city/town |

No API key. No secrets in the repo. You should be able to clone this and run it without setting anything fancy up.

## Why I built it this way

I picked Open-Meteo because it’s useful, free, and doesn’t need an account. That means a reviewer can actually try it quickly.

I also kept the tool surface small on purpose. For anything an AI agent can call, I’d rather ship a narrow tool with clear boundaries than a broad one that can surprise you. Two tools. Strict checks. Clear failures.

## What MCP means here (in plain English)

MCP is just a standard way for AI apps like Claude or Cursor to use tools that I build.

The flow is simple:

1. Someone asks the AI about the weather  
2. The AI calls one of my tools  
3. My server checks the input  
4. My server talks to Open-Meteo  
5. The AI gets a clean result and answers  

## Project layout

```text
src/weather_mcp/
  validation.py   # stop bad / unsafe input early
  client.py       # talk only to Open-Meteo
  server.py       # expose the tools over MCP
tests/            # automated checks
scripts/          # quick live smoke check
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

It runs over **stdio**, which is the normal setup for local MCP tools. The host app starts the server and talks to it.

### Example Cursor / Claude Desktop config

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

If you installed with `pip install -e .`, you can point `command` at `open-meteo-mcp` instead.

## Examples

### Example 1 — current weather

```text
get_current_weather(location="Johannesburg")
```

Successful response looks like:

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

```text
get_forecast(location="Cape Town", days=3)
```

That returns up to 3 daily high/low values.

### Example 3 — bad input gets rejected

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

Unit tests:

```bash
pytest -q
```

Live smoke check (needs internet, still no API key):

```bash
python scripts/smoke_check.py
```

### Fast path for reviewers

If you just want to confirm it works:

```bash
pip install -r requirements.txt
pip install -e .
pytest -q
python scripts/smoke_check.py
```

If both pass, the core behaviour and live Open-Meteo path are good.

## What could go wrong when an AI agent uses this?

This part mattered a lot to me. Once an AI can call a tool, you have to think about misuse — not just the happy path.

### 1) Bad input
An agent might pass a URL, random code, or nonsense instead of a city name.  
I validate location text first (length + allowed characters). Bad input fails fast and never hits Open-Meteo.

### 2) The API failing
Open-Meteo can time out or fail.  
I use timeouts, don’t follow redirects, and return a clear `{ "ok": false, "error": "..." }` response. No crash, and no invented weather.

### 3) The agent calling it in a weird way
Things I worried about:
- asking for a massive forecast window
- calling the API over and over
- trying to turn this into a general “fetch any website” tool

What I did about it:
- forecast days capped to **1–7**
- client locked to **Open-Meteo hosts only**
- tool descriptions that spell out valid input
- errors that tell the agent to retry/clarify instead of guessing

### 4) Ambiguous place names
“Springfield” could mean a lot of places.  
I take Open-Meteo’s best match and return the resolved place details, so you can see which location was used. If nothing matches, you get a clear not-found error.

## Design choices

- Small and correct beats big and half-finished  
- No API keys, so it’s easy and safe to try  
- Validate before calling the network  
- Return structured `ok` / `error` responses so failures are easy to handle  

## What I’d improve next

If I had another evening on this, I’d add:
- a small rate limit for noisy agents  
- optional lat/lon tools with the same strict checks  
- contract tests that freeze the tool schemas  

## License

MIT — feel free to reuse for learning and demos.
