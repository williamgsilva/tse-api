"""Erros HTTP no formato Problem Details (RFC 9457), com o ``traceId`` da requisição."""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..shared.errors import AppError

logger = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"


def problem(request: Request, status: int, slug: str, title: str, detail: str | None, **extra: Any) -> JSONResponse:
    body = {
        "type": f"/problems/{slug}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "traceId": getattr(request.state, "request_id", None),
        **extra,
    }
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


def register_problem_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError) -> JSONResponse:
        if exc.status >= 500:
            logger.warning("erro de dependência", extra={"slug": exc.slug, "detail": exc.detail})
        return problem(request, exc.status, exc.slug, exc.title, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"campo": ".".join(str(p) for p in e["loc"]), "mensagem": e["msg"]} for e in exc.errors()]
        return problem(request, 422, "invalid-request", "Requisição inválida", "parâmetros inválidos", errors=errors)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        title = HTTPStatus(exc.status_code).phrase
        return problem(request, exc.status_code, f"http-{exc.status_code}", title, str(exc.detail))

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("erro inesperado", extra={"path": request.url.path})
        return problem(request, 500, "internal-error", "Erro interno", "erro inesperado; consulte o traceId nos logs")
