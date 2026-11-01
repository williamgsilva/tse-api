import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

import httpx
from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..modules.ballots.interfaces.http import build_router as ballots_router
from ..modules.elections.interfaces.http import build_router as elections_router
from ..modules.geography.interfaces.http import build_router as geography_router
from ..modules.open_data.interfaces.http import build_router as open_data_router
from ..shared.config import Settings
from ..shared.errors import AppError
from ..shared.observability import configure_logging
from .container import ApiContainer, build_api_container
from .problems import register_problem_handlers
from .spa import mount_frontend

logger = logging.getLogger("tse_api.http")

API_PREFIX = "/v1"


def _version() -> str:
    try:
        return version("tse-api")
    except PackageNotFoundError:
        return "0.0.0"


def _health_router(container: ApiContainer, settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/health", tags=["infra"])

    @router.get("/live", summary="Processo vivo")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/ready", summary="Dependências disponíveis (portal do TSE)")
    async def ready() -> JSONResponse:
        checks = {"base_local": "ok" if settings.database_path.exists() else "vazia"}
        try:
            await container.elections.list_voting_events.execute(None)
            checks["portal_tse"] = "ok"
        except AppError as exc:
            checks["portal_tse"] = exc.detail
        status = 200 if checks["portal_tse"] == "ok" else 503
        return JSONResponse({"status": "ok" if status == 200 else "degradado", "checks": checks}, status_code=status)

    return router


def create_app(
    settings: Settings | None = None,
    tse_transport: httpx.AsyncBaseTransport | None = None,
    ibge_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level, settings.log_format)
    container = build_api_container(settings, tse_transport, ibge_transport)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await container.tse_client.aclose()
        await container.mesh_source.aclose()

    app = FastAPI(
        title="TSE API",
        version=_version(),
        description=(
            "Dados públicos do Tribunal Superior Eleitoral: eleições, resultados totalizados, boletins de urna "
            "por seção (decodificados do arquivo oficial) e consultas agregadas sobre os CSVs de dados abertos."
        ),
        lifespan=lifespan,
    )
    register_problem_handlers(app)

    @app.middleware("http")
    async def request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        logger.info(
            "requisição",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "ms": round((time.perf_counter() - started) * 1000, 1),
                "traceId": request.state.request_id,
            },
        )
        return response

    if settings.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["GET"])

    app.include_router(_health_router(container, settings))
    for router in (
        elections_router(container.elections),
        ballots_router(container.ballots),
        geography_router(container.geography),
        open_data_router(container.open_data),
    ):
        app.include_router(router, prefix=API_PREFIX)

    mount_frontend(app, settings.frontend_dist, reserved_prefixes=(API_PREFIX, "/health", "/docs", "/openapi.json"))
    return app
