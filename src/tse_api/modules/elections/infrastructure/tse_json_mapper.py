"""Converte os JSONs do portal de resultados do TSE (chaves abreviadas) em objetos de domínio."""

from typing import Any

from ..domain.models import (
    Candidate,
    Catalog,
    Coverage,
    Election,
    ElectionResult,
    ElectorateTotals,
    Municipality,
    Office,
    OfficeResult,
    PartyResult,
    RunningMate,
    ScopeTotals,
    SectionTotals,
    Totals,
    VoteTotals,
    VotingEvent,
)

_OFFICE_KIND = {"1": "majoritario", "2": "proporcional", "3": "consulta"}


def to_float(value: str | None) -> float | None:
    return None if value in (None, "") else float(value.replace(",", "."))


def to_int(value: str | None) -> int | None:
    return None if value in (None, "") else int(value)


def br_date_to_iso(date: str | None, time: str | None = None) -> str | None:
    if not date:
        return None
    day, month, year = date.split("/")
    return f"{year}-{month}-{day}T{time}" if time else f"{year}-{month}-{day}"


def map_catalog(raw: dict[str, Any]) -> Catalog:
    events: dict[int, VotingEvent] = {}
    elections: dict[int, Election] = {}
    for pl in raw.get("pl", []):
        event_code, cycle, date = int(pl["cd"]), pl["c"], br_date_to_iso(pl["dt"]) or ""
        event_elections = tuple(_map_election(e, event_code, cycle, date) for e in pl.get("e", []))
        events[event_code] = VotingEvent(code=event_code, cycle=cycle, date=date, elections=event_elections)
        elections.update({e.code: e for e in event_elections})
    return Catalog(voting_events=events, elections=elections)


def _map_election(raw: dict[str, Any], event_code: int, cycle: str, date: str) -> Election:
    scopes_by_office: dict[int, list[str]] = {}
    office_raw: dict[int, dict[str, Any]] = {}
    for scope in raw.get("abr", []):
        for cp in scope.get("cp", []):
            code = int(cp["cd"])
            office_raw.setdefault(code, cp)
            scopes_by_office.setdefault(code, []).append(scope["cd"])
    offices = tuple(
        Office(
            code=code, name=cp["ds"], kind=_OFFICE_KIND.get(cp["tp"], cp["tp"]), scopes=tuple(scopes_by_office[code])
        )
        for code, cp in office_raw.items()
    )
    return Election(
        code=int(raw["cd"]),
        name=raw["nm"],
        round=int(raw["t"]),
        kind=int(raw["tp"]),
        voting_event_code=event_code,
        cycle=cycle,
        date=date,
        second_round_code=to_int(raw.get("cdt2")),
        offices=offices,
    )


def map_municipalities(raw: dict[str, Any]) -> list[Municipality]:
    return [
        Municipality(
            uf=scope["cd"],
            code=int(m["cd"]),
            ibge_code=to_int(m.get("cdi")),
            name=m["nm"],
            is_capital=m.get("c") == "s",
            zones=tuple(int(z) for z in m.get("z", [])),
        )
        for scope in raw.get("abr", [])
        for m in scope.get("mu", [])
    ]


def map_totals(raw: dict[str, Any]) -> Totals:
    s, e, v = raw.get("s"), raw.get("e"), raw.get("v")
    return Totals(
        sections=SectionTotals(to_int(s.get("ts")), to_int(s.get("st")), to_float(s.get("pstn"))) if s else None,
        electorate=ElectorateTotals(
            to_int(e.get("te")), to_int(e.get("c")), to_int(e.get("a")), to_float(e.get("pcn")), to_float(e.get("pan"))
        )
        if e
        else None,
        votes=VoteTotals(
            total=to_int(v.get("tv")),
            valid=to_int(v.get("vv")),
            nominal=to_int(v.get("vnom")),
            party=to_int(v.get("van")),
            blank=to_int(v.get("vb")),
            null=to_int(v.get("tvn")),
            blank_percent=to_float(v.get("pvbn")),
            null_percent=to_float(v.get("ptvnn")),
        )
        if v
        else None,
    )


def _map_candidate(cand: dict[str, Any], party: dict[str, Any], alliance: dict[str, Any]) -> Candidate:
    return Candidate(
        number=to_int(cand.get("n")),
        name=cand.get("nm"),
        ballot_name=cand.get("nmu"),
        sequential_id=cand.get("sqcand"),
        party=party.get("sg"),
        party_number=to_int(party.get("n")),
        alliance=alliance.get("nm"),
        alliance_parties=alliance.get("com"),
        votes=to_int(cand.get("vap")) or 0,
        percent=to_float(cand.get("pvapn")),
        is_elected=cand.get("e") == "s",
        status=cand.get("st"),
        vote_destination=cand.get("dvt"),
        running_mates=tuple(
            RunningMate(kind=vs.get("tp"), name=vs.get("nm"), ballot_name=vs.get("nmu"), party=vs.get("sgp"))
            for vs in cand.get("vs", [])
        ),
    )


def _map_office_result(raw: dict[str, Any]) -> OfficeResult:
    candidates: list[Candidate] = []
    parties: list[PartyResult] = []
    for alliance in raw.get("agr", []):
        for party in alliance.get("par", []):
            parties.append(
                PartyResult(
                    number=to_int(party.get("n")),
                    acronym=party.get("sg"),
                    name=party.get("nm"),
                    federation=to_int(party.get("nfed")),
                    total_votes=to_int(party.get("tvtn")),
                    party_votes=to_int(party.get("tvtl")),
                    alliance=alliance.get("nm"),
                )
            )
            candidates.extend(_map_candidate(c, party, alliance) for c in party.get("cand", []))
    candidates.sort(key=lambda c: c.votes, reverse=True)
    return OfficeResult(
        code=to_int(raw.get("cd")),
        name=raw.get("nmn"),
        seats=to_int(raw.get("nv")),
        electoral_quotient=to_int(raw.get("qe")),
        candidates=tuple(candidates),
        parties=tuple(parties),
    )


def map_result(raw: dict[str, Any]) -> ElectionResult:
    return ElectionResult(
        election_code=to_int(raw.get("ele")),
        round=to_int(raw.get("t")),
        scope_type=raw.get("tpabr"),
        scope_code=raw.get("cdabr"),
        updated_at=br_date_to_iso(raw.get("dt"), raw.get("ht")),
        is_final=raw.get("tf") == "s",
        totals=map_totals(raw),
        offices=tuple(_map_office_result(c) for c in raw.get("carg", [])),
    )


def map_coverage(raw: dict[str, Any]) -> Coverage:
    return Coverage(
        election_code=to_int(raw.get("ele")),
        round=to_int(raw.get("t")),
        updated_at=br_date_to_iso(raw.get("dg"), raw.get("hg")),
        scopes=tuple(
            ScopeTotals(
                scope_type=a.get("tpabr"),
                scope_code=a.get("cdabr"),
                counted_at=br_date_to_iso(a.get("dt"), a.get("ht")),
                totals=map_totals(a),
            )
            for a in raw.get("abr", [])
        ),
    )
