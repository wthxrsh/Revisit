from fastapi import APIRouter, Depends, status

from secondbrain.api.dependencies import get_auth_service
from secondbrain.api.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from secondbrain.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
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


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    access_token = auth_service.login(
        email=request.email,
        password=request.password,
    )

    return TokenResponse(access_token=access_token, token_type="bearer")
