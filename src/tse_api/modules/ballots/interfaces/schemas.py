from typing import Any

from ....shared.schema import ApiSchema, pt


class SectionSummaryOut(ApiSchema):
    uf: str = pt("uf")
    municipality: int = pt("municipio")
    municipality_name: str | None = pt("nome_municipio")
    zone: int = pt("zona")
    section: int = pt("secao")
    updated_at: str | None = pt("atualizado_em")


class SectionPageOut(ApiSchema):
    total: int = pt("total")
    next_cursor: str | None = pt("proximo_cursor")
    items: list[SectionSummaryOut] = pt("secoes")


class UrnFileOut(ApiSchema):
    name: str = pt("nome")
    kind: str = pt("tipo")
    url: str = pt("url_tse")


class UrnFileSetOut(ApiSchema):
    hash: str = pt("hash")
    status: str | None = pt("situacao")
    received_at: str | None = pt("recebido_em")
    is_current: bool = pt("vigente")
    files: list[UrnFileOut] = pt("arquivos")


class SectionStatusOut(ApiSchema):
    voting_event_code: int = pt("pleito")
    uf: str = pt("uf")
    municipality: int = pt("municipio")
    zone: int = pt("zona")
    section: int = pt("secao")
    status: str | None = pt("situacao")
    updated_at: str | None = pt("atualizado_em")
    file_sets: list[UrnFileSetOut] = pt("transmissoes")


class VoteCountOut(ApiSchema):
    kind: str = pt("tipo", description="nominal | legenda | branco | nulo")
    quantity: int = pt("quantidade")
    number: int | None = pt("numero")
    party_number: int | None = pt("partido")
    candidate_name: str | None = pt("nome")
    candidate_full_name: str | None = pt("nome_completo")
    party_acronym: str | None = pt("sigla_partido")


class OfficeVotesOut(ApiSchema):
    code: int = pt("codigo")
    identifier: str = pt("identificador")
    name: str | None = pt("nome")
    kind: str = pt("tipo")
    print_order: int = pt("ordem_impressao")
    turnout: int = pt("comparecimento")
    totals: dict[str, int] = pt("totais")
    votes: list[VoteCountOut] = pt("votos")


class ElectionVotesOut(ApiSchema):
    election_code: int = pt("eleicao")
    name: str | None = pt("nome")
    eligible_voters: int = pt("aptos")
    eligible_in_section: int = pt("aptos_secao")
    eligible_in_transit: int = pt("aptos_transito")
    offices: list[OfficeVotesOut] = pt("cargos")
    last_votes_hash: str = pt("ultimo_hash_votos")


class UrnInfoOut(ApiSchema):
    kind: str = pt("tipo")
    file_kind: str = pt("tipo_arquivo")
    voting_software_version: str = pt("versao_votacao")
    internal_number: int = pt("numero_interno")
    load_flash_serial: str = pt("numero_serie_flash_carga")
    voting_flash_serial: str = pt("numero_serie_flash_votacao")
    load_code: str = pt("codigo_carga")
    loaded_at: str | None = pt("data_hora_carga")
    load_target: dict[str, Any] = pt("identificacao_carga")
    counting_system: dict[str, Any] | None = pt("apuracao_sa")


class BallotReportOut(ApiSchema):
    file_name: str | None = pt("arquivo")
    uf: str | None = pt("uf")
    phase: str = pt("fase")
    electoral_id: dict[str, Any] = pt("id_eleitoral")
    generated_at: str | None = pt("gerado_em")
    issued_at: str | None = pt("emitido_em")
    section: dict[str, int] = pt("secao")
    urn: UrnInfoOut = pt("urna")
    turnout: int = pt("comparecimento")
    voting_window: dict[str, str | None] | None = pt("votacao")
    counting_board: dict[str, Any] | None = pt("sistema_apuracao")
    turnout_breakdown: dict[str, int] | None = pt("detalhamento_comparecimento")
    elections: list[ElectionVotesOut] = pt("eleicoes")
    load_code_history: list[str] = pt("historico_codigos_carga")


class TimelineBucketOut(ApiSchema):
    start: str = pt("inicio", description="início do intervalo de 15 min (HH:MM)")
    votes: int = pt("votos")
    by_enablement: dict[str, int] = pt("por_habilitacao")


class VoteTimelineOut(ApiSchema):
    offset_to_brasilia: int | None = pt(
        "horas_para_brasilia", description="horas somadas ao horário local da urna; nulo = horário local"
    )
    total_votes: int = pt("total_votos")
    first_vote: str | None = pt("primeiro_voto")
    last_vote: str | None = pt("ultimo_voto")
    by_enablement: dict[str, int] = pt("por_habilitacao")
    buckets: list[TimelineBucketOut] = pt("intervalos")


class LateVoteEstimateOut(ApiSchema):
    kind: str = pt("tipo")
    number: int | None = pt("numero")
    name: str | None = pt("nome")
    party: str | None = pt("partido")
    section_votes: int = pt("votos_secao")
    estimated_late_votes: float = pt("votos_tardios_estimados")


class OfficeLateEstimateOut(ApiSchema):
    office_code: int = pt("codigo")
    office_name: str | None = pt("cargo")
    late_votes: int = pt("votos_tardios")
    estimates: list[LateVoteEstimateOut] = pt("estimativas")


class SectionVoteTimelineOut(ApiSchema):
    threshold: str = pt("apos", description="horário de corte (Brasília)")
    votes_after: int = pt("votos_apos")
    turnout: int = pt("comparecimento")
    offset_source: str = pt("fonte_fuso", description="uf = fuso padrão da UF; desconhecido = horário local")
    timeline: VoteTimelineOut = pt("horarios")
    offices: list[OfficeLateEstimateOut] = pt(
        "estimativa_por_cargo",
        description="ESTIMATIVA: distribui os votos tardios na proporção dos votos da seção (o voto é secreto)",
    )
