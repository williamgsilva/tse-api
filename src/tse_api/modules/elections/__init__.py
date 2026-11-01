"""API pública do módulo de eleições: o único ponto que outros módulos podem importar."""

from .application.get_election_result import GetElectionResult
from .application.get_voting_event import GetVotingEvent
from .domain.models import ElectionResult, ResultNotPublished, VotingEvent

__all__ = ["ElectionResult", "GetElectionResult", "GetVotingEvent", "ResultNotPublished", "VotingEvent"]
