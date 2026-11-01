import httpx
import pytest

from tse_api.modules.geography.domain.models import MeshNotFound
from tse_api.modules.geography.infrastructure.ibge_mesh_source import IbgeMeshSource

pytestmark = pytest.mark.anyio

GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"codarea": "12"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[-70.123456789, -10], [-69, -10.5], [-70.123456789, -10]]],
            },
        }
    ],
}


def source(tmp_path, calls):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if "estados/99" in request.url.path:
            return httpx.Response(404)
        return httpx.Response(200, json=GEOJSON)

    return IbgeMeshSource("https://ibge.test/api/v3/malhas", tmp_path, httpx.MockTransport(handler))


async def test_normalizes_rounds_and_caches_on_disk(tmp_path):
    calls: list[str] = []
    meshes = source(tmp_path, calls)
    [feature] = await meshes.fetch_states()
    assert feature["properties"] == {"codigo_ibge": 12}
    assert feature["geometry"]["coordinates"][0][0] == [-70.1235, -10]
    assert "intrarregiao=UF" in calls[0] and "qualidade=minima" in calls[0]
    await meshes.fetch_states()
    assert len(calls) == 1 and (tmp_path / "brasil-uf.json").exists()
    await meshes.fetch_municipalities(12)
    assert "estados/12" in calls[1] and "intrarregiao=municipio" in calls[1]
    await meshes.aclose()


async def test_missing_mesh(tmp_path):
    with pytest.raises(MeshNotFound):
        await source(tmp_path, []).fetch_municipalities(99)
