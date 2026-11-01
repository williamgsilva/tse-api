from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Query

from ..application.aggregate_turnout import AggregateTurnout
from ..application.aggregate_vote_timeline import AggregateVoteTimeline
from ..application.aggregate_votes import AggregateVotes
from ..application.estimate_late_votes import EstimateLateVotes
from ..application.get_import_status import GetImportStatus
from ..application.get_section_votes import GetSectionVotes
from ..domain.models import (
    Grouping,
    ImportedDataset,
    LateVotesQuery,
    SectionFilter,
    SectionVotesReport,
    TimelinePoint,
    TimelineQuery,
    TurnoutAggregate,
    TurnoutQuery,
    VoteAggregate,
    VoteQuery,
)
from .schemas import (
    ImportedDatasetOut,
    LateVotesReportOut,
    SectionVotesReportOut,
    TimelinePointOut,
    TurnoutAggregateOut,
    VoteAggregateOut,
)

LATE_VOTES_METHOD = (
    "ESTIMATIVA. O voto é secreto: o log da urna registra o horário de cada voto, nunca o candidato. "
    "Em cada seção, os votos dados após o horário são distribuídos na mesma proporção dos votos da seção, "
    "e o resultado é somado. Supõe que quem votou depois do horário votou como o restante da seção."
)


@dataclass(frozen=True)
class OpenDataUseCases:
    get_import_status: GetImportStatus
    get_section_votes: GetSectionVotes
    aggregate_votes: AggregateVotes
    aggregate_turnout: AggregateTurnout
    aggregate_vote_timeline: AggregateVoteTimeline
    estimate_late_votes: EstimateLateVotes


def _filters(
    uf: str | None = None,
    municipio: int | None = None,
    zona: int | None = None,
    secao: int | None = None,
    tipo_urna: str | None = None,
) -> SectionFilter:
    return SectionFilter(uf, municipio, zona, secao, tipo_urna)


def build_router(use_cases: OpenDataUseCases) -> APIRouter:
    # Endpoints síncronos: o FastAPI os executa em thread pool, sem bloquear o event loop com o DuckDB.
    router = APIRouter(prefix="/dados-abertos", tags=["boletins de urna (dados abertos, base local)"])

    @router.get("/importacoes", response_model=list[ImportedDatasetOut], summary="O que foi importado")
    def get_import_status() -> list[ImportedDataset]:
        return use_cases.get_import_status.execute()

    @router.get(
        "/{ano}/{turno}/secoes/{uf}/{municipio}/{zona}/{secao}",
        response_model=SectionVotesReportOut,
        summary="Boletim de urna de uma seção (CSV de dados abertos)",
    )
    def get_section_votes(ano: int, turno: int, uf: str, municipio: int, zona: int, secao: int) -> SectionVotesReport:
        return use_cases.get_section_votes.execute(ano, turno, uf, municipio, zona, secao)

    @router.get(
        "/{ano}/{turno}/votacao/{cargo}",
        response_model=list[VoteAggregateOut],
        response_model_exclude_none=True,
        summary="Soma de votos por votável, com agrupamento opcional",
    )
    def aggregate_votes(
        ano: int,
        turno: int,
        cargo: int,
        agrupar: Grouping = Grouping.VOTABLE,
        uf: str | None = None,
        municipio: int | None = None,
        zona: int | None = None,
        secao: int | None = None,
        tipo_urna: str | None = Query(None, description="tipo de urna do CSV (ex.: Apurada)"),
        votavel: int | None = Query(None, description="número do candidato ou partido"),
        limit: int = Query(100, ge=1, le=10000),
        offset: int = Query(0, ge=0),
    ) -> list[VoteAggregate]:
        query = VoteQuery(ano, turno, cargo, agrupar, uf, municipio, zona, secao, votavel, tipo_urna, limit, offset)
        return use_cases.aggregate_votes.execute(query)

    @router.get(
        "/{ano}/{turno}/comparecimento",
        response_model=list[TurnoutAggregateOut],
        summary="Aptos, comparecimento, abstenção e biometria somados por seção, local, zona, município ou UF",
    )
    def aggregate_turnout(
        ano: int,
        turno: int,
        agrupar: Grouping = Grouping.TOTAL,
        uf: str | None = None,
        municipio: int | None = None,
        zona: int | None = None,
        secao: int | None = None,
        tipo_urna: str | None = None,
        encerramento_apos: str | None = Query(
            None, description="só seções cujo último voto foi a partir deste horário de Brasília (HH:MM)"
        ),
        limit: int = Query(1000, ge=1, le=10000),
        offset: int = Query(0, ge=0),
    ) -> list[TurnoutAggregate]:
        query = TurnoutQuery(
            ano, turno, agrupar, _filters(uf, municipio, zona, secao, tipo_urna), encerramento_apos, limit, offset
        )
        return use_cases.aggregate_turnout.execute(query)

    @router.get(
        "/{ano}/{turno}/horarios",
        response_model=list[TimelinePointOut],
        summary="Votos por intervalo de horário (Brasília), contados nos logs das urnas",
    )
    def aggregate_vote_timeline(
        ano: int,
        turno: int,
        agrupar: Grouping = Grouping.TOTAL,
        uf: str | None = None,
        municipio: int | None = None,
        zona: int | None = None,
        secao: int | None = None,
        intervalo: int = Query(15, description="minutos: 15, 30 ou 60"),
    ) -> list[TimelinePoint]:
        query = TimelineQuery(ano, turno, agrupar, _filters(uf, municipio, zona, secao), intervalo)
        return use_cases.aggregate_vote_timeline.execute(query)

    @router.get(
        "/{ano}/{turno}/votos-apos/{cargo}",
        response_model=LateVotesReportOut,
        summary="Votos depois de um horário: total exato e ESTIMATIVA por votável",
    )
    def estimate_late_votes(
        ano: int,
        turno: int,
        cargo: int,
        apos: str = Query("17:00", description="horário de Brasília, múltiplo de 15 minutos"),
        agrupar: Grouping = Grouping.TOTAL,
        uf: str | None = None,
        municipio: int | None = None,
        zona: int | None = None,
        secao: int | None = None,
        limit: int = Query(100, ge=1, le=10000),
        offset: int = Query(0, ge=0),
    ) -> dict[str, Any]:
        query = LateVotesQuery(ano, turno, cargo, apos, agrupar, _filters(uf, municipio, zona, secao), limit, offset)
        report = use_cases.estimate_late_votes.execute(query)
        return {
            "after": report.after,
            "method": LATE_VOTES_METHOD,
            "summary": report.summary,
            "votables": report.votables,
        }

    return router
