"""Adaptadores do portal de resultados contra arquivos reais do TSE (servidos por um transporte simulado)."""

import json

import httpx
import pytest

from tests.conftest import BU_FILE, FIXTURES, ROUTES, fake_tse
from tse_api.modules.ballots.domain.models import InvalidBallotReport, SectionKey, SectionNotFound
from tse_api.modules.ballots.domain.ports import VotingEventRef
from tse_api.modules.ballots.infrastructure.asn1_ballot_decoder import Asn1BallotDecoder
from tse_api.modules.ballots.infrastructure.tse_urn_file_source import TseUrnFileSource
from tse_api.modules.elections.domain.models import ResultNotPublished
from tse_api.modules.elections.infrastructure import tse_json_mapper as mapper
from tse_api.modules.elections.infrastructure.tse_election_source import TseElectionSource
from tse_api.shared.tse_http import TseHttpClient

pytestmark = pytest.mark.anyio

EVENT = VotingEventRef(3220, "ele2026", {})
KEY = SectionKey("ac", 1066, 4, 77)


@pytest.fixture
def client(settings, tse_transport):
    return TseHttpClient(settings, transport=tse_transport)


def test_decoder_reads_official_ballot_report():
    report = Asn1BallotDecoder().decode((FIXTURES / BU_FILE).read_bytes())
    assert report.phase == "oficial"
    assert report.electoral_id == {"tipo": "idPleito", "codigo": 3220}
    assert report.section == {"municipio": 1066, "zona": 4, "local": 1031, "secao": 77}
    assert report.turnout == 234
    assert report.voting_window == {"abertura": "2026-10-04T06:06:52", "encerramento": "2026-10-04T15:40:41"}
    assert report.turnout_breakdown == {
        "sem_biometria": 9,
        "habilitados_biometria": 212,
        "habilitados_ano_nascimento": 13,
    }
    assert report.urn.voting_software_version.startswith("10.23")
    president = next(o for e in report.elections for o in e.offices if o.code == 1)
    assert president.totals == {"nominal": 217, "legenda": 0, "branco": 4, "nulo": 13}
    assert sorted(o.code for e in report.elections for o in e.offices) == [1, 3, 5, 6, 7]


@pytest.mark.parametrize("raw", [b"", b"\x30\x03\x02\x01\x01", b"lixo"])
def test_decoder_rejects_invalid_content(raw):
    with pytest.raises(InvalidBallotReport):
        Asn1BallotDecoder().decode(raw)


async def test_election_source_maps_catalog_and_result(client):
    source = TseElectionSource(client)
    catalog = await source.fetch_catalog()
    election = catalog.election(6257)
    assert (election.voting_event_code, election.round, election.second_round_code) == (3220, 1, 6258)
    assert catalog.election(6258).voting_event_code == 3221
    result = await source.fetch_result(election, "ac", 1, 1066)
    assert (result.scope_type, result.scope_code, result.is_final) == ("mu", "01066", True)
    candidates = result.offices[0].candidates
    assert list(candidates) == sorted(candidates, key=lambda c: c.votes, reverse=True)
    assert sum(c.votes for c in candidates) == result.totals.votes.nominal
    municipalities = await source.fetch_municipalities(election)
    assert [(m.uf, m.code, m.is_capital) for m in municipalities] == [("ac", 1066, False), ("sp", 71072, True)]


async def test_election_source_translates_missing_file(client):
    source = TseElectionSource(client)
    election = (await source.fetch_catalog()).election(6257)
    with pytest.raises(ResultNotPublished):
        await source.fetch_result(election, "sp", 1, None)


def test_mapper_parses_brazilian_numbers():
    assert mapper.to_float("47,027772356") == pytest.approx(47.027772356)
    assert mapper.to_int("") is None
    assert mapper.br_date_to_iso("25/10/2026", "23:26:38") == "2026-10-25T23:26:38"


async def test_urn_file_source_lists_sections_and_downloads_bu(client):
    source = TseUrnFileSource(client)
    sections = await source.list_sections(EVENT, "ac")
    assert [(s.key.municipality, s.key.section) for s in sections] == [(1066, 77), (1066, 78), (1120, 1)]
    status = await source.fetch_section_status(EVENT, KEY)
    file_set, bu = status.current_file("bu")
    assert bu.url.endswith(f"{file_set.hash}/{BU_FILE}")
    assert await source.fetch_file(EVENT, KEY, file_set, bu) == (FIXTURES / BU_FILE).read_bytes()


async def test_urn_file_source_caches_urn_files_on_disk(settings):
    routes = dict(ROUTES)
    client = TseHttpClient(settings, transport=httpx.MockTransport(fake_tse(routes)))
    source = TseUrnFileSource(client)
    status = await source.fetch_section_status(EVENT, KEY)
    file_set, bu = status.current_file("bu")
    await source.fetch_file(EVENT, KEY, file_set, bu)
    routes.clear()  # o portal "sai do ar": o arquivo de urna vem do cache em disco
    assert await source.fetch_file(EVENT, KEY, file_set, bu) == (FIXTURES / BU_FILE).read_bytes()


async def test_urn_file_source_missing_section(client):
    with pytest.raises(SectionNotFound):
        await TseUrnFileSource(client).fetch_section_status(EVENT, SectionKey("ac", 1066, 4, 9999))


def test_fixture_aux_has_single_totalized_hash():
    aux = json.loads((FIXTURES / "aux.json").read_text())
    assert [h["st"] for h in aux["hashes"]] == ["Totalizado"]
