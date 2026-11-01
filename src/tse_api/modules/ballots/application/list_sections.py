from ....shared.pagination import Page, paginate
from ....shared.uf import parse_uf
from ..domain.models import SectionSummary
from ..domain.ports import UrnFileSource, VotingEventDirectory


class ListSections:
    """Seções de uma UF com arquivos de urna publicados, com filtro por município/zona."""

    def __init__(self, events: VotingEventDirectory, source: UrnFileSource):
        self._events = events
        self._source = source

    async def execute(
        self,
        voting_event_code: int,
        uf: str,
        municipality: int | None = None,
        zone: int | None = None,
        limit: int = 1000,
        cursor: str | None = None,
    ) -> Page[SectionSummary]:
        event = await self._events.get(voting_event_code)
        sections = [
            s
            for s in await self._source.list_sections(event, parse_uf(uf))
            if (municipality is None or s.key.municipality == municipality) and (zone is None or s.key.zone == zone)
        ]
        return paginate(sections, limit, cursor)
