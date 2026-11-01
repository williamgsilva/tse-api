from ..domain.models import VotingEvent
from ..domain.ports import ElectionDataSource


class GetVotingEvent:
    def __init__(self, source: ElectionDataSource):
        self._source = source

    async def execute(self, code: int) -> VotingEvent:
        return (await self._source.fetch_catalog()).voting_event(code)
