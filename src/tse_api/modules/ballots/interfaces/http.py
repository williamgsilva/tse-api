from dataclasses import dataclass

from fastapi import APIRouter, Query
from fastapi.responses import Response

from ..application.download_urn_file import DownloadUrnFile
from ..application.get_ballot_report import GetBallotReport
from ..application.get_section_status import GetSectionStatus
from ..application.get_vote_timeline import GetVoteTimeline, SectionVoteTimeline
from ..application.list_sections import ListSections
from ..domain.models import BallotReport, SectionStatus
from ..domain.timeline import parse_clock
from .schemas import (
    BallotReportOut,
    SectionPageOut,
    SectionStatusOut,
    SectionSummaryOut,
    SectionVoteTimelineOut,
    UrnFileOut,
    UrnFileSetOut,
)


@dataclass(frozen=True)
class BallotUseCases:
    list_sections: ListSections
    get_section_status: GetSectionStatus
    get_ballot_report: GetBallotReport
    download_urn_file: DownloadUrnFile
    get_vote_timeline: GetVoteTimeline


def _section_status_out(status: SectionStatus) -> SectionStatusOut:
    current = status.current_file_set().hash if status.file_sets else None
    return SectionStatusOut(
        voting_event_code=status.voting_event_code,
        uf=status.key.uf,
        municipality=status.key.municipality,
        zone=status.key.zone,
        section=status.key.section,
        status=status.status,
        updated_at=status.updated_at,
        file_sets=[
            UrnFileSetOut(
                hash=fs.hash,
                status=fs.status,
                received_at=fs.received_at,
                is_current=fs.hash == current,
                files=[UrnFileOut.model_validate(f) for f in fs.files],
            )
            for fs in status.file_sets
        ],
    )


def build_router(use_cases: BallotUseCases) -> APIRouter:
    router = APIRouter(prefix="/pleitos/{pleito}/secoes/{uf}", tags=["urnas e boletins (portal de resultados)"])

    @router.get("", response_model=SectionPageOut, summary="Seções com arquivos de urna publicados")
    async def list_sections(
        pleito: int,
        uf: str,
        municipio: int | None = None,
        zona: int | None = None,
        limit: int = Query(1000, ge=1, le=10000),
        cursor: str | None = Query(None, description="valor de `proximo_cursor` da página anterior"),
    ) -> SectionPageOut:
        page = await use_cases.list_sections.execute(pleito, uf, municipio, zona, limit, cursor)
        return SectionPageOut(
            total=page.total,
            next_cursor=page.next_cursor,
            items=[
                SectionSummaryOut(
                    uf=s.key.uf,
                    municipality=s.key.municipality,
                    municipality_name=s.municipality_name,
                    zone=s.key.zone,
                    section=s.key.section,
                    updated_at=s.updated_at,
                )
                for s in page.items
            ],
        )

    @router.get(
        "/{municipio}/{zona}/{secao}", response_model=SectionStatusOut, summary="Situação da seção e arquivos da urna"
    )
    async def get_section_status(pleito: int, uf: str, municipio: int, zona: int, secao: int) -> SectionStatusOut:
        return _section_status_out(await use_cases.get_section_status.execute(pleito, uf, municipio, zona, secao))

    @router.get(
        "/{municipio}/{zona}/{secao}/boletim", response_model=BallotReportOut, summary="Boletim de urna decodificado"
    )
    async def get_ballot_report(
        pleito: int,
        uf: str,
        municipio: int,
        zona: int,
        secao: int,
        nomes: bool = Query(True, description="acrescenta nomes de eleições, candidatos e partidos"),
    ) -> BallotReport:
        return await use_cases.get_ballot_report.execute(pleito, uf, municipio, zona, secao, with_names=nomes)

    @router.get(
        "/{municipio}/{zona}/{secao}/horarios",
        response_model=SectionVoteTimelineOut,
        summary="Votos por horário (log da urna) e estimativa dos votos após um horário",
    )
    async def get_vote_timeline(
        pleito: int,
        uf: str,
        municipio: int,
        zona: int,
        secao: int,
        apos: str = Query("17:00", description="horário de Brasília (HH:MM)"),
    ) -> SectionVoteTimeline:
        return await use_cases.get_vote_timeline.execute(pleito, uf, municipio, zona, secao, parse_clock(apos))

    @router.get(
        "/{municipio}/{zona}/{secao}/arquivos/{tipo}",
        response_class=Response,
        summary="Arquivo original da urna (bu, rdv, log, vota…)",
        responses={200: {"content": {"application/octet-stream": {}}}},
    )
    async def download_urn_file(pleito: int, uf: str, municipio: int, zona: int, secao: int, tipo: str) -> Response:
        downloaded = await use_cases.download_urn_file.execute(pleito, uf, municipio, zona, secao, tipo)
        return Response(
            downloaded.content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{downloaded.name}"'},
        )

    return router
