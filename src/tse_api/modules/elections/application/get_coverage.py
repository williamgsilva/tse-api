from ....shared.uf import parse_uf
from ..domain.models import Coverage
from ..domain.ports import ElectionDataSource


class GetCoverage:
    def __init__(self, source: ElectionDataSource):
        self._source = source

    async def execute(self, election_code: int, uf: str) -> Coverage:
        election = (await self._source.fetch_catalog()).election(election_code)
        return await self._source.fetch_coverage(election, parse_uf(uf, allow_national=True))
