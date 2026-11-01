from dataclasses import dataclass
from datetime import time

from ..domain.ports import UrnLogReader
from ..domain.timeline import (
    LateVoteEstimate,
    VoteTimeline,
    build_timeline,
    count_after,
    default_offset_to_brasilia,
    estimate_late_votes,
)
from .download_urn_file import DownloadUrnFile
from .get_ballot_report import GetBallotReport


@dataclass(frozen=True)
class OfficeLateEstimate:
    office_code: int
    office_name: str | None
    late_votes: int
    estimates: list[LateVoteEstimate]


@dataclass(frozen=True)
class SectionVoteTimeline:
    timeline: VoteTimeline
    threshold: str
    votes_after: int
    turnout: int
    offset_source: str  # "uf" (fuso padrão da UF) | "desconhecido" (exterior: horário local)
    offices: list[OfficeLateEstimate]


class GetVoteTimeline:
    """Votos por horário de uma seção (log da urna) e estimativa dos votos tardios por candidato."""

    def __init__(self, ballot: GetBallotReport, download: DownloadUrnFile, reader: UrnLogReader):
        self._ballot = ballot
        self._download = download
        self._reader = reader

    async def execute(
        self, voting_event_code: int, uf: str, municipality: int, zone: int, section: int, threshold: time
    ) -> SectionVoteTimeline:
        report = await self._ballot.execute(voting_event_code, uf, municipality, zone, section)
        log = await self._download.execute(voting_event_code, uf, municipality, zone, section, "log")
        events = self._reader.read_votes(log.content, report.voting_date)
        offset = default_offset_to_brasilia(uf.lower())
        late = count_after(events, offset, threshold)
        offices = []
        for office in (o for e in report.elections for o in e.offices):
            # Eleitores em trânsito não votam em todos os cargos: escala pelo comparecimento do cargo.
            office_late = round(late * office.turnout / report.turnout) if report.turnout else 0
            offices.append(
                OfficeLateEstimate(office.code, office.name, office_late, estimate_late_votes(office, office_late))
            )
        return SectionVoteTimeline(
            timeline=build_timeline(events, offset),
            threshold=threshold.strftime("%H:%M"),
            votes_after=late,
            turnout=report.turnout,
            offset_source="uf" if offset is not None else "desconhecido",
            offices=offices,
        )
