from dataclasses import dataclass
from datetime import date
from typing import Protocol

from .models import BallotReport, CandidateNames, SectionKey, SectionStatus, SectionSummary, UrnFile, UrnFileSet
from .timeline import VoteEvent


@dataclass(frozen=True)
class VotingEventRef:
    """O que este módulo precisa saber de um pleito (vem do módulo de eleições)."""

    code: int
    cycle: str
    election_names: dict[int, str]


class VotingEventDirectory(Protocol):
    async def get(self, code: int) -> VotingEventRef: ...


class UrnFileSource(Protocol):
    async def list_sections(self, event: VotingEventRef, uf: str) -> list[SectionSummary]: ...

    async def fetch_section_status(self, event: VotingEventRef, key: SectionKey) -> SectionStatus: ...

    async def fetch_file(
        self, event: VotingEventRef, key: SectionKey, file_set: UrnFileSet, file: UrnFile
    ) -> bytes: ...


class UrnLogReader(Protocol):
    def read_votes(self, raw: bytes, voting_date: date) -> list[VoteEvent]: ...


class BallotDecoder(Protocol):
    def decode(self, raw: bytes) -> BallotReport: ...


class CandidateDirectory(Protocol):
    async def lookup(
        self, election_code: int, uf: str, municipality: int, office_code: int
    ) -> CandidateNames | None: ...
