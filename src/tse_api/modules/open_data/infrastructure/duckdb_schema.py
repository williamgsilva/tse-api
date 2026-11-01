"""Tabelas da base local e trechos de SQL reutilizados pelas consultas (ver ADR 0004).

Só nomes de colunas fixos entram no SQL; valores vêm sempre como parâmetros.
"""

from ....shared.uf import ABROAD, STATES
from ...ballots import default_offset_to_brasilia
from ..domain.models import Grouping, SectionFilter

VOTES = "votos_secao"  # CSV bweb: uma linha por votável, cargo e seção
CSV_SECTIONS = "secoes_csv"  # uma linha por seção, derivada do CSV na carga
URN_SECTIONS = "urnas_secao"  # uma linha por seção, do BU do pacote de urnas
TIMELINE = "votos_horario"  # votos por quarto de hora (horário local) e habilitação, do log da urna

SECTION_KEY = ["ano", "turno", "uf", "cd_municipio", "nr_zona", "nr_secao"]
_KEY = ", ".join(SECTION_KEY)

DDL = [
    f"""CREATE TABLE IF NOT EXISTS {VOTES} (
        ano INTEGER, cd_pleito INTEGER, turno INTEGER, cd_eleicao INTEGER, ds_eleicao VARCHAR,
        uf VARCHAR, cd_municipio INTEGER, nm_municipio VARCHAR, nr_zona INTEGER, nr_secao INTEGER,
        nr_local_votacao INTEGER, cd_cargo INTEGER, ds_cargo VARCHAR,
        nr_partido INTEGER, sg_partido VARCHAR, nm_partido VARCHAR,
        qt_aptos INTEGER, qt_comparecimento INTEGER, qt_abstencoes INTEGER,
        cd_tipo_urna INTEGER, ds_tipo_urna VARCHAR,
        cd_tipo_votavel INTEGER, ds_tipo_votavel VARCHAR, nr_votavel INTEGER, nm_votavel VARCHAR, qt_votos INTEGER,
        nr_urna_efetivada INTEGER, cd_carga_1_urna_efetivada VARCHAR, cd_carga_2_urna_efetivada VARCHAR,
        cd_flashcard_urna_efetivada VARCHAR, dt_carga_urna_efetivada TIMESTAMP, ds_secoes_agregadas VARCHAR,
        dt_abertura TIMESTAMP, dt_encerramento TIMESTAMP, qt_elei_biom_sem_habilitacao INTEGER,
        dt_emissao_bu TIMESTAMP, dt_bu_recebido TIMESTAMP, arquivo_origem VARCHAR
    )""",
    f"""CREATE TABLE IF NOT EXISTS {CSV_SECTIONS} (
        ano INTEGER, turno INTEGER, uf VARCHAR, cd_municipio INTEGER, nm_municipio VARCHAR,
        nr_zona INTEGER, nr_secao INTEGER, nr_local_votacao INTEGER, ds_tipo_urna VARCHAR,
        qt_aptos INTEGER, qt_comparecimento INTEGER, qt_abstencoes INTEGER, qt_habilitados_ano_nascimento INTEGER,
        dt_abertura TIMESTAMP, dt_encerramento TIMESTAMP
    )""",
    f"""CREATE TABLE IF NOT EXISTS {URN_SECTIONS} (
        ano INTEGER, turno INTEGER, uf VARCHAR, cd_municipio INTEGER, nr_zona INTEGER, nr_secao INTEGER,
        nr_local_votacao INTEGER, tipo_urna VARCHAR, nr_urna INTEGER, versao_votacao VARCHAR,
        dt_abertura TIMESTAMP, dt_encerramento TIMESTAMP, dt_emissao TIMESTAMP,
        qt_aptos INTEGER, qt_aptos_secao INTEGER, qt_aptos_transito INTEGER, qt_comparecimento INTEGER,
        qt_sem_biometria INTEGER, qt_habilitados_biometria INTEGER, qt_habilitados_ano_nascimento INTEGER,
        qt_votos_log INTEGER, arquivo_origem VARCHAR
    )""",
    f"""CREATE TABLE IF NOT EXISTS {TIMELINE} (
        ano INTEGER, turno INTEGER, uf VARCHAR, cd_municipio INTEGER, nr_zona INTEGER, nr_secao INTEGER,
        minuto_local SMALLINT, habilitacao VARCHAR, qt_votos INTEGER
    )""",
    f"CREATE INDEX IF NOT EXISTS idx_{VOTES}_secao ON {VOTES}({_KEY})",
]

CSV_SECTIONS_FROM_VOTES = f"""
INSERT INTO {CSV_SECTIONS}
SELECT ano, turno, uf, cd_municipio, any_value(nm_municipio), nr_zona, nr_secao, any_value(nr_local_votacao),
       any_value(ds_tipo_urna), max(qt_aptos), max(qt_comparecimento), max(qt_abstencoes),
       max(qt_elei_biom_sem_habilitacao), min(dt_abertura), max(dt_encerramento)
FROM {VOTES} WHERE ano = ? AND turno = ? AND uf = ?
GROUP BY ano, turno, uf, cd_municipio, nr_zona, nr_secao
"""

# Fuso padrão de cada UF (horas a somar ao horário local para obter o de Brasília). NULL = exterior.
_UF_DEFAULT = (
    "CASE {uf} "
    + " ".join(f"WHEN '{uf.upper()}' THEN {default_offset_to_brasilia(uf)}" for uf in sorted(STATES))
    + f" WHEN '{ABROAD.upper()}' THEN NULL ELSE 0 END"
)

# Fuso de cada município deduzido da mediana do primeiro voto: a votação começa às 8h de Brasília em
# todo o país, então abrir às 6h locais indica +2h (Acre e oeste do Amazonas), 9h locais indica −1h
# (Fernando de Noronha). No exterior o horário é local e o fuso fica desconhecido.
MUNICIPAL_OFFSET_CTE = f"""fuso AS (
    SELECT ano, turno, uf, cd_municipio,
           CASE WHEN uf = '{ABROAD.upper()}' THEN NULL ELSE least(2, greatest(-1, CAST(round(
               (480 - median(extract(hour FROM dt_abertura) * 60 + extract(minute FROM dt_abertura))) / 60.0
           ) AS INTEGER))) END AS horas
    FROM {URN_SECTIONS} WHERE dt_abertura IS NOT NULL
    GROUP BY ano, turno, uf, cd_municipio
)"""


def offset_expr(alias: str, offset_alias: str = "fuso") -> str:
    """Horas até Brasília: fuso deduzido do município ou, sem pacote de urnas, o padrão da UF."""
    default = _UF_DEFAULT.format(uf=f"{alias}.uf")
    return f"CASE WHEN {alias}.uf = '{ABROAD.upper()}' THEN NULL ELSE coalesce({offset_alias}.horas, {default}) END"


# Seções com tudo o que se sabe delas: CSV (aptos, comparecimento, nome do município) e pacote de urnas
# (biometria detalhada). Os dois são somados quando só um deles foi importado para a UF.
SECTIONS_CTE = f"""secoes AS (
    SELECT {_KEY}, c.nm_municipio,
           coalesce(u.nr_local_votacao, c.nr_local_votacao) AS nr_local_votacao,
           coalesce(c.ds_tipo_urna, u.tipo_urna) AS tipo_urna,
           coalesce(u.qt_aptos, c.qt_aptos) AS qt_aptos,
           coalesce(u.qt_comparecimento, c.qt_comparecimento) AS qt_comparecimento,
           coalesce(u.qt_aptos - u.qt_comparecimento, c.qt_abstencoes) AS qt_abstencoes,
           coalesce(u.qt_habilitados_ano_nascimento, c.qt_habilitados_ano_nascimento) AS qt_habilitados_ano_nascimento,
           u.qt_sem_biometria, u.qt_habilitados_biometria,
           coalesce(u.dt_abertura, c.dt_abertura) AS dt_abertura,
           coalesce(u.dt_encerramento, c.dt_encerramento) AS dt_encerramento,
           u.nr_secao IS NOT NULL AS tem_arquivos_urna
    FROM {CSV_SECTIONS} c FULL OUTER JOIN {URN_SECTIONS} u USING ({_KEY})
)"""

MUNICIPALITY_NAMES_CTE = f"""nomes AS (
    SELECT ano, turno, uf, cd_municipio, any_value(nm_municipio) AS nm_municipio
    FROM {CSV_SECTIONS} GROUP BY ano, turno, uf, cd_municipio
)"""

GROUP_COLUMNS: dict[Grouping, list[str]] = {
    Grouping.TOTAL: [],
    Grouping.VOTABLE: [],
    Grouping.UF: ["uf"],
    Grouping.MUNICIPALITY: ["uf", "cd_municipio", "nm_municipio"],
    Grouping.ZONE: ["uf", "cd_municipio", "nm_municipio", "nr_zona"],
    Grouping.POLLING_PLACE: ["uf", "cd_municipio", "nm_municipio", "nr_zona", "nr_local_votacao"],
    Grouping.SECTION: ["uf", "cd_municipio", "nm_municipio", "nr_zona", "nr_secao"],
}

# Coluna SQL → chave do grupo na resposta (JSON em português, ADR 0003).
GROUP_KEYS = {
    "uf": "uf",
    "cd_municipio": "municipio",
    "nm_municipio": "nome_municipio",
    "nr_zona": "zona",
    "nr_local_votacao": "local",
    "nr_secao": "secao",
}


def section_filters(filters: SectionFilter, alias: str, urn_type_column: str | None) -> tuple[list[str], list[object]]:
    clauses: list[str] = []
    params: list[object] = []
    for column, value in (
        ("uf", filters.uf),
        ("cd_municipio", filters.municipality),
        ("nr_zona", filters.zone),
        ("nr_secao", filters.section),
    ):
        if value is not None:
            clauses.append(f"{alias}.{column} = ?")
            params.append(value)
    if filters.urn_type is not None and urn_type_column:
        clauses.append(f"lower({alias}.{urn_type_column}) = lower(?)")
        params.append(filters.urn_type)
    return clauses, params


def qualified(columns: list[str], alias: str) -> list[str]:
    return [f"{alias}.{c}" for c in columns]
