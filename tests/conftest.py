import dataclasses
import json
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from tse_api.bootstrap.app import create_app
from tse_api.modules.open_data.domain.models import SectionUrnRecord
from tse_api.modules.open_data.infrastructure.duckdb_vote_repository import DuckDbVoteRepository
from tse_api.shared.config import Settings

FIXTURES = Path(__file__).parent / "fixtures"
SECTION_DIR = "ele2026/arquivo-urna/3220/dados/ac/01066/0004/0077"
BU_FILE = "o03220ac0106600040077-bu.dat"
LOG_FILE = "o03220ac0106600040077-log.jez"
BU_HASH = json.loads((FIXTURES / "aux.json").read_text())["hashes"][0]["hash"]

# Lista de seções reduzida (o arquivo real do AC tem 146 KB).
SECTIONS_JSON = {
    "dg": "05/10/2026",
    "hg": "02:59:38",
    "abr": [
        {
            "cd": "ac",
            "mu": [
                {
                    "cd": "01066",
                    "nm": "PORTO WALTER",
                    "zon": [
                        {
                            "cd": "0004",
                            "sec": [
                                {"ns": "0077", "da": "04/10/2026", "ha": "21:08:17"},
                                {"ns": "0078", "da": "04/10/2026", "ha": "21:08:17"},
                            ],
                        }
                    ],
                },
                {
                    "cd": "01120",
                    "nm": "ACRELÂNDIA",
                    "zon": [{"cd": "0008", "sec": [{"ns": "0001", "da": "04/10/2026", "ha": "20:00:00"}]}],
                },
            ],
        }
    ],
}

MUNICIPALITIES_JSON = {
    "abr": [
        {"cd": "ac", "mu": [{"cd": "01066", "cdi": "1200393", "nm": "PORTO WALTER", "c": "n", "z": ["0004"]}]},
        {"cd": "sp", "mu": [{"cd": "71072", "cdi": "3550308", "nm": "SÃO PAULO", "c": "s", "z": ["0001", "0002"]}]},
    ]
}

ROUTES: dict[str, bytes] = {
    "/oficial/comum/config/ele-c.json": (FIXTURES / "ele-c.json").read_bytes(),
    f"/oficial/{SECTION_DIR}/p003220-ac-m01066-z0004-s0077-aux.json": (FIXTURES / "aux.json").read_bytes(),
    f"/oficial/{SECTION_DIR}/{BU_HASH}/{BU_FILE}": (FIXTURES / BU_FILE).read_bytes(),
    f"/oficial/{SECTION_DIR}/{BU_HASH}/{LOG_FILE}": (FIXTURES / LOG_FILE).read_bytes(),
    "/oficial/ele2026/6257/dados/ac/ac01066-c0001-e006257-u.json": (
        FIXTURES / "ac01066-c0001-e006257-u.json"
    ).read_bytes(),
    "/oficial/ele2026/arquivo-urna/3220/config/ac/ac-p003220-cs.json": json.dumps(SECTIONS_JSON).encode(),
    "/oficial/ele2026/6257/config/mun-e006257-cm.json": json.dumps(MUNICIPALITIES_JSON).encode(),
}


def fake_tse(routes: dict[str, bytes]) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        body = routes.get(request.url.path)
        if body is None:
            return httpx.Response(404, text="<Error><Code>NoSuchKey</Code></Error>")
        return httpx.Response(200, content=body)

    return handler


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return dataclasses.replace(
        Settings(), data_dir=tmp_path, frontend_dist=tmp_path / "sem-frontend", log_format="text"
    )


@pytest.fixture
def tse_transport() -> httpx.MockTransport:
    return httpx.MockTransport(fake_tse(ROUTES))


@pytest.fixture
def api(settings: Settings, tse_transport: httpx.MockTransport) -> Iterator[TestClient]:
    with TestClient(create_app(settings, tse_transport)) as client:
        yield client


# Seção 175 da zona 4 de Cruzeiro do Sul (AC), presente no CSV de amostra (191 votantes de 256 aptos).
# O pacote de urnas é simulado: 100 votos às 6h locais (8h de Brasília) e 91 às 15h locais (17h).
URN_RECORD = SectionUrnRecord(
    uf="AC",
    municipality=1074,
    zone=4,
    section=175,
    polling_place=2143,
    urn_kind="secao",
    urn_number=2280689,
    software_version="10.23.0.0",
    opened_at="2026-10-04T06:00:01",
    closed_at="2026-10-04T15:20:00",
    issued_at="2026-10-04T15:21:00",
    eligible_voters=256,
    eligible_in_section=256,
    eligible_in_transit=0,
    turnout=191,
    without_biometrics=41,
    enabled_by_biometrics=140,
    enabled_by_birth_year=10,
    log_votes=191,
    votes_by_quarter_hour={360: {"biometria": 100}, 900: {"biometria": 40, "sem_biometria": 41, "ano_nascimento": 10}},
)


def load_sample_database(settings: Settings) -> DuckDbVoteRepository:
    repository = DuckDbVoteRepository(settings.database_path, read_only=False)
    repository.load(FIXTURES / "bweb_amostra.csv", 2026, 1, "AC")
    repository.load_urn_records(iter([URN_RECORD]), 2026, 1, "AC", "pacote_teste.zip")
    return repository
