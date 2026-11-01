"""Lê o pacote "Arquivos transmitidos para totalização" (um ZIP por UF e turno).

O ZIP é plano, com quatro arquivos por seção: ``o<pleito><uf><município><zona><seção>-bu.dat``,
``-log.jez``, ``-rdv.dat`` e ``-vota.vsc``. Aqui interessam o BU (biometria, aptos, horários) e o
log (votos por horário). A decodificação usa a API pública do módulo de boletins e roda em
vários processos, porque uma UF grande (SP) tem ~100 mil seções.
"""

import logging
import multiprocessing as mp
import re
import zipfile
from collections.abc import Callable, Iterator
from pathlib import Path

from ...ballots import Asn1BallotDecoder, InvalidBallotReport, JezUrnLogReader
from ..domain.models import SectionUrnRecord
from ..domain.ports import UrnPackageReader

logger = logging.getLogger(__name__)

_MEMBER = re.compile(r"^o\d{5}([a-z]{2})(\d{5})(\d{4})(\d{4})-(bu\.dat|log\.jez)$")
QUARTER = 15

_archive: zipfile.ZipFile | None = None


def _open_archive(path: str) -> None:
    global _archive  # um ZipFile por processo: abrir o índice de SP a cada seção seria caro
    _archive = zipfile.ZipFile(path)


def _decode(task: tuple[str, str | None]) -> SectionUrnRecord | None:
    bu_name, log_name = task
    assert _archive is not None
    try:
        report = Asn1BallotDecoder().decode(_archive.read(bu_name))
        events = JezUrnLogReader().read_votes(_archive.read(log_name), report.voting_date) if log_name else []
    except (InvalidBallotReport, KeyError, ValueError) as exc:
        logger.warning("seção ignorada", extra={"file": bu_name, "error": str(exc)})
        return None
    quarters: dict[int, dict[str, int]] = {}
    for event in events:
        minute = (event.at.hour * 60 + event.at.minute) // QUARTER * QUARTER
        kinds = quarters.setdefault(minute, {})
        kinds[event.enablement] = kinds.get(event.enablement, 0) + 1
    breakdown = report.turnout_breakdown or {}
    window = report.voting_window or {}
    match = _MEMBER.match(bu_name)
    assert match is not None
    return SectionUrnRecord(
        uf=match[1].upper(),
        municipality=report.section["municipio"],
        zone=report.section["zona"],
        section=report.section["secao"],
        polling_place=report.section["local"],
        urn_kind=report.urn.kind,
        urn_number=report.urn.internal_number,
        software_version=report.urn.voting_software_version,
        opened_at=window.get("abertura"),
        closed_at=window.get("encerramento"),
        issued_at=report.issued_at,
        eligible_voters=max((e.eligible_voters for e in report.elections), default=0),
        eligible_in_section=max((e.eligible_in_section for e in report.elections), default=0),
        eligible_in_transit=max((e.eligible_in_transit for e in report.elections), default=0),
        turnout=report.turnout,
        without_biometrics=breakdown.get("sem_biometria"),
        enabled_by_biometrics=breakdown.get("habilitados_biometria"),
        enabled_by_birth_year=breakdown.get("habilitados_ano_nascimento"),
        log_votes=len(events),
        votes_by_quarter_hour=quarters,
    )


def section_tasks(names: list[str]) -> list[tuple[str, str | None]]:
    """Pares (BU, log) por seção, a partir dos nomes do ZIP."""
    sections: dict[str, dict[str, str]] = {}
    for name in names:
        match = _MEMBER.match(name)
        if match:
            sections.setdefault(name.rsplit("-", 1)[0], {})[match[5]] = name
    return [(files["bu.dat"], files.get("log.jez")) for files in sections.values() if "bu.dat" in files]


class ZipUrnPackageReader(UrnPackageReader):
    def __init__(self, processes: int | None = None):
        self._processes = processes or max(1, (mp.cpu_count() or 2) - 1)

    def read(self, zip_path: Path, on_progress: Callable[[int, int], None]) -> Iterator[SectionUrnRecord]:
        with zipfile.ZipFile(zip_path) as archive:
            tasks = section_tasks(archive.namelist())
        total = len(tasks)
        if self._processes == 1:
            _open_archive(str(zip_path))
            results: Iterator[SectionUrnRecord | None] = map(_decode, tasks)
            yield from _with_progress(results, total, on_progress)
            return
        with mp.get_context("spawn").Pool(self._processes, _open_archive, (str(zip_path),)) as pool:
            yield from _with_progress(pool.imap_unordered(_decode, tasks, chunksize=32), total, on_progress)


def _with_progress(
    results: Iterator[SectionUrnRecord | None], total: int, on_progress: Callable[[int, int], None]
) -> Iterator[SectionUrnRecord]:
    for done, record in enumerate(results, start=1):
        if done % 500 == 0 or done == total:
            on_progress(done, total)
        if record is not None:
            yield record
