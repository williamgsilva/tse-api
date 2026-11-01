from dataclasses import dataclass

from ....shared.uf import parse_uf
from ..domain.models import SectionKey
from ..domain.ports import UrnFileSource, VotingEventDirectory


@dataclass(frozen=True)
class DownloadedFile:
    name: str
    content: bytes


class DownloadUrnFile:
    """Arquivo original da transmissão vigente da urna (bu, rdv, log, vota...)."""

    def __init__(self, events: VotingEventDirectory, source: UrnFileSource):
        self._events = events
        self._source = source

    async def execute(
        self, voting_event_code: int, uf: str, municipality: int, zone: int, section: int, kind: str
    ) -> DownloadedFile:
        event = await self._events.get(voting_event_code)
        key = SectionKey(parse_uf(uf), municipality, zone, section)
        status = await self._source.fetch_section_status(event, key)
        file_set, urn_file = status.current_file(kind)
        return DownloadedFile(urn_file.name, await self._source.fetch_file(event, key, file_set, urn_file))
