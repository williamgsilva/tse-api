"""Cliente HTTP do portal de resultados do TSE, compartilhado pelos adaptadores dos módulos."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from .config import Settings
from .errors import UpstreamUnavailableError

logger = logging.getLogger(__name__)


class TseFileNotFound(Exception):
    """O arquivo não existe no portal (o bucket responde 403/404 com NoSuchKey)."""

    def __init__(self, path: str):
        super().__init__(path)
        self.path = path


class TseHttpClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self._settings = settings
        self._http = httpx.AsyncClient(
            base_url=self.base_url + "/",
            timeout=httpx.Timeout(30.0, connect=10.0),
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
            transport=transport,
        )
        self._semaphore = asyncio.Semaphore(settings.max_upstream_concurrency)
        self._json_cache: dict[str, tuple[float, Any]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    @property
    def base_url(self) -> str:
        return self._settings.tse_results_base_url.rstrip("/")

    def url_for(self, path: str) -> str:
        return f"{self.base_url}/{path}"

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get(self, path: str) -> httpx.Response:
        async with self._semaphore:
            try:
                response = await self._http.get(path)
            except httpx.HTTPError as exc:
                logger.warning("falha ao acessar o TSE", extra={"path": path, "error": str(exc)})
                raise UpstreamUnavailableError(f"erro de rede ao acessar {path}") from exc
        if response.status_code in (403, 404):
            raise TseFileNotFound(path)
        if response.status_code >= 400:
            raise UpstreamUnavailableError(f"TSE respondeu {response.status_code} para {path}")
        return response

    async def get_json(self, path: str) -> Any:
        cached = self._fresh(path)
        if cached is not None:
            return cached
        # Evita requisições simultâneas ao mesmo arquivo grande (ex.: seções de SP).
        async with self._locks.setdefault(path, asyncio.Lock()):
            cached = self._fresh(path)
            if cached is not None:
                return cached
            data = (await self._get(path)).json()
            self._json_cache[path] = (time.monotonic() + self._settings.json_cache_ttl_seconds, data)
            return data

    def _fresh(self, path: str) -> Any | None:
        entry = self._json_cache.get(path)
        return entry[1] if entry and entry[0] > time.monotonic() else None

    async def get_bytes(self, path: str, persist: bool = False) -> bytes:
        """Baixa um binário; com ``persist`` guarda em disco (arquivos de urna não mudam após publicados)."""
        local: Path | None = self._settings.cache_dir / path if persist else None
        if local and local.exists():
            return local.read_bytes()
        content = (await self._get(path)).content
        if local:
            local.parent.mkdir(parents=True, exist_ok=True)
            partial = local.with_suffix(local.suffix + ".part")
            partial.write_bytes(content)
            partial.replace(local)
        return content
