from dataclasses import dataclass

from fastapi import APIRouter, Query

from ..application.get_coverage import GetCoverage
from ..application.get_election import GetElection
from ..application.get_election_result import GetElectionResult
from ..application.get_subdivision_results import GetSubdivisionResults
from ..application.list_municipalities import ListMunicipalities
from ..application.list_voting_events import ListVotingEvents
from ..domain.models import Coverage, Election, ElectionResult, Municipality, SubdivisionResult, VotingEvent
from .schemas import (
    CoverageOut,
    ElectionOut,
    ElectionResultOut,
    MunicipalityOut,
    SubdivisionResultOut,
    VotingEventOut,
)


@dataclass(frozen=True)
class ElectionUseCases:
    list_voting_events: ListVotingEvents
    get_election: GetElection
    list_municipalities: ListMunicipalities
    get_election_result: GetElectionResult
    get_coverage: GetCoverage
    get_subdivision_results: GetSubdivisionResults


def build_router(use_cases: ElectionUseCases) -> APIRouter:
    router = APIRouter(prefix="/eleicoes", tags=["eleições e resultados"])

    @router.get("", response_model=list[VotingEventOut], summary="Pleitos e eleições publicados pelo TSE")
    async def list_voting_events(
        ano: int | None = Query(2026, description="ano do ciclo eleitoral; vazio = todos"),
    ) -> list[VotingEvent]:
        return await use_cases.list_voting_events.execute(ano)

    @router.get("/{eleicao}", response_model=ElectionOut, summary="Detalhes de uma eleição")
    async def get_election(eleicao: int) -> Election:
        return await use_cases.get_election.execute(eleicao)

    @router.get("/{eleicao}/municipios", response_model=list[MunicipalityOut], summary="Municípios e zonas")
    async def list_municipalities(eleicao: int, uf: str | None = None) -> list[Municipality]:
        return await use_cases.list_municipalities.execute(eleicao, uf)

    @router.get(
        "/{eleicao}/abrangencias/{uf}",
        response_model=CoverageOut,
        summary="Seções totalizadas, eleitorado e comparecimento (uf ou br)",
    )
    async def get_coverage(eleicao: int, uf: str) -> Coverage:
        return await use_cases.get_coverage.execute(eleicao, uf)

    @router.get(
        "/{eleicao}/resultados/{uf}/{cargo}",
        response_model=ElectionResultOut,
        summary="Resultado totalizado de um cargo (br, UF ou município)",
    )
    async def get_election_result(
        eleicao: int,
        uf: str,
        cargo: int,
        municipio: int | None = Query(None, description="código TSE do município"),
    ) -> ElectionResult:
        return await use_cases.get_election_result.execute(eleicao, uf, cargo, municipio)

    @router.get(
        "/{eleicao}/resultados/{uf}/{cargo}/subdivisoes",
        response_model=list[SubdivisionResultOut],
        summary="Resultado de cada UF (uf=br) ou de cada município da UF, com os primeiros colocados (para mapas)",
    )
    async def get_subdivision_results(
        eleicao: int,
        uf: str,
        cargo: int,
        limite: int = Query(3, ge=1, le=20, description="candidatos por subdivisão"),
    ) -> list[SubdivisionResult]:
        return await use_cases.get_subdivision_results.execute(eleicao, uf, cargo, limite)

    return router
