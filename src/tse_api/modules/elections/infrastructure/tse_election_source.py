from typing import Any

from ....shared.tse_http import TseFileNotFound, TseHttpClient
from ..domain.models import Catalog, Coverage, Election, ElectionResult, Municipality, ResultNotPublished
from ..domain.ports import ElectionDataSource
from . import tse_json_mapper as mapper

CATALOG_PATH = "comum/config/ele-c.json"


def municipalities_path(e: Election) -> str:
    return f"{e.cycle}/{e.code}/config/mun-e{e.code:06d}-cm.json"


def coverage_path(e: Election, uf: str) -> str:
    return f"{e.cycle}/{e.code}/dados/{uf}/{uf}-e{e.code:06d}-ab.json"


def result_path(e: Election, uf: str, office_code: int, municipality_code: int | None = None) -> str:
    scope = f"{uf}{municipality_code:05d}" if municipality_code else uf
    return f"{e.cycle}/{e.code}/dados/{uf}/{scope}-c{office_code:04d}-e{e.code:06d}-u.json"


class TseElectionSource(ElectionDataSource):
    """Lê os JSONs do portal de resultados do TSE."""

    def __init__(self, client: TseHttpClient):
        self._client = client

    async def _json(self, path: str) -> Any:
        try:
            return await self._client.get_json(path)
        except TseFileNotFound as exc:
            raise ResultNotPublished(f"arquivo não publicado pelo TSE: {exc.path}") from exc

    async def fetch_catalog(self) -> Catalog:
        return mapper.map_catalog(await self._json(CATALOG_PATH))

    async def fetch_municipalities(self, election: Election) -> list[Municipality]:
        return mapper.map_municipalities(await self._json(municipalities_path(election)))

    async def fetch_result(
        self, election: Election, uf: str, office_code: int, municipality_code: int | None
    ) -> ElectionResult:
        return mapper.map_result(await self._json(result_path(election, uf, office_code, municipality_code)))

    async def fetch_coverage(self, election: Election, uf: str) -> Coverage:
        return mapper.map_coverage(await self._json(coverage_path(election, uf)))
