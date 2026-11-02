from __future__ import annotations

import os
import uuid
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
DEFAULT_TIMEOUT = 15.0


def _compact(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _first_not_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


class LabsApiClientBase:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        telemetry: bool = True,
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
        self.telemetry = telemetry
        self._instance_id = str(uuid.uuid4())

    def _get_headers(self, authenticated: bool = False) -> dict[str, str]:
        headers = {"Accept": "application/json"}

        if authenticated:
            if not self.api_key:
                raise LabsAPIAuthError(
                    "An API key is required. Set LABS_API_KEY "
                    "or pass api_key to the client."
                )
            headers["Authorization"] = f"Bearer {self.api_key}"

        if self.telemetry:
            headers.update(
                {
                    "X-SDK-Name": "labs-api-python",
                    "X-SDK-Version": __version__,
                    "X-SDK-Lang": "python",
                    "X-SDK-Instance-Id": self._instance_id,
                }
            )

        return headers

    @staticmethod
    def _validate_path(path: str) -> None:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("API path must start with one slash.")

        if "?" in path or "#" in path or "\\" in path:
            raise ValueError("Pass query parameters through params.")

    def _normalize_response(self, data: Any) -> Any:
        if isinstance(data, list):
            return [self._normalize_response(item) for item in data]

        if not isinstance(data, dict):
            return data

        if "guildCount" in data or "serverCount" in data or "server_count" in data:
            value = _first_not_none(
                data.get("guildCount"),
                data.get("serverCount"),
                data.get("server_count"),
            )
            if value is not None:
                data["guildCount"] = value
                data["serverCount"] = value
                data["server_count"] = value

        for key, value in data.items():
            data[key] = self._normalize_response(value)

        return data

    def _parse_json(self, response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return None

    def _handle_response(self, response: httpx.Response) -> Any:
        data = self._parse_json(response)

        if not response.is_success:
            raise self._build_error(response, data)

        if response.status_code == 204:
            return None

        if data is None:
            raise LabsAPIError(
                "The Labs API returned a successful response that was not valid JSON.",
                status_code=response.status_code,
            )

        return self._normalize_response(data)

    @staticmethod
    def _build_error(response: httpx.Response, data: Any) -> LabsAPIError:
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

        error_class: type[LabsAPIError] = LabsAPIRequestError

        if response.status_code == 401:
            error_class = LabsAPIAuthError
        elif response.status_code == 403:
            error_class = LabsAPIPermissionError
        elif response.status_code == 429:
            error_class = LabsAPIRateLimitError

        return error_class(
            message,
            status_code=response.status_code,
            code=code,
            retry_after=retry_after,
            response=data,
        )

    @staticmethod
    def _list_bots_params(
        limit: int | None,
        offset: int | None,
        sort: str | None,
        search: str | None,
        category: str | None,
        certified: bool | None,
        verified: bool | None,
        nsfw: bool | None,
    ) -> dict[str, Any]:
        return _compact(
            {
                "limit": limit,
                "offset": offset,
                "sort": sort,
                "search": search,
                "category": category,
                "certified": certified,
                "verified": verified,
                "nsfw": nsfw,
            }
        )

    @staticmethod
    def _list_users_params(
        limit: int | None,
        offset: int | None,
        sort: str | None,
        search: str | None,
    ) -> dict[str, Any]:
        return _compact(
            {"limit": limit, "offset": offset, "sort": sort, "search": search}
        )

    @staticmethod
    def _bot_path(bot_id: str) -> str:
        if not bot_id:
            raise ValueError("bot_id cannot be empty.")
        return f"/bots/{quote(bot_id, safe='')}"

    @staticmethod
    def _stats_body(
        bot_id: str,
        guild_count: int | None,
        server_count: int | None,
        serverCount: int | None,
        user_count: int | None,
        shard_count: int | None,
        uptime: float | None,
        ping: float | None,
        custom_fields: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not bot_id:
            raise ValueError("bot_id cannot be empty.")

        return _compact(
            {
                "botId": bot_id,
                "guildCount": _first_not_none(guild_count, server_count, serverCount),
                "userCount": user_count,
                "shardCount": shard_count,
                "uptime": uptime,
                "ping": ping,
                "customFields": custom_fields,
            }
        )

    @staticmethod
    def _get_stats_params(bot_id: str, limit: int | None) -> dict[str, Any]:
        if not bot_id:
            raise ValueError("bot_id cannot be empty.")
        return _compact({"botId": bot_id, "limit": limit})


class LabsApiClient(LabsApiClientBase):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        telemetry: bool = True,
    ):
        super().__init__(api_key, base_url, timeout, telemetry)
        self._client = httpx.Client(timeout=timeout, follow_redirects=False)

    def close(self) -> None:
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
        self._validate_path(path)
        headers = self._get_headers(authenticated)

        try:
            response = self._client.request(
                method,
                f"{self.base_url}{path}",
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

        return self._handle_response(response)

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> Any:
        return self._request("GET", path, params=params, authenticated=authenticated)

    def post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> Any:
        return self._request("POST", path, json=body, authenticated=authenticated)

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
        params = self._list_bots_params(
            limit, offset, sort, search, category, certified, verified, nsfw
        )
        return self.get("/bots", params=params)

    def get_bot_by_id(self, bot_id: str) -> Any:
        return self.get(self._bot_path(bot_id))

    def list_users(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        search: str | None = None,
    ) -> Any:
        params = self._list_users_params(limit, offset, sort, search)
        return self.get("/users", params=params)

    def get_website_stats(self) -> Any:
        return self.get("/website")

    def post_stats(
        self,
        *,
        bot_id: str,
        guild_count: int | None = None,
        server_count: int | None = None,
        serverCount: int | None = None,
        user_count: int | None = None,
        shard_count: int | None = None,
        uptime: float | None = None,
        ping: float | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> Any:
        body = self._stats_body(
            bot_id,
            guild_count,
            server_count,
            serverCount,
            user_count,
            shard_count,
            uptime,
            ping,
            custom_fields,
        )
        return self.post("/stats", body=body, authenticated=True)

    def get_stats(self, *, bot_id: str, limit: int | None = None) -> Any:
        params = self._get_stats_params(bot_id, limit)
        return self.get("/stats", params=params, authenticated=True)


class AsyncLabsApiClient(LabsApiClientBase):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        telemetry: bool = True,
    ):
        super().__init__(api_key, base_url, timeout, telemetry)
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=False)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncLabsApiClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> Any:
        self._validate_path(path)
        headers = self._get_headers(authenticated)

        try:
            response = await self._client.request(
                method,
                f"{self.base_url}{path}",
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

        return self._handle_response(response)

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> Any:
        return await self._request(
            "GET", path, params=params, authenticated=authenticated
        )

    async def post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> Any:
        return await self._request(
            "POST", path, json=body, authenticated=authenticated
        )

    async def list_bots(
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
        params = self._list_bots_params(
            limit, offset, sort, search, category, certified, verified, nsfw
        )
        return await self.get("/bots", params=params)

    async def get_bot_by_id(self, bot_id: str) -> Any:
        return await self.get(self._bot_path(bot_id))

    async def list_users(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        search: str | None = None,
    ) -> Any:
        params = self._list_users_params(limit, offset, sort, search)
        return await self.get("/users", params=params)

    async def get_website_stats(self) -> Any:
        return await self.get("/website")

    async def post_stats(
        self,
        *,
        bot_id: str,
        guild_count: int | None = None,
        server_count: int | None = None,
        serverCount: int | None = None,
        user_count: int | None = None,
        shard_count: int | None = None,
        uptime: float | None = None,
        ping: float | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> Any:
        body = self._stats_body(
            bot_id,
            guild_count,
            server_count,
            serverCount,
            user_count,
            shard_count,
            uptime,
            ping,
            custom_fields,
        )
        return await self.post("/stats", body=body, authenticated=True)

    async def get_stats(self, *, bot_id: str, limit: int | None = None) -> Any:
        params = self._get_stats_params(bot_id, limit)
        return await self.get("/stats", params=params, authenticated=True)
