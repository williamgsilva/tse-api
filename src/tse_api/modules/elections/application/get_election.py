from ..domain.models import Election
from ..domain.ports import ElectionDataSource


class GetElection:
    def __init__(self, source: ElectionDataSource):
        self._source = source

    async def execute(self, code: int) -> Election:
        return (await self._source.fetch_catalog()).election(code)
