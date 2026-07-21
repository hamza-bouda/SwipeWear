from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    detail: str | None = None


def error_response(status_code: int, error_code: str, message: str, detail: str | None = None):
    raise HTTPException(
        status_code=status_code,
        detail=ErrorResponse(error_code=error_code, message=message, detail=detail).model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    body = ErrorResponse(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
    )
    return JSONResponse(status_code=500, content=body.model_dump())
