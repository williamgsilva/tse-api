from dataclasses import replace

from ..domain.models import LateVotesQuery, LateVotesReport
from ..domain.ports import VoteRepository


class EstimateLateVotes:
    """Votos depois de um horário: total exato pelos logs e ESTIMATIVA por votável.

    O voto é secreto: o log da urna registra o horário, nunca o candidato. A estimativa distribui os
    votos tardios de cada seção na proporção dos votos daquela seção e soma as seções.
    """

    def __init__(self, repository: VoteRepository):
        self._repository = repository

    def execute(self, query: LateVotesQuery) -> LateVotesReport:
        return self._repository.late_votes(replace(query, filters=query.filters.normalized()))
