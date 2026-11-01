from ....shared.uf import parse_uf
from ..domain.models import SectionKey, SectionStatus
from ..domain.ports import UrnFileSource, VotingEventDirectory


class GetSectionStatus:
    def __init__(self, events: VotingEventDirectory, source: UrnFileSource):
        self._events = events
        self._source = source

    async def execute(
        self, voting_event_code: int, uf: str, municipality: int, zone: int, section: int
    ) -> SectionStatus:
        event = await self._events.get(voting_event_code)
        return await self._source.fetch_section_status(event, SectionKey(parse_uf(uf), municipality, zone, section))
