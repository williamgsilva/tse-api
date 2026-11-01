from ....shared.schema import ApiSchema, pt


class OfficeOut(ApiSchema):
    code: int = pt("codigo")
    name: str = pt("nome")
    kind: str = pt("tipo", description="majoritario | proporcional | consulta")
    scopes: list[str] = pt("abrangencias")


class ElectionOut(ApiSchema):
    code: int = pt("codigo")
    name: str = pt("nome")
    round: int = pt("turno")
    kind: int = pt("tipo")
    voting_event_code: int = pt("pleito")
    cycle: str = pt("ciclo")
    year: int = pt("ano")
    date: str = pt("data")
    second_round_code: int | None = pt("codigo_segundo_turno")
    offices: list[OfficeOut] = pt("cargos")


class VotingEventOut(ApiSchema):
    code: int = pt("pleito")
    cycle: str = pt("ciclo")
    year: int = pt("ano")
    date: str = pt("data")
    elections: list[ElectionOut] = pt("eleicoes")


class MunicipalityOut(ApiSchema):
    uf: str = pt("uf")
    code: int = pt("codigo", description="código TSE do município")
    ibge_code: int | None = pt("codigo_ibge")
    name: str = pt("nome")
    is_capital: bool = pt("capital")
    zones: list[int] = pt("zonas")


class SectionTotalsOut(ApiSchema):
    total: int | None = pt("total")
    counted: int | None = pt("totalizadas")
    counted_percent: float | None = pt("percentual_totalizadas")


class ElectorateTotalsOut(ApiSchema):
    total: int | None = pt("total")
    turnout: int | None = pt("comparecimento")
    abstention: int | None = pt("abstencao")
    turnout_percent: float | None = pt("percentual_comparecimento")
    abstention_percent: float | None = pt("percentual_abstencao")


class VoteTotalsOut(ApiSchema):
    total: int | None = pt("total")
    valid: int | None = pt("validos")
    nominal: int | None = pt("nominais")
    party: int | None = pt("legenda")
    blank: int | None = pt("brancos")
    null: int | None = pt("nulos")
    blank_percent: float | None = pt("percentual_brancos")
    null_percent: float | None = pt("percentual_nulos")


class TotalsOut(ApiSchema):
    sections: SectionTotalsOut | None = pt("secoes", None)
    electorate: ElectorateTotalsOut | None = pt("eleitorado", None)
    votes: VoteTotalsOut | None = pt("votos", None)


class RunningMateOut(ApiSchema):
    kind: str | None = pt("tipo")
    name: str | None = pt("nome")
    ballot_name: str | None = pt("nome_urna")
    party: str | None = pt("partido")


class CandidateOut(ApiSchema):
    number: int | None = pt("numero")
    name: str | None = pt("nome")
    ballot_name: str | None = pt("nome_urna")
    sequential_id: str | None = pt("sequencial")
    party: str | None = pt("partido")
    party_number: int | None = pt("numero_partido")
    alliance: str | None = pt("agremiacao")
    alliance_parties: str | None = pt("composicao")
    votes: int = pt("votos")
    percent: float | None = pt("percentual")
    is_elected: bool = pt("eleito")
    status: str | None = pt("situacao")
    vote_destination: str | None = pt("destinacao_votos")
    running_mates: list[RunningMateOut] = pt("vices_suplentes")


class PartyResultOut(ApiSchema):
    number: int | None = pt("numero")
    acronym: str | None = pt("sigla")
    name: str | None = pt("nome")
    federation: int | None = pt("federacao")
    total_votes: int | None = pt("votos_total")
    party_votes: int | None = pt("votos_legenda")
    alliance: str | None = pt("agremiacao")


class OfficeResultOut(ApiSchema):
    code: int | None = pt("codigo")
    name: str | None = pt("nome")
    seats: int | None = pt("vagas")
    electoral_quotient: int | None = pt("quociente_eleitoral")
    candidates: list[CandidateOut] = pt("candidatos")
    parties: list[PartyResultOut] = pt("partidos")


class ElectionResultOut(ApiSchema):
    election_code: int | None = pt("eleicao")
    round: int | None = pt("turno")
    scope_type: str | None = pt("tipo_abrangencia", description="br | uf | mu")
    scope_code: str | None = pt("codigo_abrangencia")
    updated_at: str | None = pt("atualizado_em")
    is_final: bool = pt("totalizacao_finalizada")
    totals: TotalsOut = pt("totais")
    offices: list[OfficeResultOut] = pt("cargos")


class ScopeTotalsOut(ApiSchema):
    scope_type: str | None = pt("tipo_abrangencia")
    scope_code: str | None = pt("codigo_abrangencia")
    counted_at: str | None = pt("totalizado_em")
    totals: TotalsOut = pt("totais")


class CoverageOut(ApiSchema):
    election_code: int | None = pt("eleicao")
    round: int | None = pt("turno")
    updated_at: str | None = pt("atualizado_em")
    scopes: list[ScopeTotalsOut] = pt("abrangencias")


class SubdivisionCandidateOut(ApiSchema):
    number: int | None = pt("numero")
    ballot_name: str | None = pt("nome_urna")
    party: str | None = pt("partido")
    votes: int = pt("votos")
    percent: float | None = pt("percentual")
    is_elected: bool = pt("eleito")
    status: str | None = pt("situacao")


class SubdivisionResultOut(ApiSchema):
    scope_type: str = pt("tipo_abrangencia", description="uf | mu")
    code: str = pt("codigo", description="sigla da UF ou código TSE do município")
    ibge_code: int | None = pt("codigo_ibge")
    name: str = pt("nome")
    is_final: bool = pt("totalizacao_finalizada")
    totals: TotalsOut = pt("totais")
    candidates: list[SubdivisionCandidateOut] = pt("candidatos")
