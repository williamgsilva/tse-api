"""Horário dos votos a partir do log da urna.

O log registra *quando* cada eleitor votou e como foi habilitado, nunca *em quem* votou
(o sigilo do voto é garantido pelo RDV, que não tem horário). Por isso a distribuição de
votos por candidato num intervalo de horário só pode ser **estimada**.
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from ....shared.errors import InvalidInputError
from .models import OfficeVotes

BUCKET_MINUTES = 15

# Tipos de habilitação do eleitor, como no detalhamento de comparecimento do BU.
BIOMETRICS = "biometria"
BIRTH_YEAR = "ano_nascimento"
NO_BIOMETRICS = "sem_biometria"

# Horas a somar ao horário local da urna para obter o horário de Brasília (fuso padrão da UF).
# Exceções dentro da UF (oeste do Amazonas, Fernando de Noronha) só são detectadas na base local,
# pelo horário de abertura das seções do município. No exterior o fuso varia por país.
UF_OFFSET_TO_BRASILIA = {"ac": 2, "am": 1, "rr": 1, "ro": 1, "mt": 1, "ms": 1}


def default_offset_to_brasilia(uf: str) -> int | None:
    if uf == "zz":
        return None
    return UF_OFFSET_TO_BRASILIA.get(uf, 0)


@dataclass(frozen=True)
class VoteEvent:
    """Um voto computado, no horário local da urna, com o tipo de habilitação do eleitor."""

    at: datetime
    enablement: str


@dataclass(frozen=True)
class TimelineBucket:
    start: str  # HH:MM
    votes: int
    by_enablement: dict[str, int]


@dataclass(frozen=True)
class VoteTimeline:
    offset_to_brasilia: int | None  # None = horário local (fuso desconhecido)
    total_votes: int
    first_vote: str | None
    last_vote: str | None
    by_enablement: dict[str, int]
    buckets: tuple[TimelineBucket, ...]


def parse_clock(value: str) -> time:
    try:
        parsed = datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise InvalidInputError(f"horário inválido (use HH:MM): {value}") from exc
    return parsed


def to_brasilia(at: datetime, offset: int | None) -> datetime:
    return at + timedelta(hours=offset or 0)


def bucket_start(at: datetime, minutes: int = BUCKET_MINUTES) -> str:
    floored = (at.hour * 60 + at.minute) // minutes * minutes
    return f"{floored // 60:02d}:{floored % 60:02d}"


def build_timeline(events: list[VoteEvent], offset: int | None, minutes: int = BUCKET_MINUTES) -> VoteTimeline:
    buckets: dict[str, dict[str, int]] = {}
    totals: dict[str, int] = {}
    moments = sorted(to_brasilia(e.at, offset) for e in events)
    for event in events:
        kind = event.enablement
        key = bucket_start(to_brasilia(event.at, offset), minutes)
        bucket = buckets.setdefault(key, {})
        bucket[kind] = bucket.get(kind, 0) + 1
        totals[kind] = totals.get(kind, 0) + 1
    return VoteTimeline(
        offset_to_brasilia=offset,
        total_votes=len(events),
        first_vote=moments[0].isoformat() if moments else None,
        last_vote=moments[-1].isoformat() if moments else None,
        by_enablement=totals,
        buckets=tuple(TimelineBucket(start, sum(kinds.values()), kinds) for start, kinds in sorted(buckets.items())),
    )


def count_after(events: list[VoteEvent], offset: int | None, threshold: time) -> int:
    """Votos computados a partir de ``threshold`` (horário de Brasília, ou local se o fuso for desconhecido)."""
    return sum(1 for e in events if to_brasilia(e.at, offset).time() >= threshold)


@dataclass(frozen=True)
class LateVoteEstimate:
    kind: str
    number: int | None
    name: str | None
    party: str | None
    section_votes: int
    estimated_late_votes: float


def estimate_late_votes(office: OfficeVotes, late_votes: int) -> list[LateVoteEstimate]:
    """Distribui os votos tardios do cargo na mesma proporção dos votos da seção.

    Supõe que quem votou depois do horário votou como o restante da seção: é uma **estimativa**.
    """
    share = late_votes / office.turnout if office.turnout else 0.0
    return [
        LateVoteEstimate(
            kind=v.kind,
            number=v.number,
            name=v.candidate_name,
            party=v.party_acronym,
            section_votes=v.quantity,
            estimated_late_votes=round(v.quantity * share, 2),
        )
        for v in sorted(office.votes, key=lambda v: v.quantity, reverse=True)
    ]
