from ....shared.errors import InvalidInputError
from ....shared.uf import IBGE_STATE_CODES, parse_uf
from ..domain.models import Mesh
from ..domain.ports import MeshSource


class GetMunicipalitiesMesh:
    """Mapa de uma UF por município (o código IBGE liga a feição ao município do TSE)."""

    def __init__(self, source: MeshSource):
        self._source = source

    async def execute(self, uf: str) -> Mesh:
        code = parse_uf(uf)
        if code not in IBGE_STATE_CODES:
            raise InvalidInputError("não há mapa para o exterior")
        return Mesh(code, await self._source.fetch_municipalities(IBGE_STATE_CODES[code]))
