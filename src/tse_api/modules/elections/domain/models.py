"""Eleições, pleitos e resultados totalizados (termos em docs/glossario.md)."""

from dataclasses import dataclass, field

from ....shared.errors import InvalidInputError, NotFoundError


class ElectionNotFound(NotFoundError):
    slug = "election-not-found"
    title = "Eleição não encontrada"


class VotingEventNotFound(NotFoundError):
    slug = "voting-event-not-found"
    title = "Pleito não encontrado"


class ResultNotPublished(NotFoundError):
    slug = "result-not-published"
    title = "Resultado não publicado pelo TSE"


@dataclass(frozen=True)
class Office:
    """Cargo em disputa (ou pergunta de consulta popular)."""

    code: int
    name: str
    kind: str  # majoritario | proporcional | consulta
    scopes: tuple[str, ...]


@dataclass(frozen=True)
class Election:
    code: int
    name: str
    round: int
    kind: int
    voting_event_code: int
    cycle: str
    date: str
    second_round_code: int | None
    offices: tuple[Office, ...]

    @property
    def year(self) -> int:
        return cycle_year(self.cycle)

    def require_office(self, office_code: int) -> Office:
        for office in self.offices:
            if office.code == office_code:
                return office
        raise InvalidInputError(f"cargo {office_code} não pertence à eleição {self.code}")


@dataclass(frozen=True)
class VotingEvent:
    """Pleito: uma data de votação. Os arquivos de urna são organizados por pleito."""

    code: int
    cycle: str
    date: str
    elections: tuple[Election, ...]

    @property
    def year(self) -> int:
        return cycle_year(self.cycle)


def cycle_year(cycle: str) -> int:
    return int(cycle.removeprefix("ele"))


@dataclass(frozen=True)
class Catalog:
    voting_events: dict[int, VotingEvent]
    elections: dict[int, Election]

    def election(self, code: int) -> Election:
        try:
            return self.elections[code]
        except KeyError:
            raise ElectionNotFound(f"eleição {code} não encontrada no catálogo do TSE") from None

    def voting_event(self, code: int) -> VotingEvent:
        try:
            return self.voting_events[code]
        except KeyError:
            raise VotingEventNotFound(f"pleito {code} não encontrado no catálogo do TSE") from None

    def voting_events_of_year(self, year: int | None) -> list[VotingEvent]:
        events = [e for e in self.voting_events.values() if year is None or e.year == year]
        return sorted(events, key=lambda e: (e.date, e.code))


@dataclass(frozen=True)
class Municipality:
    uf: str
    code: int
    ibge_code: int | None
    name: str
    is_capital: bool
    zones: tuple[int, ...]


@dataclass(frozen=True)
class SectionTotals:
    total: int | None
    counted: int | None
    counted_percent: float | None


@dataclass(frozen=True)
class ElectorateTotals:
    total: int | None
    turnout: int | None
    abstention: int | None
    turnout_percent: float | None
    abstention_percent: float | None


@dataclass(frozen=True)
class VoteTotals:
    total: int | None
    valid: int | None
    nominal: int | None
    party: int | None
    blank: int | None
    null: int | None
    blank_percent: float | None
    null_percent: float | None


@dataclass(frozen=True)
class Totals:
    sections: SectionTotals | None = None
    electorate: ElectorateTotals | None = None
    votes: VoteTotals | None = None


@dataclass(frozen=True)
class RunningMate:
    kind: str | None
    name: str | None
    ballot_name: str | None
    party: str | None


@dataclass(frozen=True)
class Candidate:
    number: int | None
    name: str | None
    ballot_name: str | None
    sequential_id: str | None
    party: str | None
    party_number: int | None
    alliance: str | None
    alliance_parties: str | None
    votes: int
    percent: float | None
    is_elected: bool
    status: str | None
    vote_destination: str | None
    running_mates: tuple[RunningMate, ...] = ()


@dataclass(frozen=True)
class PartyResult:
    number: int | None
    acronym: str | None
    name: str | None
    federation: int | None
    total_votes: int | None
    party_votes: int | None
    alliance: str | None


@dataclass(frozen=True)
class OfficeResult:
    code: int | None
    name: str | None
    seats: int | None
    electoral_quotient: int | None
    candidates: tuple[Candidate, ...]
    parties: tuple[PartyResult, ...]

    def candidate_by_number(self) -> dict[int, Candidate]:
        return {c.number: c for c in self.candidates if c.number is not None}

    def party_by_number(self) -> dict[int, PartyResult]:
        return {p.number: p for p in self.parties if p.number is not None}


@dataclass(frozen=True)
class ElectionResult:
    election_code: int | None
    round: int | None
    scope_type: str | None
    scope_code: str | None
    updated_at: str | None
    is_final: bool
    totals: Totals
    offices: tuple[OfficeResult, ...]


@dataclass(frozen=True)
class ScopeTotals:
    scope_type: str | None
    scope_code: str | None
    counted_at: str | None
    totals: Totals


@dataclass(frozen=True)
class Coverage:
    """Totais por abrangência (UF/Brasil): seções totalizadas, eleitorado, comparecimento."""

    election_code: int | None
    round: int | None
    updated_at: str | None
    scopes: tuple[ScopeTotals, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SubdivisionResult:
    """Resultado resumido de uma UF (no Brasil) ou de um município (numa UF), para mapas."""

    scope_type: str  # uf | mu
    code: str  # sigla da UF ou código TSE do município
    ibge_code: int | None
    name: str
    is_final: bool
    totals: Totals
    candidates: tuple[Candidate, ...]  # os primeiros colocados
