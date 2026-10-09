from fastapi import Request
from fastapi.responses import JSONResponse
from secondbrain.exceptions import UserAlreadyExistsError, InvalidCredentialsError
from secondbrain.exceptions import (
    InvalidNoteError,
    NoteAlreadyExistsError,
    NoteNotFoundError,
)


async def note_not_found_handler(
    request: Request,
    exc: NoteNotFoundError,
) -> JSONResponse:

    return JSONResponse(
        status_code=404,
        content={
            "error": "note_not_found",
            "message": str(exc),
        },
    )


async def invalid_note_handler(
    request: Request,
    exc: InvalidNoteError,
) -> JSONResponse:

    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_note",
            "message": str(exc),
        },
    )


async def duplicate_note_handler(
    request: Request,
    exc: NoteAlreadyExistsError,
) -> JSONResponse:

    return JSONResponse(
        status_code=409,
        content={
            "error": "note_already_exists",
            "message": str(exc),
        },
    )

async def user_already_exists_handler(
    request: Request,
    exc: UserAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": "user_already_exists",
            "message": str(exc),
        },
    )

async def invalid_credentials_handler(
    request: Request,
    exc: InvalidCredentialsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "error": "invalid_credentials",
            "message": str(exc),
        },
        headers={"WWW-Authenticate": "Bearer"},
    )