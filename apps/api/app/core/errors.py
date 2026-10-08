from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings

settings = get_settings()


class AppError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_payload(
    request: Request,
    *,
    code: str,
    message: str,
    details: Any | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": _request_id(request),
        }
    }


def _bind_error_context(request: Request, code: str, details: Any | None) -> None:
    request.state.error_code = code
    request.state.error_details = details


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        _bind_error_context(request, exc.code, exc.details)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                request,
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = exc.errors()
        _bind_error_context(request, "validation_error", details)
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                request,
                code="validation_error",
                message="Request validation failed",
                details=details,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "HTTP request failed"
        details = None if isinstance(exc.detail, str) else exc.detail
        code = f"http_{exc.status_code}"
        _bind_error_context(request, code, details)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                request,
                code=code,
                message=message,
                details=details,
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        details = repr(exc) if settings.debug else None
        _bind_error_context(request, "internal_server_error", details)
        return JSONResponse(
            status_code=500,
            content=_error_payload(
                request,
                code="internal_server_error",
                message="Internal server error",
                details=details,
            ),
        )
