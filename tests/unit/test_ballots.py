import pytest

from tse_api.modules.ballots.application.download_urn_file import DownloadUrnFile
from tse_api.modules.ballots.application.get_ballot_report import GetBallotReport
from tse_api.modules.ballots.application.list_sections import ListSections
from tse_api.modules.ballots.domain.enrichment import name_votes
from tse_api.modules.ballots.domain.models import (
    BallotReport,
    CandidateNames,
    ElectionVotes,
    OfficeVotes,
    SectionKey,
    SectionNotFound,
    SectionStatus,
    SectionSummary,
    UrnFile,
    UrnFileNotFound,
    UrnFileSet,
    UrnInfo,
    VoteCount,
)
from tse_api.modules.ballots.domain.ports import VotingEventRef
from tse_api.shared.errors import InvalidInputError

pytestmark = pytest.mark.anyio

KEY = SectionKey("ac", 1066, 4, 77)
EVENT = VotingEventRef(3220, "ele2026", {6257: "Federal 1º turno"})
BU = UrnFile("o-bu.dat", "bu", "https://tse/o-bu.dat")


def file_set(hash_: str, status: str, files=(BU,)) -> UrnFileSet:
    return UrnFileSet(hash_, status, None, tuple(files))


def status_with(*sets: UrnFileSet) -> SectionStatus:
    return SectionStatus(3220, KEY, "Totalizada", None, sets)


OFFICE = OfficeVotes(
    code=1,
    identifier="presidente",
    kind="majoritario",
    print_order=1,
    turnout=10,
    votes=(
        VoteCount("nominal", 6, 13, 13),
        VoteCount("nominal", 2, 22, 22),
        VoteCount("branco", 1),
        VoteCount("nulo", 1),
    ),
)
REPORT = BallotReport(
    phase="oficial",
    electoral_id={"tipo": "idPleito", "codigo": 3220},
    generated_at=None,
    issued_at=None,
    section={"municipio": 1066, "zona": 4, "local": 1031, "secao": 77},
    urn=UrnInfo("secao", "votacaoUE", "10", 1, "A", "B", "C", None, {}),
    turnout=10,
    elections=(ElectionVotes(6257, 12, 12, 0, (OFFICE,), "FF"),),
    load_code_history=(),
)
NAMES = CandidateNames("Presidente", {13: ("LULA", "LUIZ INÁCIO LULA DA SILVA")}, {13: "PT", 22: "PL"})


@pytest.mark.parametrize("args", [("ac", 0, 4, 77), ("ac", 1066, 10000, 77), ("ac", 1066, 4, 0)])
def test_section_key_rejects_out_of_range(args):
    with pytest.raises(InvalidInputError):
        SectionKey(*args)


def test_current_file_set_prefers_last_totalized():
    status = status_with(file_set("a", "Totalizado"), file_set("b", "Excluído"))
    assert status.current_file_set().hash == "a"
    status = status_with(file_set("a", "Recebido"), file_set("b", "Recebido"))
    assert status.current_file_set().hash == "b"


def test_current_file_errors():
    with pytest.raises(SectionNotFound):
        status_with().current_file_set()
    with pytest.raises(UrnFileNotFound, match="disponíveis: bu"):
        status_with(file_set("a", "Totalizado")).current_file("rdv")


def test_office_totals_by_vote_kind():
    assert OFFICE.totals == {"nominal": 8, "legenda": 0, "branco": 1, "nulo": 1}


def test_name_votes_fills_candidate_and_party():
    named = name_votes(OFFICE, NAMES)
    lula, other, blank, _ = named.votes
    assert (named.name, lula.candidate_name, lula.party_acronym) == ("Presidente", "LULA", "PT")
    assert (other.candidate_name, other.party_acronym) == (None, "PL")
    assert blank == OFFICE.votes[2]


class FakeEvents:
    async def get(self, code):
        return EVENT


class FakeSource:
    async def list_sections(self, event, uf):
        return [SectionSummary(SectionKey(uf, 1066, 4, n), "PORTO WALTER", None) for n in (77, 78)] + [
            SectionSummary(SectionKey(uf, 1120, 8, 1), "ACRELÂNDIA", None)
        ]

    async def fetch_section_status(self, event, key):
        return status_with(file_set("a", "Totalizado"))

    async def fetch_file(self, event, key, file_set_, file):
        return b"raw-bu"


class FakeDecoder:
    def decode(self, raw):
        assert raw == b"raw-bu"
        return REPORT


class FakeDirectory:
    def __init__(self):
        self.calls = []

    async def lookup(self, election_code, uf, municipality, office_code):
        self.calls.append((election_code, uf, municipality, office_code))
        return NAMES


async def test_list_sections_filters_and_paginates():
    use_case = ListSections(FakeEvents(), FakeSource())
    page = await use_case.execute(3220, "AC", municipality=1066, limit=1)
    assert (page.total, [s.key.section for s in page.items]) == (2, [77])
    page = await use_case.execute(3220, "AC", municipality=1066, limit=1, cursor=page.next_cursor)
    assert [s.key.section for s in page.items] == [78] and page.next_cursor is None
    assert (await use_case.execute(3220, "ac", zone=8)).total == 1


async def test_get_ballot_report_names_votes():
    directory = FakeDirectory()
    use_case = GetBallotReport(FakeEvents(), DownloadUrnFile(FakeEvents(), FakeSource()), FakeDecoder(), directory)
    report = await use_case.execute(3220, "AC", 1066, 4, 77)
    assert (report.file_name, report.uf) == ("o-bu.dat", "ac")
    assert report.elections[0].name == "Federal 1º turno"
    assert report.elections[0].offices[0].votes[0].candidate_name == "LULA"
    assert directory.calls == [(6257, "ac", 1066, 1)]


async def test_get_ballot_report_without_names_skips_lookup():
    directory = FakeDirectory()
    use_case = GetBallotReport(FakeEvents(), DownloadUrnFile(FakeEvents(), FakeSource()), FakeDecoder(), directory)
    report = await use_case.execute(3220, "ac", 1066, 4, 77, with_names=False)
    assert report.elections[0].name is None and directory.calls == []
