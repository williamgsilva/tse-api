import pytest

from tse_api.modules.elections.application.get_coverage import GetCoverage
from tse_api.modules.elections.application.get_election_result import GetElectionResult
from tse_api.modules.elections.application.list_municipalities import ListMunicipalities
from tse_api.modules.elections.application.list_voting_events import ListVotingEvents
from tse_api.modules.elections.domain.models import (
    Catalog,
    Coverage,
    Election,
    ElectionNotFound,
    ElectionResult,
    Municipality,
    Office,
    Totals,
    VotingEvent,
    VotingEventNotFound,
)
from tse_api.shared.errors import InvalidInputError

pytestmark = pytest.mark.anyio

PRESIDENT = Office(1, "Presidente", "majoritario", ("br",))
ELECTION = Election(6257, "Federal 1º turno", 1, 8, 3220, "ele2026", "2026-10-04", 6258, (PRESIDENT,))
OLD = Election(619, "Municipal 2024", 1, 3, 452, "ele2024", "2024-10-06", 620, ())
CATALOG = Catalog(
    voting_events={
        3220: VotingEvent(3220, "ele2026", "2026-10-04", (ELECTION,)),
        452: VotingEvent(452, "ele2024", "2024-10-06", (OLD,)),
    },
    elections={6257: ELECTION, 619: OLD},
)


class FakeSource:
    def __init__(self):
        self.result_calls = []

    async def fetch_catalog(self):
        return CATALOG

    async def fetch_municipalities(self, election):
        return [
            Municipality("ac", 1066, None, "PORTO WALTER", False, (4,)),
            Municipality("sp", 71072, 3550308, "SÃO PAULO", True, (1,)),
        ]

    async def fetch_result(self, election, uf, office_code, municipality_code):
        self.result_calls.append((election.code, uf, office_code, municipality_code))
        return ElectionResult(election.code, 1, "uf", uf, None, True, Totals(), ())

    async def fetch_coverage(self, election, uf):
        return Coverage(election.code, 1, None)


def test_catalog_lookups():
    assert CATALOG.election(6257).year == 2026
    assert CATALOG.voting_event(3220).year == 2026
    assert [e.code for e in CATALOG.voting_events_of_year(None)] == [452, 3220]
    with pytest.raises(ElectionNotFound):
        CATALOG.election(1)
    with pytest.raises(VotingEventNotFound):
        CATALOG.voting_event(1)


def test_election_requires_known_office():
    assert ELECTION.require_office(1) is PRESIDENT
    with pytest.raises(InvalidInputError):
        ELECTION.require_office(13)


async def test_list_voting_events_filters_by_year():
    events = await ListVotingEvents(FakeSource()).execute(2026)
    assert [e.code for e in events] == [3220]


async def test_list_municipalities_filters_by_uf():
    source = FakeSource()
    assert len(await ListMunicipalities(source).execute(6257, None)) == 2
    assert [m.code for m in await ListMunicipalities(source).execute(6257, "SP")] == [71072]


async def test_get_election_result_normalizes_scope():
    source = FakeSource()
    await GetElectionResult(source).execute(6257, "AC", 1, 1066)
    await GetElectionResult(source).execute(6257, "BR", 1)
    assert source.result_calls == [(6257, "ac", 1, 1066), (6257, "br", 1, None)]


async def test_get_election_result_rejects_invalid_combinations():
    use_case = GetElectionResult(FakeSource())
    with pytest.raises(InvalidInputError):
        await use_case.execute(6257, "br", 1, 1066)
    with pytest.raises(InvalidInputError):
        await use_case.execute(6257, "sp", 99)
    with pytest.raises(ElectionNotFound):
        await use_case.execute(1, "sp", 1)


async def test_get_coverage_accepts_national_scope():
    coverage = await GetCoverage(FakeSource()).execute(6257, "br")
    assert coverage.election_code == 6257
