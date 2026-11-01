"""Boletins de urna do Portal de Dados Abertos do TSE (CSV ``bweb``) carregados na base local."""

import re
from dataclasses import dataclass, replace
from enum import Enum

from ....shared.errors import InvalidInputError, NotFoundError, ServiceUnavailableError
from ....shared.uf import parse_uf


class LocalDatabaseUnavailable(ServiceUnavailableError):
    slug = "local-database-unavailable"
    title = "Base local de boletins indisponível"


class SectionVotesNotFound(NotFoundError):
    slug = "section-not-imported"
    title = "Seção não encontrada na base local"


class DatasetKind(str, Enum):
    BALLOTS_CSV = "boletins"  # CSV bweb: votos por votável, cargo e seção
    URN_FILES = "urnas"  # pacote com BU, log, RDV e assinatura de todas as seções


_BALLOTS_CSV_NAME = re.compile(r"bweb_(\d)t_([A-Z]{2})_(\d{12})\.zip$")
_URN_FILES_NAME = re.compile(r"bu_imgbu_logjez_rdv_vscmr_\d{4}_(\d)t_([A-Z]{2})\.zip$")


@dataclass(frozen=True)
class DatasetFile:
    """Um ZIP publicado pelo TSE: CSV de boletins (``bweb_...``) ou pacote de arquivos de urna."""

    kind: DatasetKind
    round: int
    uf: str
    timestamp: str  # ddmmaaaahhmm; vazio quando o nome não traz data
    url: str
    checksum_url: str | None

    @classmethod
    def from_url(cls, url: str, checksum_url: str | None) -> "DatasetFile | None":
        if match := _BALLOTS_CSV_NAME.search(url):
            return cls(DatasetKind.BALLOTS_CSV, int(match[1]), match[2], match[3], url, checksum_url)
        if match := _URN_FILES_NAME.search(url):
            return cls(DatasetKind.URN_FILES, int(match[1]), match[2], "", url, checksum_url)
        return None

    @property
    def name(self) -> str:
        return self.url.rsplit("/", 1)[-1]

    @property
    def published_order(self) -> str:
        t = self.timestamp
        return t[4:8] + t[2:4] + t[0:2] + t[8:12] if t else ""


def latest_per_round_and_uf(files: list[DatasetFile]) -> list[DatasetFile]:
    """O TSE republica arquivos corrigidos; vale o mais recente de cada (tipo, turno, UF)."""
    latest: dict[tuple[DatasetKind, int, str], DatasetFile] = {}
    for f in files:
        key = (f.kind, f.round, f.uf)
        current = latest.get(key)
        if current is None or f.published_order > current.published_order:
            latest[key] = f
    return sorted(latest.values(), key=lambda f: (f.kind.value, f.round, f.uf))


@dataclass(frozen=True)
class ImportedDataset:
    year: int
    round: int
    uf: str
    source_file: str
    rows: int
    sections: int
    kind: DatasetKind = DatasetKind.BALLOTS_CSV


class Grouping(str, Enum):
    TOTAL = "total"
    VOTABLE = "votavel"  # mesmo que TOTAL: só por votável (nome mantido na rota de votação)
    UF = "uf"
    MUNICIPALITY = "municipio"
    ZONE = "zona"
    POLLING_PLACE = "local"
    SECTION = "secao"


def _check_paging(limit: int, offset: int) -> None:
    if not 1 <= limit <= 10000:
        raise InvalidInputError("limit deve estar entre 1 e 10000")
    if offset < 0:
        raise InvalidInputError("offset não pode ser negativo")


@dataclass(frozen=True)
class VoteQuery:
    year: int
    round: int
    office: int
    grouping: Grouping = Grouping.VOTABLE
    uf: str | None = None
    municipality: int | None = None
    zone: int | None = None
    section: int | None = None
    votable: int | None = None
    urn_type: str | None = None
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        _check_paging(self.limit, self.offset)


@dataclass(frozen=True)
class VoteAggregate:
    votable_kind: str | None
    votable_number: int | None
    votable_name: str | None
    party: str | None
    votes: int
    uf: str | None = None
    municipality: int | None = None
    municipality_name: str | None = None
    zone: int | None = None
    polling_place: int | None = None
    section: int | None = None


@dataclass(frozen=True)
class SectionVote:
    kind: str | None
    number: int | None
    name: str | None
    party: str | None
    quantity: int


@dataclass(frozen=True)
class SectionOfficeVotes:
    election_code: int
    election_name: str | None
    office_code: int
    office_name: str | None
    eligible_voters: int | None
    turnout: int | None
    abstentions: int | None
    votes: tuple[SectionVote, ...]


@dataclass(frozen=True)
class SectionUrn:
    kind: str | None
    number: int | None
    load_code_1: str | None
    load_code_2: str | None
    flash_card: str | None
    loaded_at: str | None


@dataclass(frozen=True)
class SectionVotesReport:
    year: int
    round: int
    voting_event_code: int | None
    uf: str
    municipality: int
    municipality_name: str | None
    zone: int
    section: int
    polling_place: int | None
    aggregated_sections: str | None
    urn: SectionUrn
    opened_at: str | None
    closed_at: str | None
    issued_at: str | None
    received_at: str | None
    biometric_not_enabled: int | None
    offices: tuple[SectionOfficeVotes, ...]
    source_file: str | None


# --- Pacotes de arquivos de urna (BU + log) ----------------------------------------------------


@dataclass(frozen=True)
class SectionUrnRecord:
    """Uma seção lida do pacote de arquivos de urna: dados do BU e votos por horário do log."""

    uf: str
    municipality: int
    zone: int
    section: int
    polling_place: int
    urn_kind: str
    urn_number: int
    software_version: str
    opened_at: str | None  # horário local da urna
    closed_at: str | None
    issued_at: str | None
    eligible_voters: int
    eligible_in_section: int
    eligible_in_transit: int
    turnout: int
    without_biometrics: int | None
    enabled_by_biometrics: int | None
    enabled_by_birth_year: int | None
    log_votes: int
    # (minuto do dia no horário local, múltiplo de 15) → tipo de habilitação → votos
    votes_by_quarter_hour: dict[int, dict[str, int]]


@dataclass(frozen=True)
class SectionFilter:
    uf: str | None = None
    municipality: int | None = None
    zone: int | None = None
    section: int | None = None
    urn_type: str | None = None

    def normalized(self) -> "SectionFilter":
        """UF em maiúsculas, como no CSV do TSE."""
        return replace(self, uf=parse_uf(self.uf).upper()) if self.uf else self


@dataclass(frozen=True)
class TurnoutQuery:
    year: int
    round: int
    grouping: Grouping = Grouping.TOTAL
    filters: SectionFilter = SectionFilter()
    closed_after: str | None = None  # HH:MM, horário de Brasília
    limit: int = 1000
    offset: int = 0

    def __post_init__(self) -> None:
        _check_paging(self.limit, self.offset)
        if self.grouping == Grouping.VOTABLE:
            raise InvalidInputError("agrupamento 'votavel' não se aplica ao comparecimento")


@dataclass(frozen=True)
class TurnoutAggregate:
    sections: int
    eligible_voters: int
    turnout: int
    abstentions: int
    turnout_percent: float | None
    enabled_by_birth_year: int | None
    without_biometrics: int | None
    enabled_by_biometrics: int | None
    sections_with_urn_files: int
    first_opening: str | None
    last_closing: str | None
    group: dict[str, object]


VALID_INTERVALS = (15, 30, 60)


def minutes_of(clock: str) -> int:
    try:
        hours, minutes = (int(p) for p in clock.split(":"))
    except ValueError as exc:
        raise InvalidInputError(f"horário inválido (use HH:MM): {clock}") from exc
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise InvalidInputError(f"horário inválido: {clock}")
    return hours * 60 + minutes


@dataclass(frozen=True)
class TimelineQuery:
    year: int
    round: int
    grouping: Grouping = Grouping.TOTAL
    filters: SectionFilter = SectionFilter()
    interval: int = 15

    def __post_init__(self) -> None:
        if self.interval not in VALID_INTERVALS:
            raise InvalidInputError(f"intervalo deve ser um de {VALID_INTERVALS} minutos")
        if self.grouping in (Grouping.VOTABLE, Grouping.SECTION, Grouping.POLLING_PLACE):
            raise InvalidInputError("horários agrupam por total, uf, municipio ou zona")


@dataclass(frozen=True)
class TimelinePoint:
    start: str  # HH:MM, horário de Brasília
    votes: int
    by_enablement: dict[str, int]
    group: dict[str, object]


@dataclass(frozen=True)
class LateVotesQuery:
    """Votos depois de um horário: total exato (log) e ESTIMATIVA por votável (proporção da seção)."""

    year: int
    round: int
    office: int
    after: str = "17:00"  # horário de Brasília, múltiplo de 15 min
    grouping: Grouping = Grouping.TOTAL
    filters: SectionFilter = SectionFilter()
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        _check_paging(self.limit, self.offset)
        if minutes_of(self.after) % 15:
            raise InvalidInputError("o horário de corte deve ser múltiplo de 15 minutos (ex.: 17:00, 16:45)")
        if self.grouping in (Grouping.SECTION, Grouping.POLLING_PLACE, Grouping.ZONE):
            raise InvalidInputError("estimativa agrupa por total, uf ou municipio")


@dataclass(frozen=True)
class LateVotesSummary:
    sections: int
    turnout: int
    late_votes: int
    sections_without_timezone: int


@dataclass(frozen=True)
class LateVoteAggregate:
    votable_kind: str | None
    votable_number: int | None
    votable_name: str | None
    party: str | None
    section_votes: int
    estimated_late_votes: float
    group: dict[str, object]


@dataclass(frozen=True)
class LateVotesReport:
    after: str
    summary: LateVotesSummary
    votables: list[LateVoteAggregate]
