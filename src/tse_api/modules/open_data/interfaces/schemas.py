from ....shared.schema import ApiSchema, pt


class ImportedDatasetOut(ApiSchema):
    kind: str = pt("tipo", description="boletins (CSV) | urnas (pacote de BU e log)")
    year: int = pt("ano")
    round: int = pt("turno")
    uf: str = pt("uf")
    source_file: str = pt("arquivo")
    rows: int = pt("linhas")
    sections: int = pt("secoes")


class SectionVoteOut(ApiSchema):
    kind: str | None = pt("tipo")
    number: int | None = pt("numero")
    name: str | None = pt("nome")
    party: str | None = pt("partido")
    quantity: int = pt("quantidade")


class SectionOfficeVotesOut(ApiSchema):
    election_code: int = pt("eleicao")
    election_name: str | None = pt("nome_eleicao")
    office_code: int = pt("codigo")
    office_name: str | None = pt("cargo")
    eligible_voters: int | None = pt("aptos")
    turnout: int | None = pt("comparecimento")
    abstentions: int | None = pt("abstencoes")
    votes: list[SectionVoteOut] = pt("votos")


class SectionUrnOut(ApiSchema):
    kind: str | None = pt("tipo")
    number: int | None = pt("numero")
    load_code_1: str | None = pt("codigo_carga_1")
    load_code_2: str | None = pt("codigo_carga_2")
    flash_card: str | None = pt("flashcard")
    loaded_at: str | None = pt("data_carga")


class SectionVotesReportOut(ApiSchema):
    year: int = pt("ano")
    round: int = pt("turno")
    voting_event_code: int | None = pt("pleito")
    uf: str = pt("uf")
    municipality: int = pt("municipio")
    municipality_name: str | None = pt("nome_municipio")
    zone: int = pt("zona")
    section: int = pt("secao")
    polling_place: int | None = pt("local_votacao")
    aggregated_sections: str | None = pt("secoes_agregadas")
    urn: SectionUrnOut = pt("urna")
    opened_at: str | None = pt("abertura")
    closed_at: str | None = pt("encerramento")
    issued_at: str | None = pt("emissao_bu")
    received_at: str | None = pt("recebido_em")
    biometric_not_enabled: int | None = pt("eleitores_biometria_sem_habilitacao")
    offices: list[SectionOfficeVotesOut] = pt("cargos")
    source_file: str | None = pt("arquivo_origem")


class VoteAggregateOut(ApiSchema):
    uf: str | None = pt("uf", None)
    municipality: int | None = pt("municipio", None)
    municipality_name: str | None = pt("nome_municipio", None)
    zone: int | None = pt("zona", None)
    polling_place: int | None = pt("local", None)
    section: int | None = pt("secao", None)
    votable_kind: str | None = pt("tipo")
    votable_number: int | None = pt("numero")
    votable_name: str | None = pt("nome")
    party: str | None = pt("partido")
    votes: int = pt("votos")


class TurnoutAggregateOut(ApiSchema):
    group: dict[str, object] = pt("grupo")
    sections: int = pt("secoes")
    eligible_voters: int = pt("aptos")
    turnout: int = pt("comparecimento")
    abstentions: int = pt("abstencoes")
    turnout_percent: float | None = pt("percentual_comparecimento")
    enabled_by_biometrics: int | None = pt(
        "habilitados_biometria", description="só nas seções com pacote de urnas importado"
    )
    enabled_by_birth_year: int | None = pt(
        "habilitados_ano_nascimento", description="tinham biometria, mas foram habilitados pelo ano de nascimento"
    )
    without_biometrics: int | None = pt("sem_biometria", description="só nas seções com pacote de urnas importado")
    sections_with_urn_files: int = pt("secoes_com_arquivos_urna")
    first_opening: str | None = pt("primeira_abertura", description="primeiro voto, horário de Brasília")
    last_closing: str | None = pt("ultimo_encerramento", description="último voto, horário de Brasília")


class TimelinePointOut(ApiSchema):
    group: dict[str, object] = pt("grupo")
    start: str = pt("inicio", description="início do intervalo, horário de Brasília (HH:MM)")
    votes: int = pt("votos")
    by_enablement: dict[str, int] = pt("por_habilitacao")


class LateVotesSummaryOut(ApiSchema):
    sections: int = pt("secoes")
    turnout: int = pt("comparecimento")
    late_votes: int = pt("votos_apos", description="exato, contado no log das urnas")
    sections_without_timezone: int = pt("secoes_sem_fuso", description="exterior: horário local, fora da conta")


class LateVoteAggregateOut(ApiSchema):
    group: dict[str, object] = pt("grupo")
    votable_kind: str | None = pt("tipo")
    votable_number: int | None = pt("numero")
    votable_name: str | None = pt("nome")
    party: str | None = pt("partido")
    section_votes: int = pt("votos_nas_secoes")
    estimated_late_votes: float = pt("votos_apos_estimados")


class LateVotesReportOut(ApiSchema):
    after: str = pt("apos")
    method: str = pt("metodo")
    summary: LateVotesSummaryOut = pt("resumo")
    votables: list[LateVoteAggregateOut] = pt("votaveis")
