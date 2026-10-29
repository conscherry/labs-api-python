from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote, urlsplit

import httpx

from ._version import __version__
from .exceptions import (
    LabsAPIAuthError,
    LabsAPIConnectionError,
    LabsAPIError,
    LabsAPIPermissionError,
    LabsAPIRateLimitError,
    LabsAPIRequestError,
)

DEFAULT_BASE_URL = "https://labs.conscherry.com/api/v1"


class LabsApiClient:
    """
    Synchronous client for the Discord Labs API.

    Public calls can be made without an API key.
    Authenticated calls require an API key.

    Args:
        api_key: Labs API key. Defaults to LABS_API_KEY.
        base_url: API base URL. Defaults to DEFAULT_BASE_URL.
        timeout: HTTP timeout in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 15.0,
    ):
        self.api_key = api_key or os.getenv("LABS_API_KEY")

        base_url = base_url.rstrip("/")

        parsed = urlsplit(base_url)

        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "base_url must be a valid HTTPS URL "
                "without credentials, query, or fragment."
            )

        self.base_url = base_url
        self.timeout = timeout
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            headers={
                "Accept": "application/json",
                "User-Agent": f"labs-api-python/{__version__}",
                "X-SDK-Name": "labs-api-python",
                "X-SDK-Version": __version__,
                "X-SDK-Lang": "python",
            },
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> LabsApiClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> Any:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("API path must start with one slash.")

        if "?" in path or "#" in path or "\\" in path:
            raise ValueError("Pass query parameters through params.")

        if authenticated and not self.api_key:
            raise LabsAPIAuthError(
                "An API key is required. Set LABS_API_KEY "
                "or pass api_key to LabsApiClient."
            )

        headers: dict[str, str] = {}

        if authenticated:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}{path}"

        try:
            response = self._client.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers,
            )

        except httpx.TimeoutException as exc:
            raise LabsAPIConnectionError("The Labs API request timed out.") from exc

        except httpx.RequestError as exc:
            raise LabsAPIConnectionError(
                f"Could not connect to the Labs API: {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError:
            data = None

        if not response.is_success:
            message = f"Labs API returned HTTP {response.status_code}"
            code = None

            if isinstance(data, dict):
                message = str(data.get("message") or data.get("error") or message)
                raw_code = data.get("code")
                if raw_code is not None:
                    code = str(raw_code)

            retry_after = None
            raw_retry = response.headers.get("Retry-After")

            if raw_retry:
                try:
                    retry_after = max(0.0, float(raw_retry))
                except ValueError:
                    retry_after = None

            error_class = LabsAPIRequestError

            if response.status_code in (401, 403):
                if response.status_code == 401:
                    error_class = LabsAPIAuthError
                else:
                    error_class = LabsAPIPermissionError

            elif response.status_code == 429:
                error_class = LabsAPIRateLimitError

            raise error_class(
                message,
                status_code=response.status_code,
                code=code,
                retry_after=retry_after,
                response=data,
            )

        if response.status_code == 204:
            return None

        if data is None:
            raise LabsAPIError(
                "The Labs API returned a successful response that was not valid JSON.",
                status_code=response.status_code,
            )

        return data

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> Any:
        """Send a GET request to an API path."""
        return self._request(
            "GET",
            path,
            params=params,
            authenticated=authenticated,
        )

    def post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> Any:
        """Send a POST request to an API path."""
        return self._request(
            "POST",
            path,
            json=body,
            authenticated=authenticated,
        )

    def list_bots(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        search: str | None = None,
        category: str | None = None,
        certified: bool | None = None,
        verified: bool | None = None,
        nsfw: bool | None = None,
    ) -> Any:
        """List public bots."""
        params = {
            key: value
            for key, value in {
                "limit": limit,
                "offset": offset,
                "sort": sort,
                "search": search,
                "category": category,
                "certified": certified,
                "verified": verified,
                "nsfw": nsfw,
            }.items()
            if value is not None
        }

        return self.get("/bots", params=params)

    def get_bot_by_id(self, bot_id: str) -> Any:
        """Get a public bot by ID."""
        if not bot_id:
            raise ValueError("bot_id cannot be empty.")

        bot_id = quote(bot_id, safe="")

        return self.get(f"/bots/{bot_id}")

    def list_users(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        search: str | None = None,
    ) -> Any:
        """List public users."""
        params = {
            key: value
            for key, value in {
                "limit": limit,
                "offset": offset,
                "sort": sort,
                "search": search,
            }.items()
            if value is not None
        }

        return self.get("/users", params=params)

    def get_website_stats(self) -> Any:
        """Get public website statistics."""
        return self.get("/website")

    def post_stats(
        self,
        *,
        bot_id: str,
        guild_count: int | None = None,
        user_count: int | None = None,
        shard_count: int | None = None,
        uptime: float | None = None,
        ping: float | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> Any:
        """
        Post bot statistics.

        Requires the write:stats permission.
        The API enforces its own validation and write limits.
        """
        if not bot_id:
            raise ValueError("bot_id cannot be empty.")

        body: dict[str, Any] = {
            "botId": bot_id,
        }

        optional_fields = {
            "guildCount": guild_count,
            "userCount": user_count,
            "shardCount": shard_count,
            "uptime": uptime,
            "ping": ping,
            "customFields": custom_fields,
        }

        body.update(
            {key: value for key, value in optional_fields.items() if value is not None}
        )

        return self.post(
            "/stats",
            body=body,
            authenticated=True,
        )

    def get_stats(
        self,
        *,
        bot_id: str,
        limit: int | None = None,
    ) -> Any:
        """Get bot statistics. Requires authentication."""
        if not bot_id:
            raise ValueError("bot_id cannot be empty.")

        params: dict[str, Any] = {"botId": bot_id}

        if limit is not None:
            params["limit"] = limit

        return self.get(
            "/stats",
            params=params,
            authenticated=True,
        )
