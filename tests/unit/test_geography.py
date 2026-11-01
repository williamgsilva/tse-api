import pytest

from tests.unit.test_elections import CATALOG, FakeSource
from tse_api.modules.elections.application.get_subdivision_results import GetSubdivisionResults
from tse_api.modules.elections.domain.models import Candidate, ElectionResult, ResultNotPublished, Totals
from tse_api.modules.geography.application.get_municipalities_mesh import GetMunicipalitiesMesh
from tse_api.modules.geography.application.get_states_mesh import GetStatesMesh
from tse_api.shared.errors import InvalidInputError
from tse_api.shared.uf import region_of

pytestmark = pytest.mark.anyio


def candidate(number: int, votes: int) -> Candidate:
    return Candidate(number, f"C{number}", f"C{number}", None, "P", 1, None, None, votes, None, False, None, None)


class SubdivisionSource(FakeSource):
    async def fetch_result(self, election, uf, office_code, municipality_code):
        if uf == "sp" and municipality_code is None:
            raise ResultNotPublished("sem SP")
        office = type("O", (), {"candidates": (candidate(1, 10), candidate(2, 30), candidate(3, 20))})
        return ElectionResult(election.code, 1, "uf", uf, None, True, Totals(), (office,))  # type: ignore[arg-type]


async def test_states_skip_unpublished_and_keep_top_candidates():
    results = await GetSubdivisionResults(SubdivisionSource()).execute(6257, "br", 1, top=2)
    codes = [r.code for r in results]
    assert "sp" not in codes and "ac" in codes and len(codes) == 26
    assert [c.number for c in results[0].candidates] == [2, 3]
    assert results[0].scope_type == "uf" and results[0].ibge_code == 12


async def test_municipalities_of_state():
    [only] = await GetSubdivisionResults(SubdivisionSource()).execute(6257, "AC", 1)
    assert (only.scope_type, only.code, only.name) == ("mu", "1066", "PORTO WALTER")
    with pytest.raises(InvalidInputError):
        await GetSubdivisionResults(SubdivisionSource()).execute(6257, "ac", 1, top=0)
    assert CATALOG.election(6257).code == 6257


class FakeMeshes:
    async def fetch_states(self):
        return [
            {"type": "Feature", "properties": {"codigo_ibge": 12}, "geometry": None},
            {"type": "Feature", "properties": {"codigo_ibge": 99}, "geometry": None},
        ]

    async def fetch_municipalities(self, code):
        return [{"type": "Feature", "properties": {"codigo_ibge": code * 100000 + 1}, "geometry": None}]


async def test_states_mesh_adds_uf_and_region():
    mesh = await GetStatesMesh(FakeMeshes()).execute()
    assert [f["properties"] for f in mesh.features] == [{"codigo_ibge": 12, "uf": "ac", "regiao": "norte"}]
    assert mesh.as_geojson()["type"] == "FeatureCollection"


async def test_municipalities_mesh():
    mesh = await GetMunicipalitiesMesh(FakeMeshes()).execute("SP")
    assert mesh.scope == "sp" and mesh.features[0]["properties"]["codigo_ibge"] == 3500001
    with pytest.raises(InvalidInputError):
        await GetMunicipalitiesMesh(FakeMeshes()).execute("zz")


def test_region_of():
    assert (region_of("ac"), region_of("df"), region_of("rs"), region_of("zz")) == (
        "norte",
        "centro-oeste",
        "sul",
        None,
    )
