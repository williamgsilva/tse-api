"""Malhas do IBGE (API de malhas v3, qualidade mínima), com cache em disco: os limites não mudam."""

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from ....shared.errors import UpstreamUnavailableError
from ..domain.models import MeshNotFound
from ..domain.ports import MeshSource

_QUERY = {"formato": "application/vnd.geo+json", "qualidade": "minima"}
PRECISION = 4  # ~10 m: suficiente para o mapa e reduz o GeoJSON pela metade


def _round(coordinates: Any) -> Any:
    if isinstance(coordinates, (int, float)):
        return round(coordinates, PRECISION)
    return [_round(c) for c in coordinates]


def _normalize(geojson: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "type": "Feature",
            "properties": {"codigo_ibge": int(f["properties"]["codarea"])},
            "geometry": {"type": f["geometry"]["type"], "coordinates": _round(f["geometry"]["coordinates"])},
        }
        for f in geojson.get("features", [])
    ]


class IbgeMeshSource(MeshSource):
    def __init__(self, base_url: str, cache_dir: Path, transport: httpx.AsyncBaseTransport | None = None):
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/", timeout=httpx.Timeout(60.0, connect=10.0), transport=transport
        )
        self._cache_dir = cache_dir
        self._lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self._http.aclose()

    async def fetch_states(self) -> list[dict[str, Any]]:
        return await self._cached("brasil-uf", "paises/BR", "UF")

    async def fetch_municipalities(self, ibge_state_code: int) -> list[dict[str, Any]]:
        return await self._cached(f"uf-{ibge_state_code}-municipios", f"estados/{ibge_state_code}", "municipio")

    async def _cached(self, name: str, path: str, subdivision: str) -> list[dict[str, Any]]:
        file = self._cache_dir / f"{name}.json"
        async with self._lock:
            if file.exists():
                features: list[dict[str, Any]] = json.loads(file.read_text())
                return features
            features = _normalize(await self._download(path, subdivision))
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(json.dumps(features, separators=(",", ":")))
            return features

    async def _download(self, path: str, subdivision: str) -> dict[str, Any]:
        try:
            response = await self._http.get(path, params={**_QUERY, "intrarregiao": subdivision})
        except httpx.HTTPError as exc:
            raise UpstreamUnavailableError(f"falha ao acessar a API de malhas do IBGE: {exc}") from exc
        if response.status_code == 404:
            raise MeshNotFound(f"malha não encontrada no IBGE: {path}")
        if response.status_code >= 400:
            raise UpstreamUnavailableError(f"IBGE respondeu {response.status_code} para {path}")
        data: dict[str, Any] = response.json()
        return data
