from ....shared.errors import InvalidInputError
from ....shared.uf import NATIONAL, parse_uf
from ..domain.models import ElectionResult
from ..domain.ports import ElectionDataSource


class GetElectionResult:
    """Resultado totalizado de um cargo no Brasil, numa UF ou num município."""

    def __init__(self, source: ElectionDataSource):
        self._source = source

    async def execute(
        self, election_code: int, uf: str, office_code: int, municipality_code: int | None = None
    ) -> ElectionResult:
        election = (await self._source.fetch_catalog()).election(election_code)
        election.require_office(office_code)
        scope = parse_uf(uf, allow_national=True)
        if scope == NATIONAL and municipality_code is not None:
            raise InvalidInputError("informe a UF do município em vez de 'br'")
        return await self._source.fetch_result(election, scope, office_code, municipality_code)
