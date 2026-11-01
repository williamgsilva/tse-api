from ....shared.uf import parse_uf
from ..domain.models import Municipality
from ..domain.ports import ElectionDataSource


class ListMunicipalities:
    def __init__(self, source: ElectionDataSource):
        self._source = source

    async def execute(self, election_code: int, uf: str | None) -> list[Municipality]:
        election = (await self._source.fetch_catalog()).election(election_code)
        municipalities = await self._source.fetch_municipalities(election)
        if uf is None:
            return municipalities
        wanted = parse_uf(uf)
        return [m for m in municipalities if m.uf == wanted]
