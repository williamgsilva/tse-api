from ....shared.uf import parse_uf
from ..domain.models import SectionVotesNotFound, SectionVotesReport
from ..domain.ports import VoteRepository


class GetSectionVotes:
    def __init__(self, repository: VoteRepository):
        self._repository = repository

    def execute(self, year: int, round: int, uf: str, municipality: int, zone: int, section: int) -> SectionVotesReport:
        report = self._repository.section_votes(year, round, parse_uf(uf).upper(), municipality, zone, section)
        if report is None:
            raise SectionVotesNotFound("seção não encontrada na base local (a UF e o turno foram importados?)")
        return report
