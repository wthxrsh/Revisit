from fastapi import APIRouter, Depends, Query

from secondbrain.api.auth_dependencies import get_current_user
from secondbrain.api.dependencies import (
    get_conversation_service,
    get_rag_service,
)
from secondbrain.api.schemas import (
    ChatRequest,
    ChatResponse,
    CitationResponse,
    ConversationDetailResponse,
    ConversationResponse,
    DeleteResponse,
    MessageResponse,
)
from secondbrain.models.user import User
from secondbrain.services.conversation_service import ConversationService
from secondbrain.services.rag_service import RagService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    service: RagService = Depends(get_rag_service),
    current_user: User = Depends(get_current_user),
):
    result = service.ask(
        user_id=current_user.id,
        question=request.question,
        conversation_id=request.conversation_id,
        top_k=request.top_k,
        document_ids=request.document_ids,
    )

    return ChatResponse(
        conversation_id=result.conversation_id,
        message_id=result.message_id,
        answer=result.answer,
        grounded=result.grounded,
        citations=[
            CitationResponse(
                document_id=citation.document_id,
                filename=citation.filename,
                page_number=citation.page_number,
                chunk_id=citation.chunk_id,
                chunk_index=citation.chunk_index,
                snippet=citation.snippet,
            )
            for citation in result.citations
        ],
    )


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user),
):
    return service.list_conversations(
        current_user.id, limit=limit, offset=offset
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
)
def get_conversation(
    conversation_id: int,
    service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user),
):
    conversation, messages = service.get(conversation_id, current_user.id)

    return ConversationDetailResponse(
        conversation=ConversationResponse.model_validate(conversation),
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.delete(
    "/conversations/{conversation_id}",
    response_model=DeleteResponse,
)
def delete_conversation(
    conversation_id: int,
    service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user),
):
    service.delete(conversation_id, current_user.id)
    return DeleteResponse(message="Conversation deleted successfully")
