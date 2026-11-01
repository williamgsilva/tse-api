import hashlib
import io
import zipfile

import httpx
import pytest

from tests.conftest import FIXTURES
from tse_api.modules.open_data.domain.models import (
    DatasetFile,
    DatasetKind,
    Grouping,
    LocalDatabaseUnavailable,
    VoteQuery,
)
from tse_api.modules.open_data.infrastructure.ckan_dataset_catalog import CkanDatasetCatalog
from tse_api.modules.open_data.infrastructure.duckdb_vote_repository import DuckDbVoteRepository
from tse_api.modules.open_data.infrastructure.http_dataset_downloader import HttpDatasetDownloader
from tse_api.shared.errors import UpstreamDataError

CSV = FIXTURES / "bweb_amostra.csv"
ZIP_URL = "https://cdn.tse.jus.br/x/bweb_1t_AC_051020261403.zip"


@pytest.fixture
def repository(tmp_path):
    repo = DuckDbVoteRepository(tmp_path / "bweb.duckdb", read_only=False)
    repo.load(CSV, 2026, 1, "AC")
    return repo


def test_load_is_idempotent_per_round_and_uf(repository):
    assert repository.load(CSV, 2026, 1, "AC") == 199
    [imported] = repository.imported()
    assert (imported.year, imported.round, imported.uf, imported.rows) == (2026, 1, "AC", 199)
    assert imported.source_file == CSV.name


def test_section_votes(repository):
    report = repository.section_votes(2026, 1, "AC", 1074, 4, 175)
    assert report is not None
    assert (report.municipality_name, report.voting_event_code) == ("CRUZEIRO DO SUL", 3220)
    assert report.opened_at == "2026-10-04T06:00:01"
    assert any(v.name == "ELTER NÓBREGA" for o in report.offices for v in o.votes)
    assert repository.section_votes(2026, 1, "AC", 1074, 4, 9999) is None


def test_aggregate_sums_match_raw_rows(repository, tmp_path):
    rows = repository.aggregate(VoteQuery(2026, 1, 7, limit=10000))
    by_municipality = repository.aggregate(VoteQuery(2026, 1, 7, Grouping.MUNICIPALITY, uf="AC", limit=10000))
    assert sum(r.votes for r in rows) == sum(r.votes for r in by_municipality) > 0
    assert all(r.municipality and r.municipality_name for r in by_municipality)
    only_one = repository.aggregate(VoteQuery(2026, 1, 7, votable=rows[0].votable_number))
    assert [r.votable_number for r in only_one] == [rows[0].votable_number]


def test_read_only_repository_without_database(tmp_path):
    repo = DuckDbVoteRepository(tmp_path / "nao-existe.duckdb", read_only=True)
    assert repo.imported() == []
    with pytest.raises(LocalDatabaseUnavailable):
        repo.aggregate(VoteQuery(2026, 1, 1))


def _zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("bweb_1t_AC_051020261403.csv", CSV.read_bytes())
        archive.writestr("_leiame.pdf", b"%PDF")
    return buffer.getvalue()


def _downloader(checksum: str) -> HttpDatasetDownloader:
    content = _zip_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(".sha512"):
            return httpx.Response(200, text=f"{checksum}  bweb_1t_AC_051020261403.zip\n")
        return httpx.Response(200, content=content)

    return HttpDatasetDownloader(httpx.Client(transport=httpx.MockTransport(handler)))


def test_downloader_verifies_checksum_and_extracts_csv(tmp_path):
    file = DatasetFile.from_url(ZIP_URL, ZIP_URL + ".sha512")
    downloader = _downloader(hashlib.sha512(_zip_bytes()).hexdigest())
    zip_path = downloader.download_archive(file, tmp_path)
    assert downloader.extract_csv(zip_path).read_bytes() == CSV.read_bytes()


def test_downloader_rejects_wrong_checksum(tmp_path):
    file = DatasetFile.from_url(ZIP_URL, ZIP_URL + ".sha512")
    with pytest.raises(UpstreamDataError, match="SHA-512"):
        _downloader("0" * 128).download_archive(file, tmp_path)


def test_ckan_catalog_pairs_zip_with_checksum():
    payload = {
        "result": {
            "resources": [
                {"url": ZIP_URL},
                {"url": ZIP_URL + ".sha512"},
                {"url": "https://cdn.tse.jus.br/x/bweb_2t_AC_261020260742.zip"},
                {"url": "https://cdn.tse.jus.br/x/leiame.pdf"},
            ]
        }
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload)))
    files = CkanDatasetCatalog(http, "https://dadosabertos.tse.jus.br").list_files(2026, DatasetKind.BALLOTS_CSV)
    assert [(f.round, f.checksum_url is not None) for f in files] == [(1, True), (2, False)]
