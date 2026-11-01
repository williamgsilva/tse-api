from pathlib import Path

import pytest

from tse_api.modules.open_data.application.aggregate_turnout import AggregateTurnout
from tse_api.modules.open_data.application.aggregate_vote_timeline import AggregateVoteTimeline
from tse_api.modules.open_data.application.aggregate_votes import AggregateVotes
from tse_api.modules.open_data.application.estimate_late_votes import EstimateLateVotes
from tse_api.modules.open_data.application.get_section_votes import GetSectionVotes
from tse_api.modules.open_data.application.import_ballot_datasets import ImportBallotDatasets
from tse_api.modules.open_data.application.list_available_datasets import ListAvailableDatasets
from tse_api.modules.open_data.domain.models import (
    DatasetFile,
    DatasetKind,
    Grouping,
    LateVotesQuery,
    SectionFilter,
    SectionVotesNotFound,
    TimelineQuery,
    TurnoutQuery,
    VoteQuery,
    latest_per_round_and_uf,
    minutes_of,
)
from tse_api.shared.errors import InvalidInputError

BASE = "https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/buweb"


def dataset(name: str) -> DatasetFile:
    file = DatasetFile.from_url(f"{BASE}/{name}", None)
    assert file is not None
    return file


def test_dataset_file_parses_name():
    file = dataset("bweb_2t_SP_261020260742.zip")
    assert (file.round, file.uf, file.name, file.published_order) == (
        2,
        "SP",
        "bweb_2t_SP_261020260742.zip",
        "202610260742",
    )
    assert file.kind == DatasetKind.BALLOTS_CSV
    assert DatasetFile.from_url(f"{BASE}/bweb_1t_SP_051020261403.zip.sha512", None) is None
    urns = dataset("bu_imgbu_logjez_rdv_vscmr_2026_1t_SP.zip")
    assert (urns.kind, urns.round, urns.uf, urns.published_order) == (DatasetKind.URN_FILES, 1, "SP", "")


def test_latest_per_round_and_uf_keeps_newest_republication():
    files = [
        dataset("bweb_1t_AC_051020261403.zip"),
        dataset("bweb_1t_AC_061020260900.zip"),
        dataset("bweb_1t_AL_051020261403.zip"),
        dataset("bweb_2t_AC_261020260742.zip"),
    ]
    latest = latest_per_round_and_uf(files)
    assert [f.name for f in latest] == [
        "bweb_1t_AC_061020260900.zip",
        "bweb_1t_AL_051020261403.zip",
        "bweb_2t_AC_261020260742.zip",
    ]


@pytest.mark.parametrize("kwargs", [{"limit": 0}, {"limit": 10001}, {"offset": -1}])
def test_vote_query_validates_paging(kwargs):
    with pytest.raises(InvalidInputError):
        VoteQuery(2026, 1, 1, **kwargs)


URN_FILES = [dataset("bu_imgbu_logjez_rdv_vscmr_2026_1t_AC.zip"), dataset("bu_imgbu_logjez_rdv_vscmr_2026_1t_SP.zip")]


class FakeCatalog:
    def list_files(self, year, kind):
        if kind == DatasetKind.URN_FILES:
            return URN_FILES
        return [
            dataset("bweb_1t_AC_051020261403.zip"),
            dataset("bweb_2t_AC_261020260742.zip"),
            dataset("bweb_1t_SP_051020261403.zip"),
        ]


class FakeDownloader:
    def download_archive(self, file, dest_dir):
        dest_dir.mkdir(parents=True, exist_ok=True)
        path = dest_dir / file.name
        path.write_text("zip")
        return path

    def extract_csv(self, zip_path):
        path = zip_path.with_suffix(".csv")
        path.write_text("csv")
        return path


class FakeUrnReader:
    def read(self, zip_path, on_progress):
        on_progress(1, 1)
        yield "registro"


class FakeRepository:
    def __init__(self):
        self.loaded = []
        self.queries = []

    def load(self, csv_path, year, round, uf):
        self.loaded.append((csv_path.name, year, round, uf))
        return 10

    def load_urn_records(self, records, year, round, uf, source):
        self.loaded.append((source, year, round, uf))
        return len(list(records))

    def section_votes(self, *args):
        return None

    def aggregate(self, query):
        self.queries.append(query)
        return []

    turnout = timeline = late_votes = aggregate


def importer(repository: FakeRepository, work_dir: Path) -> ImportBallotDatasets:
    return ImportBallotDatasets(
        ListAvailableDatasets(FakeCatalog()), FakeDownloader(), FakeUrnReader(), repository, work_dir
    )


def test_import_loads_selected_files_and_removes_downloads(tmp_path):
    repository = FakeRepository()
    progress = []
    reports = importer(repository, tmp_path).execute(2026, [1], ["ac", "SP"], on_progress=progress.append)
    assert [r.rows for r in reports] == [10, 10] and len(progress) == 2
    assert [(y, r, uf) for _, y, r, uf in repository.loaded] == [(2026, 1, "AC"), (2026, 1, "SP")]
    assert not list((tmp_path / "2026").iterdir())


def test_import_all_ufs_and_keep_files(tmp_path):
    repository = FakeRepository()
    importer(repository, tmp_path).execute(2026, [1, 2], None, keep_files=True)
    assert len(repository.loaded) == 3
    assert len(list((tmp_path / "2026").glob("*.csv"))) == 3


def test_import_urn_packages_and_warn_missing_round(tmp_path):
    repository = FakeRepository()
    missing, sections = [], []
    reports = importer(repository, tmp_path).execute(
        2026,
        [1, 2],
        ["AC"],
        kinds=(DatasetKind.URN_FILES,),
        on_sections=lambda done, total: sections.append((done, total)),
        on_missing=missing.append,
    )
    assert [r.rows for r in reports] == [1]
    assert repository.loaded == [("bu_imgbu_logjez_rdv_vscmr_2026_1t_AC.zip", 2026, 1, "AC")]
    assert sections == [(1, 1)]
    assert missing == ["'urnas' do 2º turno ainda não publicado para: AC"]


def test_import_rejects_unpublished_uf(tmp_path):
    with pytest.raises(InvalidInputError, match="RJ"):
        importer(FakeRepository(), tmp_path).execute(2026, [1], ["RJ"])


def test_get_section_votes_not_found():
    with pytest.raises(SectionVotesNotFound):
        GetSectionVotes(FakeRepository()).execute(2026, 1, "ac", 1066, 4, 77)


def test_aggregate_normalizes_uf():
    repository = FakeRepository()
    AggregateVotes(repository).execute(VoteQuery(2026, 1, 1, uf="sp"))
    AggregateVotes(repository).execute(VoteQuery(2026, 1, 1))
    assert [q.uf for q in repository.queries] == ["SP", None]
    with pytest.raises(InvalidInputError):
        AggregateVotes(repository).execute(VoteQuery(2026, 1, 1, uf="xx"))


def test_new_queries_normalize_filters():
    repository = FakeRepository()
    AggregateTurnout(repository).execute(TurnoutQuery(2026, 1, filters=SectionFilter(uf="sp")))
    AggregateVoteTimeline(repository).execute(TimelineQuery(2026, 1, filters=SectionFilter(uf="ac")))
    EstimateLateVotes(repository).execute(LateVotesQuery(2026, 1, 1, filters=SectionFilter()))
    assert [q.filters.uf for q in repository.queries] == ["SP", "AC", None]


@pytest.mark.parametrize(
    "build",
    [
        lambda: TurnoutQuery(2026, 1, Grouping.VOTABLE),
        lambda: TimelineQuery(2026, 1, interval=20),
        lambda: TimelineQuery(2026, 1, Grouping.SECTION),
        lambda: LateVotesQuery(2026, 1, 1, after="17:10"),
        lambda: LateVotesQuery(2026, 1, 1, grouping=Grouping.ZONE),
        lambda: LateVotesQuery(2026, 1, 1, after="25:00"),
        lambda: TurnoutQuery(2026, 1, limit=0),
    ],
)
def test_query_validation(build):
    with pytest.raises(InvalidInputError):
        build()


def test_minutes_of():
    assert minutes_of("17:00") == 1020
    with pytest.raises(InvalidInputError):
        minutes_of("abc")
