from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Protocol

from .models import (
    DatasetFile,
    DatasetKind,
    ImportedDataset,
    LateVotesQuery,
    LateVotesReport,
    SectionUrnRecord,
    SectionVotesReport,
    TimelinePoint,
    TimelineQuery,
    TurnoutAggregate,
    TurnoutQuery,
    VoteAggregate,
    VoteQuery,
)


class DatasetCatalog(Protocol):
    def list_files(self, year: int, kind: DatasetKind) -> list[DatasetFile]: ...


class DatasetDownloader(Protocol):
    def download_archive(self, file: DatasetFile, dest_dir: Path) -> Path:
        """Baixa o ZIP (sem reaproveitar download parcial) e confere o SHA-512, se publicado."""
        ...

    def extract_csv(self, zip_path: Path) -> Path: ...


class UrnPackageReader(Protocol):
    def read(self, zip_path: Path, on_progress: Callable[[int, int], None]) -> Iterator[SectionUrnRecord]:
        """Decodifica BU e log de cada seção do pacote; ``on_progress(lidas, total)``."""
        ...


class VoteRepository(Protocol):
    def load(self, csv_path: Path, year: int, round: int, uf: str) -> int: ...

    def load_urn_records(
        self, records: Iterator[SectionUrnRecord], year: int, round: int, uf: str, source: str
    ) -> int: ...

    def imported(self) -> list[ImportedDataset]: ...

    def section_votes(
        self, year: int, round: int, uf: str, municipality: int, zone: int, section: int
    ) -> SectionVotesReport | None: ...

    def aggregate(self, query: VoteQuery) -> list[VoteAggregate]: ...

    def turnout(self, query: TurnoutQuery) -> list[TurnoutAggregate]: ...

    def timeline(self, query: TimelineQuery) -> list[TimelinePoint]: ...

    def late_votes(self, query: LateVotesQuery) -> LateVotesReport: ...
