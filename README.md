# Discord Labs Python SDK

A user-friendly Python client for the [Discord Labs API](https://labs.conscherry.com/developers/docs/v1). This package makes it simple to fetch public data (bots, users, website stats) and post authenticated bot statistics.

[![Python](https://img.shields.io/pypi/pyversions/labs-api-python)](https://pypi.org/project/labs-api-python/)
[![PyPI](https://img.shields.io/pypi/v/labs-api-python)](https://pypi.org/project/labs-api-python/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Links

- [Conscherry](https://conscherry.com/)
- [Discord Labs](https://labs.conscherry.com/)
- [Labs API Documentation](https://labs.conscherry.com/developers/docs/v1)
- [Labs API Source](https://github.com/conscherry/labs-api-python)
- [JavaScript SDK on npm](https://www.npmjs.com/package/@conscherry/labs-api)
- [Python SDK on PyPI](https://pypi.org/project/labs-api-python/)


## Installation

```bash
python -m pip install labs-api-python
```

## Quick start

### Synchronous Client

```python
from labs import LabsApiClient

with LabsApiClient() as client:
    bots = client.list_bots(limit=5)
    print(bots)
```

### Asynchronous Client

```python
import asyncio
from labs import AsyncLabsApiClient

async def main():
    async with AsyncLabsApiClient() as client:
        bots = await client.list_bots(limit=5)
        print(bots)

asyncio.run(main())
```

## Client options

| Option | Type | Default |
| --- | --- | --- |
| `api_key` | `str` | `LABS_API_KEY` environment variable |
| `base_url` | `str` (HTTPS only) | `https://labs.conscherry.com/api/v1` |
| `timeout` | `float` (seconds) | `15.0` |
| `telemetry` | `bool` | `True` |

Both `LabsApiClient` and `AsyncLabsApiClient` accept the same options and expose the same methods. Close clients with a `with` / `async with` block or call `close()`.

## Authentication

Public endpoints do not require an API key.

For authenticated requests, configure `LABS_API_KEY` in your environment:

**PowerShell**
```powershell
$env:LABS_API_KEY = "YOUR_API_KEY"
```

**Linux/macOS**
```bash
export LABS_API_KEY="YOUR_API_KEY"
```

Or provide the key directly:

```python
from labs import LabsApiClient

client = LabsApiClient(api_key="YOUR_API_KEY")
```

Never expose your API key in client-side applications or public repositories.

## API examples

### List bots

```python
with LabsApiClient() as client:
    result = client.list_bots(limit=10)
    print(result)
```

### Get a bot

```python
with LabsApiClient() as client:
    result = client.get_bot_by_id("YOUR_BOT_ID")
    print(result)
```

### List users

```python
with LabsApiClient() as client:
    result = client.list_users(limit=10)
    print(result)
```

### Website statistics

```python
with LabsApiClient() as client:
    result = client.get_website_stats()
    print(result)
```

### Post bot stats

```python
with LabsApiClient() as client:
    # Supports guild_count, server_count, and serverCount aliases
    result = client.post_stats(
        bot_id="YOUR_BOT_ID",
        server_count=100,
        user_count=5000,
    )
    print(result)
```

Stats submission requires appropriate API permissions.

### Generic requests

```python
with LabsApiClient() as client:
    result = client.get("/custom", params={"q": "search"})
    print(result)
```

Authenticated request:

```python
with LabsApiClient() as client:
    result = client.post(
        "/admin",
        body={"action": "rebuild"},
        authenticated=True,
    )
```

Paths must start with a single `/` and must not contain a query string; pass query values through `params`. The async client exposes the same helpers as coroutines. Only use endpoints and request bodies supported by your API credentials and documentation.

## Error handling

`LabsAPIError` is the base class. `LabsAPIAuthError` covers 401 or a missing key, `LabsAPIPermissionError` covers 403, `LabsAPIRateLimitError` covers 429, `LabsAPIRequestError` covers other HTTP errors and `LabsAPIConnectionError` covers timeouts and network failures. Every error exposes `status_code`, `code`, `retry_after` and `response`.

```python
from labs import (
    LabsApiClient,
    LabsAPIError,
    LabsAPIRateLimitError,
)

try:
    with LabsApiClient() as client:
        result = client.list_bots()
        print(result)

except LabsAPIRateLimitError as exc:
    print("Rate limited:", exc.retry_after)

except LabsAPIError as exc:
    print("Labs API error:", exc)
```

## Telemetry

This client sends a small set of telemetry headers by default to identify the SDK and runtime to your API: `X-SDK-Name`, `X-SDK-Version`, `X-SDK-Lang` and `X-SDK-Instance-Id` (a random UUID generated once per client).

To disable telemetry, pass `telemetry=False` when creating the client:

```python
client = LabsApiClient(telemetry=False)
```

## Development

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest -q
```

## License

MIT
