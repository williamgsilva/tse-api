from typing import Protocol

from .models import Catalog, Coverage, Election, ElectionResult, Municipality


class ElectionDataSource(Protocol):
    async def fetch_catalog(self) -> Catalog: ...

    async def fetch_municipalities(self, election: Election) -> list[Municipality]: ...

    async def fetch_result(
        self, election: Election, uf: str, office_code: int, municipality_code: int | None
    ) -> ElectionResult: ...

    async def fetch_coverage(self, election: Election, uf: str) -> Coverage: ...
