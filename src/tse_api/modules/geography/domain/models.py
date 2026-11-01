"""Malhas geográficas usadas nos mapas do painel."""

from dataclasses import dataclass
from typing import Any

from ....shared.errors import NotFoundError


class MeshNotFound(NotFoundError):
    slug = "mesh-not-found"
    title = "Malha geográfica não encontrada"


@dataclass(frozen=True)
class Mesh:
    """GeoJSON ``FeatureCollection``. Cada feição traz o código IBGE em ``codigo_ibge``."""

    scope: str  # "br" (feições = UFs) ou a sigla da UF (feições = municípios)
    features: list[dict[str, Any]]

    def as_geojson(self) -> dict[str, Any]:
        return {"type": "FeatureCollection", "features": self.features}
