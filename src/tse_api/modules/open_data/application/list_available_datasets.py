from ..domain.models import DatasetFile, DatasetKind, latest_per_round_and_uf
from ..domain.ports import DatasetCatalog


class ListAvailableDatasets:
    def __init__(self, catalog: DatasetCatalog):
        self._catalog = catalog

    def execute(self, year: int, rounds: list[int], kind: DatasetKind = DatasetKind.BALLOTS_CSV) -> list[DatasetFile]:
        return [f for f in latest_per_round_and_uf(self._catalog.list_files(year, kind)) if f.round in rounds]
