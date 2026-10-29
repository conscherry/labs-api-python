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

```python
from labs import LabsApiClient

with LabsApiClient() as client:
    bots = client.list_bots(limit=5)
    print(bots)
```

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
    result = client.post_stats(
        bot_id="YOUR_BOT_ID",
        guild_count=100,
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

Only use endpoints and request bodies supported by your API credentials and documentation.

## Error handling

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

## Development

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest -q
```

## Links

- Website: https://labs.conscherry.com/
- API docs: https://labs.conscherry.com/developers/docs/v1
- Source: https://github.com/conscherry/labs-api-python
- npm SDK: https://www.npmjs.com/package/@conscherry/labs-api-python

## License

MIT
