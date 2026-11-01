import asyncio

from ....shared.errors import InvalidInputError
from ....shared.uf import IBGE_STATE_CODES, NATIONAL, parse_uf
from ..domain.models import Election, ResultNotPublished, SubdivisionResult
from ..domain.ports import ElectionDataSource

MAX_TOP = 20


class GetSubdivisionResults:
    """Resultado de cada UF do Brasil, ou de cada município de uma UF, com os ``top`` primeiros colocados.

    Faz uma consulta por subdivisão (em paralelo, limitada pelo cliente do TSE); as que o TSE não
    publicou para o cargo ficam de fora.
    """

    def __init__(self, source: ElectionDataSource):
        self._source = source

    async def execute(self, election_code: int, uf: str, office_code: int, top: int = 3) -> list[SubdivisionResult]:
        if not 1 <= top <= MAX_TOP:
            raise InvalidInputError(f"limite deve estar entre 1 e {MAX_TOP}")
        election = (await self._source.fetch_catalog()).election(election_code)
        election.require_office(office_code)
        scope = parse_uf(uf, allow_national=True)
        areas: list[tuple[str, str, int | None, int | None, str]]
        if scope == NATIONAL:
            areas = [("uf", state, None, code, state.upper()) for state, code in sorted(IBGE_STATE_CODES.items())]
        else:
            areas = [
                ("mu", scope, m.code, m.ibge_code, m.name)
                for m in await self._source.fetch_municipalities(election)
                if m.uf == scope
            ]
        results = await asyncio.gather(*(self._one(election, office_code, top, *area) for area in areas))
        return [r for r in results if r is not None]

    async def _one(
        self,
        election: Election,
        office_code: int,
        top: int,
        scope_type: str,
        uf: str,
        municipality: int | None,
        ibge_code: int | None,
        name: str,
    ) -> SubdivisionResult | None:
        try:
            result = await self._source.fetch_result(election, uf, office_code, municipality)
        except ResultNotPublished:
            return None
        candidates = tuple(c for office in result.offices for c in office.candidates)
        return SubdivisionResult(
            scope_type=scope_type,
            code=str(municipality) if municipality is not None else uf,
            ibge_code=ibge_code,
            name=name,
            is_final=result.is_final,
            totals=result.totals,
            candidates=tuple(sorted(candidates, key=lambda c: c.votes, reverse=True)[:top]),
        )
