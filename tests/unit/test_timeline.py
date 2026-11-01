from datetime import datetime, time

import pytest

from tse_api.modules.ballots.domain.models import OfficeVotes, VoteCount
from tse_api.modules.ballots.domain.timeline import (
    BIOMETRICS,
    BIRTH_YEAR,
    NO_BIOMETRICS,
    VoteEvent,
    bucket_start,
    build_timeline,
    count_after,
    default_offset_to_brasilia,
    estimate_late_votes,
    parse_clock,
)
from tse_api.shared.errors import InvalidInputError

# Horário local do Acre (Brasília = local + 2h)
EVENTS = [
    VoteEvent(datetime(2026, 10, 4, 6, 8, 59), BIOMETRICS),
    VoteEvent(datetime(2026, 10, 4, 6, 14, 0), BIRTH_YEAR),
    VoteEvent(datetime(2026, 10, 4, 14, 59, 59), BIOMETRICS),
    VoteEvent(datetime(2026, 10, 4, 15, 0, 0), NO_BIOMETRICS),
    VoteEvent(datetime(2026, 10, 4, 15, 40, 41), BIOMETRICS),
]


def test_default_offsets():
    assert default_offset_to_brasilia("ac") == 2
    assert default_offset_to_brasilia("mt") == 1
    assert default_offset_to_brasilia("sp") == 0
    assert default_offset_to_brasilia("zz") is None


def test_build_timeline_converts_to_brasilia_and_buckets():
    timeline = build_timeline(EVENTS, offset=2)
    assert timeline.total_votes == 5
    assert timeline.first_vote == "2026-10-04T08:08:59"
    assert timeline.last_vote == "2026-10-04T17:40:41"
    assert timeline.by_enablement == {BIOMETRICS: 3, BIRTH_YEAR: 1, NO_BIOMETRICS: 1}
    assert [(b.start, b.votes) for b in timeline.buckets] == [("08:00", 2), ("16:45", 1), ("17:00", 1), ("17:30", 1)]


def test_unknown_timezone_keeps_local_time():
    assert build_timeline(EVENTS[:1], offset=None).first_vote == "2026-10-04T06:08:59"


def test_count_after_threshold_is_inclusive():
    assert count_after(EVENTS, 2, time(17, 0)) == 2
    assert count_after(EVENTS, 0, time(17, 0)) == 0


def test_bucket_and_clock():
    assert bucket_start(datetime(2026, 1, 1, 17, 44), 30) == "17:30"
    assert parse_clock("17:00") == time(17, 0)
    with pytest.raises(InvalidInputError):
        parse_clock("5pm")


def test_estimate_late_votes_is_proportional():
    office = OfficeVotes(
        1, "presidente", "majoritario", 1, 10, (VoteCount("nominal", 2, 13, 13), VoteCount("nominal", 8, 22, 22))
    )
    estimates = estimate_late_votes(office, 5)
    assert [(e.number, e.estimated_late_votes) for e in estimates] == [(22, 4.0), (13, 1.0)]
    assert estimate_late_votes(OfficeVotes(1, "p", "m", 1, 0, ()), 3) == []
