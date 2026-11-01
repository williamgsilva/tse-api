from typing import Any, Protocol


class MeshSource(Protocol):
    async def fetch_states(self) -> list[dict[str, Any]]:
        """Feições das UFs, com ``properties.codigo_ibge`` (2 dígitos)."""
        ...

    async def fetch_municipalities(self, ibge_state_code: int) -> list[dict[str, Any]]:
        """Feições dos municípios da UF, com ``properties.codigo_ibge`` (7 dígitos)."""
        ...
