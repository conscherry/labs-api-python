# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0]
- Initial release with `LabsApiClient` and `AsyncLabsApiClient`.
- Server count alias normalization, telemetry headers and typed exceptions.
- Fix `AsyncLabsApiClient` response parsing and make `get_bot_by_id` a coroutine.
- Export `AsyncLabsApiClient` and `DEFAULT_BASE_URL` from the package.
- Send one stable `X-SDK-Instance-Id` per client instead of one per request.
- Share request, error and parameter handling between the sync and async clients.
- Treat a `guild_count` of `0` as a real value.
