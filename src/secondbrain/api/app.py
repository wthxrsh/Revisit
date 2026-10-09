import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from secondbrain.api.exception_handlers import (
    domain_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from secondbrain.api.routers import auth, chat, documents, health, notes
from secondbrain.config import settings
from secondbrain.exceptions import SecondBrainError
from secondbrain.logging_config import configure_logging

logger = logging.getLogger(__name__)


def _register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SecondBrainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


def _register_middleware(app: FastAPI) -> None:
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    max_request_size = settings.max_request_size_bytes

    @app.middleware("http")
    async def enforce_request_size(request: Request, call_next):
        content_length = request.headers.get("content-length")

        if content_length is not None:
            try:
                if int(content_length) > max_request_size:
                    limit_mb = settings.max_request_size_mb
                    return JSONResponse(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        content={
                            "error": "request_too_large",
                            "message": (
                                f"Request exceeds the maximum size of "
                                f"{limit_mb} MB"
                            ),
                        },
                    )
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "invalid_content_length",
                        "message": "Invalid Content-Length header",
                    },
                )

        return await call_next(request)


def create_app() -> FastAPI:
    configure_logging()
    settings.validate()

    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        description=(
            "Personal knowledge management with notes, PDF ingestion, "
            "semantic retrieval, and a grounded RAG assistant."
        ),
    )

    _register_middleware(app)
    _register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(notes.router)
    app.include_router(documents.router)
    app.include_router(chat.router)

    return app


app = create_app()
