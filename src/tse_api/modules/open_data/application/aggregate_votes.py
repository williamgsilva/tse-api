from dataclasses import replace

from ....shared.uf import parse_uf
from ..domain.models import VoteAggregate, VoteQuery
from ..domain.ports import VoteRepository


class AggregateVotes:
    """Soma de votos por votável, opcionalmente agrupada por UF, município, zona ou seção."""

    def __init__(self, repository: VoteRepository):
        self._repository = repository

    def execute(self, query: VoteQuery) -> list[VoteAggregate]:
        if query.uf is not None:
            query = replace(query, uf=parse_uf(query.uf).upper())
        return self._repository.aggregate(query)
