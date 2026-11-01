import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ....shared.errors import InvalidInputError
from ..domain.models import DatasetFile, DatasetKind
from ..domain.ports import DatasetDownloader, UrnPackageReader, VoteRepository
from .list_available_datasets import ListAvailableDatasets

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImportReport:
    file: DatasetFile
    rows: int
    seconds: float


def _ignore_sections(done: int, total: int) -> None:
    return None


class ImportBallotDatasets:
    """Baixa os arquivos escolhidos e (re)carrega cada (ano, turno, UF) na base local.

    - ``boletins``: CSV com votos por votável, cargo e seção;
    - ``urnas``: pacote com BU e log de cada seção (biometria detalhada e votos por horário).
    """

    def __init__(
        self,
        available: ListAvailableDatasets,
        downloader: DatasetDownloader,
        urn_reader: UrnPackageReader,
        repository: VoteRepository,
        work_dir: Path,
    ):
        self._available = available
        self._downloader = downloader
        self._urn_reader = urn_reader
        self._repository = repository
        self._work_dir = work_dir

    def execute(
        self,
        year: int,
        rounds: list[int],
        ufs: list[str] | None,
        kinds: tuple[DatasetKind, ...] = (DatasetKind.BALLOTS_CSV,),
        keep_files: bool = False,
        on_progress: Callable[[ImportReport], None] = lambda _: None,
        on_sections: Callable[[int, int], None] = _ignore_sections,
        on_missing: Callable[[str], None] = lambda _: None,
    ) -> list[ImportReport]:
        reports = []
        for dataset_file in [f for kind in kinds for f in self._select(year, rounds, ufs, kind, on_missing)]:
            started = time.monotonic()
            rows = self._import(dataset_file, year, keep_files, on_sections)
            report = ImportReport(dataset_file, rows, time.monotonic() - started)
            logger.info("dataset importado", extra={"file": dataset_file.name, "rows": rows})
            on_progress(report)
            reports.append(report)
        return reports

    def _import(self, file: DatasetFile, year: int, keep_files: bool, on_sections: Callable[[int, int], None]) -> int:
        zip_path = self._downloader.download_archive(file, self._work_dir / str(year))
        extracted: Path | None = None
        try:
            if file.kind == DatasetKind.BALLOTS_CSV:
                extracted = self._downloader.extract_csv(zip_path)
                return self._repository.load(extracted, year, file.round, file.uf)
            records = self._urn_reader.read(zip_path, on_sections)
            return self._repository.load_urn_records(records, year, file.round, file.uf, file.name)
        finally:
            if not keep_files:
                zip_path.unlink(missing_ok=True)
                if extracted:
                    extracted.unlink(missing_ok=True)

    def _select(
        self, year: int, rounds: list[int], ufs: list[str] | None, kind: DatasetKind, on_missing: Callable[[str], None]
    ) -> list[DatasetFile]:
        files = self._available.execute(year, rounds, kind)
        published = {f.uf for f in files}
        wanted = {uf.upper() for uf in ufs} if ufs is not None else published
        unknown = wanted - published
        if ufs is not None and unknown:
            raise InvalidInputError(f"sem arquivo '{kind.value}' publicado para: {', '.join(sorted(unknown))}")
        for round_ in rounds:
            missing = wanted - {f.uf for f in files if f.round == round_}
            if missing:
                on_missing(f"'{kind.value}' do {round_}º turno ainda não publicado para: {', '.join(sorted(missing))}")
        return [f for f in files if f.uf in wanted]
