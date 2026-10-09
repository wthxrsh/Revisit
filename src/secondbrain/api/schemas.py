from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateNoteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class UpdateNoteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


class DeleteResponse(BaseModel):
    message: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    file_size: int
    mime_type: str
    status: str
    page_count: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None


class CitationResponse(BaseModel):
    document_id: int
    filename: str
    page_number: int | None
    chunk_id: int | None
    chunk_index: int
    snippet: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)
    document_ids: list[int] | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    grounded: bool
    citations: list[CitationResponse]


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    citations: list[dict] | None
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[MessageResponse]
