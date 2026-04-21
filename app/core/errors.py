"""Global API exception handlers."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.schemas import ErrorDetail, ErrorResponse


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle all HTTPException instances with standard contract."""
        code_map = {
            400: "BAD_REQUEST",
            404: "NOT_FOUND",
            429: "RATE_LIMIT_EXCEEDED",
            503: "CONCURRENCY_LIMIT_EXCEEDED",
            500: "INTERNAL_ERROR",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(code=code, message=str(exc.detail))
            ).model_dump(exclude_none=True),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle non-HTTPException errors."""
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="UNKNOWN_ERROR", message=str(exc))
            ).model_dump(exclude_none=True),
        )
