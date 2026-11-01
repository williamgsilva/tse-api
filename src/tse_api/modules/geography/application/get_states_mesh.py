from ....shared.uf import IBGE_STATE_CODES, region_of
from ..domain.models import Mesh
from ..domain.ports import MeshSource

_UF_BY_CODE = {code: uf for uf, code in IBGE_STATE_CODES.items()}


class GetStatesMesh:
    """Mapa do Brasil por UF, com sigla e região em cada feição."""

    def __init__(self, source: MeshSource):
        self._source = source

    async def execute(self) -> Mesh:
        features = []
        for feature in await self._source.fetch_states():
            uf = _UF_BY_CODE.get(int(feature["properties"]["codigo_ibge"]))
            if uf is None:
                continue
            properties = {**feature["properties"], "uf": uf, "regiao": region_of(uf)}
            features.append({**feature, "properties": properties})
        return Mesh("br", features)
