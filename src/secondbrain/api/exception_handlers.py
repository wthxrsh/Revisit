import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from secondbrain.exceptions import (
    AuthenticationError,
    ConflictError,
    FileTooLargeError,
    InvalidCredentialsError,
    NotFoundError,
    ProviderError,
    SecondBrainError,
    UnsupportedFileTypeError,
    ValidationError,
)

logger = logging.getLogger(__name__)

_STATUS_BY_EXCEPTION: dict[type[SecondBrainError], tuple[int, str]] = {
    NotFoundError: (status.HTTP_404_NOT_FOUND, "not_found"),
    ValidationError: (status.HTTP_400_BAD_REQUEST, "validation_error"),
    ConflictError: (status.HTTP_409_CONFLICT, "conflict"),
    AuthenticationError: (status.HTTP_401_UNAUTHORIZED, "unauthorized"),
    InvalidCredentialsError: (
        status.HTTP_401_UNAUTHORIZED,
        "invalid_credentials",
    ),
    FileTooLargeError: (
        status.HTTP_413_CONTENT_TOO_LARGE,
        "file_too_large",
    ),
    UnsupportedFileTypeError: (
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "unsupported_media_type",
    ),
    ProviderError: (status.HTTP_503_SERVICE_UNAVAILABLE, "provider_error"),
}

_FALLBACK = (status.HTTP_400_BAD_REQUEST, "error")


def _resolve(exc: SecondBrainError) -> tuple[int, str]:
    for klass in type(exc).__mro__:
        if klass in _STATUS_BY_EXCEPTION:
            return _STATUS_BY_EXCEPTION[klass]
    return _FALLBACK


async def domain_error_handler(
    request: Request, exc: SecondBrainError
) -> JSONResponse:
    status_code, code = _resolve(exc)
    headers = (
        {"WWW-Authenticate": "Bearer"}
        if isinstance(exc, InvalidCredentialsError)
        else None
    )

    return JSONResponse(
        status_code=status_code,
        content={"error": code, "message": str(exc)},
        headers=headers,
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": "request_validation_error",
            "message": "The request payload is invalid",
            "details": exc.errors(),
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": str(exc.detail)},
        headers=getattr(exc, "headers", None),
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled error while handling %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
        },
    )
