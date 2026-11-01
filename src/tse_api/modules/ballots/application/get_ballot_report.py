from dataclasses import replace

from ..domain.enrichment import name_votes
from ..domain.models import BallotReport, ElectionVotes
from ..domain.ports import BallotDecoder, CandidateDirectory, VotingEventDirectory
from .download_urn_file import DownloadUrnFile


class GetBallotReport:
    """Boletim de urna decodificado; opcionalmente com nomes de eleições, candidatos e partidos."""

    def __init__(
        self,
        events: VotingEventDirectory,
        download: DownloadUrnFile,
        decoder: BallotDecoder,
        directory: CandidateDirectory,
    ):
        self._events = events
        self._download = download
        self._decoder = decoder
        self._directory = directory

    async def execute(
        self, voting_event_code: int, uf: str, municipality: int, zone: int, section: int, with_names: bool = True
    ) -> BallotReport:
        downloaded = await self._download.execute(voting_event_code, uf, municipality, zone, section, "bu")
        report = replace(self._decoder.decode(downloaded.content), file_name=downloaded.name, uf=uf.lower())
        if not with_names:
            return report
        election_names = (await self._events.get(voting_event_code)).election_names
        elections = [
            replace(await self._name_offices(e, uf.lower(), municipality), name=election_names.get(e.election_code))
            for e in report.elections
        ]
        return replace(report, elections=tuple(elections))

    async def _name_offices(self, election: ElectionVotes, uf: str, municipality: int) -> ElectionVotes:
        offices = []
        for office in election.offices:
            names = await self._directory.lookup(election.election_code, uf, municipality, office.code)
            offices.append(name_votes(office, names) if names else office)
        return replace(election, offices=tuple(offices))
