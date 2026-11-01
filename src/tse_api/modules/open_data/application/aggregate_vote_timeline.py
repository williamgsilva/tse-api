from dataclasses import replace

from ..domain.models import TimelinePoint, TimelineQuery
from ..domain.ports import VoteRepository


class AggregateVoteTimeline:
    """Votos por intervalo de horário (Brasília), a partir dos logs das urnas importados."""

    def __init__(self, repository: VoteRepository):
        self._repository = repository

    def execute(self, query: TimelineQuery) -> list[TimelinePoint]:
        return self._repository.timeline(replace(query, filters=query.filters.normalized()))
