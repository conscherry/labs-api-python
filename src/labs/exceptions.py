class LabsAPIError(Exception):
    """Base exception for Labs API errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        retry_after: float | None = None,
        response: object = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.retry_after = retry_after
        self.response = response


class LabsAPIAuthError(LabsAPIError):
    """Authentication failed or credentials are missing."""


class LabsAPIPermissionError(LabsAPIError):
    """The API key lacks the required permission."""


class LabsAPIRateLimitError(LabsAPIError):
    """The API rate limit was exceeded."""


class LabsAPIRequestError(LabsAPIError):
    """The API rejected a request."""


class LabsAPIConnectionError(LabsAPIError):
    """A connection or timeout error occurred."""
