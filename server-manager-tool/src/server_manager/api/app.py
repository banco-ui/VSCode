"""FastAPI Application (Phase 8/10C).

Server Manager REST API application object.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .routes import router
from .scheduler_routes import router as scheduler_router
from .schemas import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Server Manager REST API",
        description=(
            "Server hardware inventory collection, verification, and query API. "
            "External systems (e.g. TBMS) integrate via this HTTP boundary."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Register routes
    app.include_router(router)
    app.include_router(scheduler_router)

    # ── Error handlers ────────────────────────────────────────────────

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        detail = exc.detail if hasattr(exc, "detail") else "Not found"
        if isinstance(detail, dict) and "code" in detail:
            return JSONResponse(
                status_code=404,
                content={"error": detail},
            )
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": str(detail), "details": {}}},
        )

    @app.exception_handler(400)
    async def bad_request_handler(request: Request, exc):
        detail = exc.detail if hasattr(exc, "detail") else "Bad request"
        if isinstance(detail, dict) and "code" in detail:
            return JSONResponse(
                status_code=400,
                content={"error": detail},
            )
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "BAD_REQUEST", "message": str(detail), "details": {}}},
        )

    @app.exception_handler(422)
    async def validation_handler(request: Request, exc):
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "details": {}}},
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        logger.error("Internal error: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred", "details": {}}},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred", "details": {}}},
        )

    return app


# Module-level app for uvicorn: `uvicorn server_manager.api.app:app`
app = create_app()
