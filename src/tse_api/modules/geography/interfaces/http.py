from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..application.get_municipalities_mesh import GetMunicipalitiesMesh
from ..application.get_states_mesh import GetStatesMesh

# Limites geográficos praticamente não mudam: o navegador pode guardar por um dia.
CACHE_HEADERS = {"Cache-Control": "public, max-age=86400"}
GEOJSON = "application/geo+json"


@dataclass(frozen=True)
class GeographyUseCases:
    get_states_mesh: GetStatesMesh
    get_municipalities_mesh: GetMunicipalitiesMesh


def build_router(use_cases: GeographyUseCases) -> APIRouter:
    router = APIRouter(prefix="/mapas", tags=["mapas (malhas do IBGE)"])
    schema: dict[int | str, dict[str, Any]] = {
        200: {"content": {GEOJSON: {}}, "description": "GeoJSON FeatureCollection"}
    }

    @router.get("/brasil", summary="Mapa do Brasil por UF (propriedades: uf, regiao, codigo_ibge)", responses=schema)
    async def states_mesh() -> JSONResponse:
        mesh = await use_cases.get_states_mesh.execute()
        return JSONResponse(mesh.as_geojson(), media_type=GEOJSON, headers=CACHE_HEADERS)

    @router.get("/{uf}", summary="Mapa de uma UF por município (propriedade: codigo_ibge)", responses=schema)
    async def municipalities_mesh(uf: str) -> JSONResponse:
        mesh = await use_cases.get_municipalities_mesh.execute(uf)
        return JSONResponse(mesh.as_geojson(), media_type=GEOJSON, headers=CACHE_HEADERS)

    return router
