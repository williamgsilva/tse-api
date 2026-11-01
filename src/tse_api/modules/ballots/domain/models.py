"""Seções eleitorais, arquivos de urna e boletim de urna (BU)."""

from dataclasses import dataclass, field
from datetime import date

from ....shared.errors import InvalidInputError, NotFoundError, UpstreamDataError


class SectionNotFound(NotFoundError):
    slug = "section-not-found"
    title = "Seção sem arquivos de urna publicados"


class UrnFileNotFound(NotFoundError):
    slug = "urn-file-not-found"
    title = "Arquivo de urna não disponível"


class InvalidBallotReport(UpstreamDataError):
    slug = "invalid-ballot-report"
    title = "Boletim de urna inválido"


@dataclass(frozen=True)
class SectionKey:
    uf: str
    municipality: int
    zone: int
    section: int

    def __post_init__(self) -> None:
        for name, value, limit in (
            ("município", self.municipality, 99999),
            ("zona", self.zone, 9999),
            ("seção", self.section, 9999),
        ):
            if not 1 <= value <= limit:
                raise InvalidInputError(f"{name} fora do intervalo 1..{limit}: {value}")


@dataclass(frozen=True)
class SectionSummary:
    key: SectionKey
    municipality_name: str | None
    updated_at: str | None


@dataclass(frozen=True)
class UrnFile:
    name: str
    kind: str  # bu, rdv, log, vota...
    url: str


TOTALIZED_STATUS = "totaliz"


@dataclass(frozen=True)
class UrnFileSet:
    """Conjunto de arquivos de uma transmissão da urna (identificado por um hash)."""

    hash: str
    status: str | None
    received_at: str | None
    files: tuple[UrnFile, ...]

    @property
    def is_totalized(self) -> bool:
        return (self.status or "").lower().startswith(TOTALIZED_STATUS)


@dataclass(frozen=True)
class SectionStatus:
    voting_event_code: int
    key: SectionKey
    status: str | None
    updated_at: str | None
    file_sets: tuple[UrnFileSet, ...]

    def current_file_set(self) -> UrnFileSet:
        """A transmissão vigente: a última totalizada ou, se nenhuma foi, a última recebida."""
        if not self.file_sets:
            raise SectionNotFound("seção sem arquivos de urna publicados")
        totalized = [fs for fs in self.file_sets if fs.is_totalized]
        return (totalized or list(self.file_sets))[-1]

    def current_file(self, kind: str) -> tuple[UrnFileSet, UrnFile]:
        file_set = self.current_file_set()
        for urn_file in file_set.files:
            if urn_file.kind == kind:
                return file_set, urn_file
        available = ", ".join(f.kind for f in file_set.files)
        raise UrnFileNotFound(f"arquivo do tipo '{kind}' não disponível (disponíveis: {available})")


@dataclass(frozen=True)
class VoteCount:
    kind: str  # nominal | legenda | branco | nulo
    quantity: int
    number: int | None = None
    party_number: int | None = None
    candidate_name: str | None = None
    candidate_full_name: str | None = None
    party_acronym: str | None = None


@dataclass(frozen=True)
class OfficeVotes:
    code: int
    identifier: str
    kind: str  # majoritario | proporcional | consulta
    print_order: int
    turnout: int
    votes: tuple[VoteCount, ...]
    name: str | None = None

    @property
    def totals(self) -> dict[str, int]:
        totals = {"nominal": 0, "legenda": 0, "branco": 0, "nulo": 0}
        for vote in self.votes:
            totals[vote.kind] = totals.get(vote.kind, 0) + vote.quantity
        return totals


@dataclass(frozen=True)
class ElectionVotes:
    election_code: int
    eligible_voters: int
    eligible_in_section: int
    eligible_in_transit: int
    offices: tuple[OfficeVotes, ...]
    last_votes_hash: str
    name: str | None = None


@dataclass(frozen=True)
class UrnInfo:
    kind: str
    file_kind: str
    voting_software_version: str
    internal_number: int
    load_flash_serial: str
    voting_flash_serial: str
    load_code: str
    loaded_at: str | None
    load_target: dict[str, object]
    counting_system: dict[str, object] | None = None


@dataclass(frozen=True)
class BallotReport:
    """Boletim de urna (BU) de uma seção, decodificado do arquivo oficial."""

    phase: str
    electoral_id: dict[str, object]
    generated_at: str | None
    issued_at: str | None
    section: dict[str, int]
    urn: UrnInfo
    turnout: int
    elections: tuple[ElectionVotes, ...]
    load_code_history: tuple[str, ...]
    voting_window: dict[str, str | None] | None = None
    counting_board: dict[str, object] | None = None
    turnout_breakdown: dict[str, int] | None = None
    file_name: str | None = None
    uf: str | None = None

    @property
    def voting_date(self) -> date:
        """Dia da votação (primeiro voto ou emissão do BU), usado para filtrar o log da urna."""
        opened = (self.voting_window or {}).get("abertura") or self.issued_at
        if not opened:
            raise InvalidBallotReport("boletim sem data de votação")
        return date.fromisoformat(opened[:10])


@dataclass(frozen=True)
class CandidateNames:
    """Nomes de candidatos e siglas de partidos de um cargo, usados para enriquecer o BU."""

    office_name: str | None
    candidates: dict[int, tuple[str | None, str | None]] = field(default_factory=dict)  # número → (urna, completo)
    parties: dict[int, str | None] = field(default_factory=dict)  # número → sigla
