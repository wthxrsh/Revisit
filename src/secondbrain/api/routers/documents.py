from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    UploadFile,
    status,
)

from secondbrain.api.auth_dependencies import get_current_user
from secondbrain.api.dependencies import get_document_service
from secondbrain.api.schemas import DeleteResponse, DocumentResponse
from secondbrain.models.user import User
from secondbrain.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    return service.upload(
        user_id=current_user.id,
        filename=file.filename,
        fileobj=file.file,
    )


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    return service.list_documents(current_user.id, limit=limit, offset=offset)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    return service.get(document_id, current_user.id)


@router.get("/{document_id}/status", response_model=DocumentResponse)
def get_document_status(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    return service.get(document_id, current_user.id)


@router.post("/{document_id}/process", response_model=DocumentResponse)
def process_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    return service.reprocess(document_id, current_user.id)


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    service.delete(document_id, current_user.id)
    return DeleteResponse(message="Document deleted successfully")
