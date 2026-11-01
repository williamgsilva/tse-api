from ..domain.models import VotingEvent
from ..domain.ports import ElectionDataSource


class ListVotingEvents:
    def __init__(self, source: ElectionDataSource):
        self._source = source

    async def execute(self, year: int | None) -> list[VotingEvent]:
        return (await self._source.fetch_catalog()).voting_events_of_year(year)
