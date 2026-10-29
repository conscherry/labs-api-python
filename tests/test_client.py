import httpx
import pytest

from labs import (
    LabsAPIAuthError,
    LabsApiClient,
    LabsAPIRateLimitError,
)


def make_client(handler, api_key=None):
    client = LabsApiClient(api_key=api_key)

    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    return client


def test_list_bots():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path.endswith("/bots")
        assert request.url.params["limit"] == "5"

        return httpx.Response(
            200,
            json={"data": [{"id": "123", "name": "Test"}]},
        )

    client = make_client(handler)

    try:
        result = client.list_bots(limit=5)
        assert result["data"][0]["name"] == "Test"
    finally:
        client.close()


def test_authenticated_request():
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test-key"

        return httpx.Response(200, json={"success": True})

    client = make_client(handler, api_key="test-key")

    try:
        result = client.get("/stats", authenticated=True)
        assert result["success"] is True
    finally:
        client.close()


def test_missing_api_key():
    client = make_client(lambda request: httpx.Response(200))

    try:
        with pytest.raises(LabsAPIAuthError):
            client.get("/stats", authenticated=True)
    finally:
        client.close()


def test_rate_limit():
    def handler(request):
        return httpx.Response(
            429,
            headers={"Retry-After": "60"},
            json={"error": "Rate limit exceeded"},
        )

    client = make_client(handler)

    try:
        with pytest.raises(LabsAPIRateLimitError) as exc:
            client.get("/bots")

        assert exc.value.status_code == 429
        assert exc.value.retry_after == 60
    finally:
        client.close()
