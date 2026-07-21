from __future__ import annotations

from fastapi import APIRouter

from api.auth import create_token
from api.schemas import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def issue_token(body: TokenRequest):
    token = create_token(body.user_id)
    return TokenResponse(access_token=token)
