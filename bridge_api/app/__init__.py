from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import chat, health, history, index, search, sources, upload


def create_app() -> FastAPI:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    app = FastAPI(
        title="JAH AI Bridge API",
        description="Bridge local entre el frontend JAH AI y el cerebro RAG TUTOR_IA.",
        version="0.4.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_origin_regex=settings.allowed_origin_regex,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(index.router)
    app.include_router(search.router)
    app.include_router(sources.router)
    app.include_router(upload.router)
    app.include_router(history.router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "error": "Solicitud invalida.",
                "detail": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request.app.logger.exception("Unhandled API error: %s", exc) if hasattr(request.app, "logger") else None
        logging.getLogger("jah_ai_bridge").exception("Unhandled API error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "Error interno del bridge JAH AI.",
                "detail": str(exc),
            },
        )

    return app
