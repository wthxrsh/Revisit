from fastapi import APIRouter, Depends, Query, status

from secondbrain.api.auth_dependencies import get_current_user
from secondbrain.api.dependencies import get_note_service
from secondbrain.api.schemas import (
    CreateNoteRequest,
    DeleteResponse,
    NoteResponse,
    UpdateNoteRequest,
)
from secondbrain.models.user import User
from secondbrain.services.note_service import NoteService

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    request: CreateNoteRequest,
    note_service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_current_user),
):
    return note_service.create_note(
        title=request.title,
        content=request.content,
        user_id=current_user.id,
    )


@router.get("", response_model=list[NoteResponse])
def get_notes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_current_user),
):
    return service.get_all_notes(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        search=search,
    )


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_current_user),
):
    return service.get_note(note_id, current_user.id)


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    request: UpdateNoteRequest,
    service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_current_user),
):
    return service.update_note(
        note_id,
        request.title,
        request.content,
        current_user.id,
    )


@router.delete("/{note_id}", response_model=DeleteResponse)
def delete_note(
    note_id: int,
    service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_current_user),
):
    service.delete_note(note_id, current_user.id)
    return DeleteResponse(message="Note deleted successfully")
