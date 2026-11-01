from ..domain.models import ImportedDataset
from ..domain.ports import VoteRepository


class GetImportStatus:
    def __init__(self, repository: VoteRepository):
        self._repository = repository

    def execute(self) -> list[ImportedDataset]:
        return self._repository.imported()
