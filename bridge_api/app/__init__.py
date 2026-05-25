from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings
from app.routes import auth, chat, health, history, index, search, sources, upload, workspaces


def create_app() -> FastAPI:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    app = FastAPI(
        title="JAH AI Bridge API",
        description="Bridge HTTPS entre el frontend JAH AI y el cerebro RAG TUTOR_IA.",
        version="0.4.0",
    )

    class PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next) -> Response:
            response = await call_next(request)
            if request.headers.get("access-control-request-private-network", "").lower() == "true":
                response.headers["Access-Control-Allow-Private-Network"] = "true"
            return response

    app.add_middleware(PrivateNetworkAccessMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_origin_regex=settings.allowed_origin_regex,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Session-Id", "X-Requested-With", "Accept", "Origin"],
        expose_headers=["Access-Control-Allow-Private-Network"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(index.router)
    app.include_router(search.router)
    app.include_router(sources.router)
    app.include_router(upload.router)
    app.include_router(history.router)
    app.include_router(workspaces.router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        message = detail if isinstance(detail, str) else str(detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "ok": False,
                "error": message,
                "detail": detail,
            },
        )

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
