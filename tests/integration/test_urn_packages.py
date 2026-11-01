"""Leitura do log e do pacote de urnas (arquivos reais do TSE) e consultas sobre a base com esses dados."""

import zipfile
from datetime import date

import pytest

from tests.conftest import BU_FILE, FIXTURES, LOG_FILE, URN_RECORD, load_sample_database
from tse_api.modules.ballots import InvalidBallotReport, JezUrnLogReader
from tse_api.modules.open_data.domain.models import (
    Grouping,
    LateVotesQuery,
    SectionFilter,
    TimelineQuery,
    TurnoutQuery,
)
from tse_api.modules.open_data.infrastructure.zip_urn_package_reader import ZipUrnPackageReader, section_tasks


def test_log_reader_counts_match_ballot_report():
    events = JezUrnLogReader().read_votes((FIXTURES / LOG_FILE).read_bytes(), date(2026, 10, 4))
    kinds = {kind: sum(1 for e in events if e.enablement == kind) for kind in {e.enablement for e in events}}
    # BU da seção: comparecimento 234 = 212 biometria + 13 ano de nascimento + 9 sem biometria
    assert len(events) == 234
    assert kinds == {"biometria": 212, "ano_nascimento": 13, "sem_biometria": 9}
    assert events[0].at.isoformat() == "2026-10-04T06:09:09"
    assert JezUrnLogReader().read_votes((FIXTURES / LOG_FILE).read_bytes(), date(2026, 10, 5)) == []


def test_log_reader_rejects_invalid_archive():
    with pytest.raises(InvalidBallotReport):
        JezUrnLogReader().read_votes(b"nao e zip", date(2026, 10, 4))


@pytest.fixture
def package(tmp_path):
    path = tmp_path / "bu_imgbu_logjez_rdv_vscmr_2026_1t_AC.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("leiame.pdf", b"%PDF")
        archive.write(FIXTURES / BU_FILE, BU_FILE)
        archive.write(FIXTURES / LOG_FILE, LOG_FILE)
        archive.writestr("o03220ac0106600040078-bu.dat", b"corrompido")
        archive.writestr("o03220ac0106600040079-log.jez", b"log sem BU")
    return path


def test_section_tasks_pairs_files():
    names = [BU_FILE, LOG_FILE, "o03220ac0106600040078-bu.dat", "o03220ac0106600040079-log.jez", "leiame.pdf"]
    assert sorted(section_tasks(names)) == [(BU_FILE, LOG_FILE), ("o03220ac0106600040078-bu.dat", None)]


@pytest.mark.parametrize("processes", [1, 2])
def test_package_reader_decodes_sections_and_skips_corrupted(package, processes):
    progress = []
    records = list(ZipUrnPackageReader(processes).read(package, lambda done, total: progress.append((done, total))))
    assert progress[-1] == (2, 2)
    [record] = records
    assert (record.uf, record.municipality, record.zone, record.section) == ("AC", 1066, 4, 77)
    assert (record.turnout, record.log_votes, record.enabled_by_biometrics) == (234, 234, 212)
    assert sum(sum(k.values()) for k in record.votes_by_quarter_hour.values()) == 234
    assert all(minute % 15 == 0 for minute in record.votes_by_quarter_hour)


@pytest.fixture
def repository(settings):
    return load_sample_database(settings)


def test_turnout_combines_csv_and_urn_files(repository):
    [total] = repository.turnout(TurnoutQuery(2026, 1))
    assert total.sections == 181
    assert total.sections_with_urn_files == 1
    assert total.enabled_by_biometrics == 140 and total.without_biometrics == 41
    [section] = repository.turnout(
        TurnoutQuery(2026, 1, Grouping.SECTION, SectionFilter(uf="AC", municipality=1074, zone=4, section=175))
    )
    assert (section.eligible_voters, section.turnout, section.abstentions) == (256, 191, 65)
    assert section.group == {
        "uf": "AC",
        "municipio": 1074,
        "nome_municipio": "CRUZEIRO DO SUL",
        "zona": 4,
        "secao": 175,
    }
    # Fuso deduzido da abertura (6h locais = 8h de Brasília): encerramento 15:20 local = 17:20 Brasília
    assert section.last_closing == "2026-10-04T17:20:00"
    closed_late = repository.turnout(TurnoutQuery(2026, 1, filters=SectionFilter(uf="AC"), closed_after="17:15"))
    assert closed_late[0].sections >= 1


def test_timeline_in_brasilia_time(repository):
    points = repository.timeline(TimelineQuery(2026, 1, filters=SectionFilter(uf="AC"), interval=60))
    assert [(p.start, p.votes) for p in points] == [("08:00", 100), ("17:00", 91)]
    assert points[1].by_enablement == {"biometria": 40, "sem_biometria": 41, "ano_nascimento": 10}


def test_late_votes_estimate_is_proportional(repository):
    report = repository.late_votes(LateVotesQuery(2026, 1, 7, after="17:00"))
    assert (report.summary.sections, report.summary.late_votes, report.summary.turnout) == (1, 91, 191)
    total_votes = sum(v.section_votes for v in report.votables)
    estimated = sum(v.estimated_late_votes for v in report.votables)
    assert estimated == pytest.approx(total_votes * 91 / 191, abs=0.05)
    by_municipality = repository.late_votes(LateVotesQuery(2026, 1, 7, grouping=Grouping.MUNICIPALITY))
    assert by_municipality.votables[0].group["nome_municipio"] == "CRUZEIRO DO SUL"


def test_imported_lists_both_sources(repository):
    kinds = {(d.kind.value, d.sections) for d in repository.imported()}
    assert kinds == {("boletins", 181), ("urnas", 1)}
    assert URN_RECORD.turnout == 191
