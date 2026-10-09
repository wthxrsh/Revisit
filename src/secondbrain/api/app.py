from fastapi import FastAPI, Query

from secondbrain.api.auth_dependencies import get_current_user
from secondbrain.models.note import Note
from secondbrain.logging_config import configure_logging
from secondbrain.repositories.in_memory_note_repository import (
    InMemoryNoteRepository,
)
from secondbrain.repositories.postgres_user_repository import PostgresUserRepository
from secondbrain.services.auth_service import AuthService
from secondbrain.services.note_service import NoteService
from fastapi import HTTPException

from secondbrain.exceptions import NoteNotFoundError, InvalidNoteError, UserAlreadyExistsError, InvalidCredentialsError
from fastapi import Depends, FastAPI

from sqlalchemy.orm import Session

from secondbrain.database.dependencies import get_db
from secondbrain.repositories.postgres_note_repository import (
    PostgresNoteRepository,
)
from secondbrain.api.exception_handlers import (
    duplicate_note_handler,
    invalid_note_handler,
    note_not_found_handler, user_already_exists_handler, invalid_credentials_handler,
)

from secondbrain.exceptions import (
    InvalidNoteError,
    NoteAlreadyExistsError,
    NoteNotFoundError,
)
from secondbrain.services.note_service import NoteService
configure_logging()

app = FastAPI(
    title="SecondBrain",
    version="0.1.0",
)

app.add_exception_handler(
    NoteNotFoundError,
    note_not_found_handler,
)

app.add_exception_handler(
    InvalidNoteError,
    invalid_note_handler,
)

app.add_exception_handler(
    NoteAlreadyExistsError,
    duplicate_note_handler,
)

app.add_exception_handler(
    UserAlreadyExistsError,
    user_already_exists_handler,
)

app.add_exception_handler(
    InvalidCredentialsError,
    invalid_credentials_handler,
)


def get_note_service(
    db: Session = Depends(get_db),
) -> NoteService:
    repository = PostgresNoteRepository(db)
    return NoteService(repository)

@app.get("/health")
def health_check():
    return {"status": "ok"}

from secondbrain.api.schemas import CreateNoteRequest, NoteResponse, DeleteNoteResponse, UpdateNoteRequest, \
    UserResponse, RegisterRequest, TokenResponse, LoginRequest

from fastapi import status


@app.post(
    "/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    request: CreateNoteRequest,
    note_service: NoteService = Depends(get_note_service),
    current_user=Depends(get_current_user),
):
    return note_service.create_note(
        note_id=request.id,
        title=request.title,
        content=request.content,
        user_id=current_user.id,
    )

@app.get(
    "/notes",
    response_model=list[NoteResponse],
)
def get_notes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, min_length=1),
    service: NoteService = Depends(get_note_service),
    current_user=Depends(get_current_user),
):
    return service.get_all_notes(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        search=search,
    )

@app.get(
    "/notes/{note_id}",
    response_model=NoteResponse,
)
def get_note(
    note_id: int,
    service: NoteService = Depends(get_note_service),
    current_user=Depends(get_current_user),
):
    return service.get_note(note_id, current_user.id)


@app.delete(
    "/notes/{note_id}",
    response_model=DeleteNoteResponse,
)
def delete_note(
    note_id: int,
    service: NoteService = Depends(get_note_service),
    current_user=Depends(get_current_user),
):
    service.delete_note(note_id, current_user.id)

    return {
        "message": "Note deleted successfully"
    }

@app.put(
    "/notes/{note_id}",
    response_model=NoteResponse,
)
def update_note(
    note_id: int,
    request: UpdateNoteRequest,
    service: NoteService = Depends(get_note_service),
    current_user=Depends(get_current_user),
):
    return service.update_note(
        note_id,
        request.title,
        request.content,
        current_user.id,
    )

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repository = PostgresUserRepository(db)
    return AuthService(user_repository)

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.register(
        email=request.email,
        password=request.password,
    )

@app.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    access_token = auth_service.login(
        email=request.email,
        password=request.password,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }