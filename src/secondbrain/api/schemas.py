from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class CreateNoteRequest(BaseModel):
    id: int
    title: str
    content: str


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


class DeleteNoteResponse(BaseModel):
    message: str

class UpdateNoteRequest(BaseModel):
    title: str
    content: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str