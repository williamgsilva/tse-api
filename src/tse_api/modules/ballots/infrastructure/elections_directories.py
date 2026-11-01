"""Adaptadores que consultam o módulo de eleições pela sua API pública."""

from ....shared.errors import InvalidInputError
from ...elections import GetElectionResult, GetVotingEvent, ResultNotPublished
from ..domain.models import CandidateNames
from ..domain.ports import CandidateDirectory, VotingEventDirectory, VotingEventRef


class ElectionsVotingEventDirectory(VotingEventDirectory):
    def __init__(self, get_voting_event: GetVotingEvent):
        self._get_voting_event = get_voting_event

    async def get(self, code: int) -> VotingEventRef:
        event = await self._get_voting_event.execute(code)
        return VotingEventRef(
            code=event.code, cycle=event.cycle, election_names={e.code: e.name for e in event.elections}
        )


class ElectionsCandidateDirectory(CandidateDirectory):
    """Nomes vêm do resultado totalizado do município, que lista todos os candidatos do cargo."""

    def __init__(self, get_election_result: GetElectionResult):
        self._get_election_result = get_election_result

    async def lookup(self, election_code: int, uf: str, municipality: int, office_code: int) -> CandidateNames | None:
        try:
            result = await self._get_election_result.execute(election_code, uf, office_code, municipality)
        except (ResultNotPublished, InvalidInputError):
            return None
        candidates: dict[int, tuple[str | None, str | None]] = {}
        parties: dict[int, str | None] = {}
        office_name = None
        for office in result.offices:
            office_name = office_name or office.name
            candidates.update({n: (c.ballot_name, c.name) for n, c in office.candidate_by_number().items()})
            parties.update({n: p.acronym for n, p in office.party_by_number().items()})
        return CandidateNames(office_name=office_name, candidates=candidates, parties=parties)
