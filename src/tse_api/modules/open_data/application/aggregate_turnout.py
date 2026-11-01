from dataclasses import replace

from ..domain.models import TurnoutAggregate, TurnoutQuery
from ..domain.ports import VoteRepository


class AggregateTurnout:
    """Aptos, comparecimento, abstenção e biometria somados por UF, município, zona, local ou seção."""

    def __init__(self, repository: VoteRepository):
        self._repository = repository

    def execute(self, query: TurnoutQuery) -> list[TurnoutAggregate]:
        return self._repository.turnout(replace(query, filters=query.filters.normalized()))
