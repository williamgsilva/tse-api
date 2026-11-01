"""Repositório DuckDB dos boletins de urna (CSV ``bweb`` e pacotes de arquivos de urna). Ver ADR 0004.

``votos_secao`` tem uma linha por votável, cargo e seção (CSV). ``urnas_secao`` e ``votos_horario``
vêm do BU e do log de cada urna. Toda consulta é parametrizada; só nomes de colunas fixos entram no SQL.
"""

import csv
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import duckdb

from ..domain.models import (
    DatasetKind,
    ImportedDataset,
    LateVoteAggregate,
    LateVotesQuery,
    LateVotesReport,
    LateVotesSummary,
    LocalDatabaseUnavailable,
    SectionOfficeVotes,
    SectionUrn,
    SectionUrnRecord,
    SectionVote,
    SectionVotesReport,
    TimelinePoint,
    TimelineQuery,
    TurnoutAggregate,
    TurnoutQuery,
    VoteAggregate,
    VoteQuery,
    minutes_of,
)
from ..domain.ports import VoteRepository
from .duckdb_schema import (
    CSV_SECTIONS,
    CSV_SECTIONS_FROM_VOTES,
    DDL,
    GROUP_COLUMNS,
    GROUP_KEYS,
    MUNICIPAL_OFFSET_CTE,
    MUNICIPALITY_NAMES_CTE,
    SECTION_KEY,
    SECTIONS_CTE,
    TIMELINE,
    URN_SECTIONS,
    VOTES,
    offset_expr,
    qualified,
    section_filters,
)

EMPTY = "base local vazia: importe os dados com `make ingest`"
NO_URN_FILES = 'nenhum pacote de arquivos de urna importado: use `make ingest ARGS="--fonte urnas ..."`'

_AGGREGATE_FIELDS = {
    "uf": "uf",
    "cd_municipio": "municipality",
    "nm_municipio": "municipality_name",
    "nr_zona": "zone",
    "nr_local_votacao": "polling_place",
    "nr_secao": "section",
}


def _value(col: str) -> str:
    return f"NULLIF(NULLIF({col}, '#NULO#'), '#NE#')"


def _int(col: str) -> str:
    return f"TRY_CAST({_value(col)} AS INTEGER)"


def _timestamp(col: str) -> str:
    return f"TRY_CAST({_value(col)} AS TIMESTAMP)"


_SELECT_FROM_CSV = f"""
SELECT {_int("ano_eleicao")}, {_int("cd_pleito")}, {_int("nr_turno")}, {_int("cd_eleicao")}, ds_eleicao,
       sg_uf, {_int("cd_municipio")}, nm_municipio, {_int("nr_zona")}, {_int("nr_secao")},
       {_int("nr_local_votacao")}, {_int("cd_cargo_pergunta")}, ds_cargo_pergunta,
       {_int("nr_partido")}, {_value("sg_partido")}, {_value("nm_partido")},
       {_int("qt_aptos")}, {_int("qt_comparecimento")}, {_int("qt_abstencoes")},
       {_int("cd_tipo_urna")}, ds_tipo_urna,
       {_int("cd_tipo_votavel")}, ds_tipo_votavel, {_int("nr_votavel")}, nm_votavel, {_int("qt_votos")},
       {_int("nr_urna_efetivada")}, {_value("cd_carga_1_urna_efetivada")}, {_value("cd_carga_2_urna_efetivada")},
       {_value("cd_flashcard_urna_efetivada")}, {_timestamp("dt_carga_urna_efetivada")},
       {_value("ds_secoes_agregadas")}, {_timestamp("dt_abertura")}, {_timestamp("dt_encerramento")},
       {_int("qt_elei_biom_sem_habilitacao")}, {_timestamp("dt_emissao_bu")}, {_timestamp("dt_bu_recebido")},
       $source
FROM read_csv($path, delim=';', quote='"', header=true, encoding='latin-1', all_varchar=true, normalize_names=true)
"""

_URN_SECTION_COLUMNS = [
    "ano", "turno", "uf", "cd_municipio", "nr_zona", "nr_secao", "nr_local_votacao", "tipo_urna", "nr_urna",
    "versao_votacao", "dt_abertura", "dt_encerramento", "dt_emissao", "qt_aptos", "qt_aptos_secao",
    "qt_aptos_transito", "qt_comparecimento", "qt_sem_biometria", "qt_habilitados_biometria",
    "qt_habilitados_ano_nascimento", "qt_votos_log", "arquivo_origem",
]  # fmt: skip
_TIMELINE_COLUMNS = [*SECTION_KEY, "minuto_local", "habilitacao", "qt_votos"]


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def _clock(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _group(row: dict[str, Any], columns: list[str]) -> dict[str, object]:
    return {GROUP_KEYS[c]: row[c] for c in columns}


class DuckDbVoteRepository(VoteRepository):
    def __init__(self, database_path: Path, read_only: bool):
        self._path = database_path
        self._read_only = read_only

    @contextmanager
    def _connect(self) -> Iterator[duckdb.DuckDBPyConnection]:
        if self._read_only and not self._path.exists():
            raise LocalDatabaseUnavailable(EMPTY)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            connection = duckdb.connect(str(self._path), read_only=self._read_only)
        except duckdb.IOException as exc:
            raise LocalDatabaseUnavailable("base local em uso por uma importação; tente novamente depois") from exc
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _tables(con: duckdb.DuckDBPyConnection) -> set[str]:
        return {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall()}

    def _require(self, con: duckdb.DuckDBPyConnection, *tables: str, message: str = EMPTY) -> None:
        if not set(tables) <= self._tables(con):
            raise LocalDatabaseUnavailable(message)

    def _require_urn_files(self, con: duckdb.DuckDBPyConnection, year: int, round: int) -> None:
        self._require(con, URN_SECTIONS, TIMELINE, message=NO_URN_FILES)
        row = con.execute(f"SELECT count(*) FROM {URN_SECTIONS} WHERE ano = ? AND turno = ?", [year, round]).fetchone()
        if not row or not row[0]:
            raise LocalDatabaseUnavailable(f"{NO_URN_FILES} (ano {year}, {round}º turno)")

    @staticmethod
    def _rows(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
        columns = [d[0] for d in cursor.description or []]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    @staticmethod
    def _ensure_schema(con: duckdb.DuckDBPyConnection) -> None:
        for ddl in DDL:
            con.execute(ddl)

    @contextmanager
    def _transaction(self, con: duckdb.DuckDBPyConnection) -> Iterator[None]:
        con.execute("BEGIN")
        try:
            yield
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise

    # --- Carga ------------------------------------------------------------------------------

    def load(self, csv_path: Path, year: int, round: int, uf: str) -> int:
        scope = [year, round, uf]
        with self._connect() as con:
            self._ensure_schema(con)
            with self._transaction(con):
                con.execute(f"DELETE FROM {VOTES} WHERE ano = ? AND turno = ? AND uf = ?", scope)
                con.execute(f"DELETE FROM {CSV_SECTIONS} WHERE ano = ? AND turno = ? AND uf = ?", scope)
                con.execute(f"INSERT INTO {VOTES} {_SELECT_FROM_CSV}", {"path": str(csv_path), "source": csv_path.name})
                con.execute(CSV_SECTIONS_FROM_VOTES, scope)
                row = con.execute(
                    f"SELECT count(*) FROM {VOTES} WHERE ano = ? AND turno = ? AND uf = ?", scope
                ).fetchone()
            return int(row[0]) if row else 0

    def load_urn_records(self, records: Iterator[SectionUrnRecord], year: int, round: int, uf: str, source: str) -> int:
        # Grava em CSV temporário e carrega com read_csv: ordens de grandeza mais rápido que INSERT linha a linha.
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=self._path.parent) as tmp:
            sections_csv, timeline_csv = Path(tmp) / "secoes.csv", Path(tmp) / "horarios.csv"
            count = _write_urn_csvs(records, year, round, source, sections_csv, timeline_csv)
            scope = [year, round, uf]
            with self._connect() as con:
                self._ensure_schema(con)
                with self._transaction(con):
                    con.execute(f"DELETE FROM {URN_SECTIONS} WHERE ano = ? AND turno = ? AND uf = ?", scope)
                    con.execute(f"DELETE FROM {TIMELINE} WHERE ano = ? AND turno = ? AND uf = ?", scope)
                    for table, path, columns in (
                        (URN_SECTIONS, sections_csv, _URN_SECTION_COLUMNS),
                        (TIMELINE, timeline_csv, _TIMELINE_COLUMNS),
                    ):
                        con.execute(
                            f"INSERT INTO {table} ({', '.join(columns)}) "
                            "SELECT * FROM read_csv($path, header=true, auto_detect=false, columns=$columns)",
                            {"path": str(path), "columns": _csv_columns(con, table, columns)},
                        )
        return count

    # --- Consultas ----------------------------------------------------------------------------

    def imported(self) -> list[ImportedDataset]:
        if self._read_only and not self._path.exists():
            return []
        with self._connect() as con:
            tables = self._tables(con)
            rows = []
            if VOTES in tables:
                rows += self._rows(
                    con.execute(f"""
                        SELECT 'boletins' AS tipo, ano, turno, uf, any_value(arquivo_origem) AS arquivo,
                               count(*) AS linhas, count(DISTINCT (cd_municipio, nr_zona, nr_secao)) AS secoes
                        FROM {VOTES} GROUP BY ALL""")
                )
            if URN_SECTIONS in tables:
                rows += self._rows(
                    con.execute(f"""
                        SELECT 'urnas' AS tipo, ano, turno, uf, any_value(arquivo_origem) AS arquivo,
                               count(*) AS linhas, count(*) AS secoes
                        FROM {URN_SECTIONS} GROUP BY ALL""")
                )
        rows.sort(key=lambda r: (r["ano"], r["turno"], r["uf"], r["tipo"]))
        return [
            ImportedDataset(
                r["ano"], r["turno"], r["uf"], r["arquivo"], r["linhas"], r["secoes"], DatasetKind(r["tipo"])
            )
            for r in rows
        ]

    def section_votes(
        self, year: int, round: int, uf: str, municipality: int, zone: int, section: int
    ) -> SectionVotesReport | None:
        with self._connect() as con:
            if VOTES not in self._tables(con):
                return None
            rows = self._rows(
                con.execute(
                    f"""SELECT * FROM {VOTES}
                        WHERE ano = ? AND turno = ? AND uf = ? AND cd_municipio = ? AND nr_zona = ? AND nr_secao = ?
                        ORDER BY cd_eleicao, cd_cargo, qt_votos DESC""",
                    [year, round, uf, municipality, zone, section],
                )
            )
        return _section_report(year, round, rows) if rows else None

    def aggregate(self, query: VoteQuery) -> list[VoteAggregate]:
        group = GROUP_COLUMNS[query.grouping]
        filters = ["ano = ?", "turno = ?", "cd_cargo = ?"]
        params: list[object] = [query.year, query.round, query.office]
        for column, value in (
            ("uf", query.uf),
            ("cd_municipio", query.municipality),
            ("nr_zona", query.zone),
            ("nr_secao", query.section),
            ("nr_votavel", query.votable),
        ):
            if value is not None:
                filters.append(f"{column} = ?")
                params.append(value)
        if query.urn_type is not None:
            filters.append("lower(ds_tipo_urna) = lower(?)")
            params.append(query.urn_type)
        columns = ", ".join([*group, "ds_tipo_votavel", "nr_votavel", "nm_votavel", "sg_partido"])
        order = ", ".join([*group, "votos DESC", "nr_votavel"])
        sql = f"""
            SELECT {columns}, sum(qt_votos)::BIGINT AS votos FROM {VOTES}
            WHERE {" AND ".join(filters)} GROUP BY {columns} ORDER BY {order} LIMIT ? OFFSET ?
        """
        with self._connect() as con:
            self._require(con, VOTES)
            rows = self._rows(con.execute(sql, [*params, query.limit, query.offset]))
        return [
            VoteAggregate(
                votable_kind=r["ds_tipo_votavel"],
                votable_number=r["nr_votavel"],
                votable_name=r["nm_votavel"],
                party=r["sg_partido"],
                votes=r["votos"],
                **{_AGGREGATE_FIELDS[c]: r[c] for c in group},
            )
            for r in rows
        ]

    def turnout(self, query: TurnoutQuery) -> list[TurnoutAggregate]:
        group = GROUP_COLUMNS[query.grouping]
        where, params = section_filters(query.filters, "s", "tipo_urna")
        offset = offset_expr("s")
        if query.closed_after:
            where.append(f"{offset} IS NOT NULL AND CAST(s.dt_encerramento + to_hours({offset}) AS TIME) >= ?::TIME")
            params.append(query.closed_after)
        select_group = ", ".join(qualified(group, "s"))
        sql = f"""
            WITH {SECTIONS_CTE}, {MUNICIPAL_OFFSET_CTE}
            SELECT {select_group + "," if group else ""}
                   count(*) AS secoes, sum(s.qt_aptos)::BIGINT AS aptos,
                   sum(s.qt_comparecimento)::BIGINT AS comparecimento, sum(s.qt_abstencoes)::BIGINT AS abstencoes,
                   sum(s.qt_habilitados_ano_nascimento)::BIGINT AS ano_nascimento,
                   sum(s.qt_sem_biometria)::BIGINT AS sem_biometria,
                   sum(s.qt_habilitados_biometria)::BIGINT AS biometria,
                   count(*) FILTER (WHERE s.tem_arquivos_urna) AS com_arquivos,
                   min(s.dt_abertura + to_hours(coalesce({offset}, 0))) AS abertura,
                   max(s.dt_encerramento + to_hours(coalesce({offset}, 0))) AS encerramento
            FROM secoes s LEFT JOIN fuso USING (ano, turno, uf, cd_municipio)
            WHERE s.ano = ? AND s.turno = ? {"AND " + " AND ".join(where) if where else ""}
            {"GROUP BY " + select_group + " ORDER BY " + select_group if group else ""}
            LIMIT ? OFFSET ?
        """
        with self._connect() as con:
            self._require(con, CSV_SECTIONS, URN_SECTIONS)
            rows = self._rows(con.execute(sql, [query.year, query.round, *params, query.limit, query.offset]))
        return [
            TurnoutAggregate(
                sections=r["secoes"],
                eligible_voters=r["aptos"] or 0,
                turnout=r["comparecimento"] or 0,
                abstentions=r["abstencoes"] or 0,
                turnout_percent=round(100 * r["comparecimento"] / r["aptos"], 4) if r["aptos"] else None,
                enabled_by_birth_year=r["ano_nascimento"],
                without_biometrics=r["sem_biometria"],
                enabled_by_biometrics=r["biometria"],
                sections_with_urn_files=r["com_arquivos"],
                first_opening=_iso(r["abertura"]),
                last_closing=_iso(r["encerramento"]),
                group=_group(r, group),
            )
            for r in rows
            if r["secoes"]
        ]

    def timeline(self, query: TimelineQuery) -> list[TimelinePoint]:
        group = GROUP_COLUMNS[query.grouping]
        where, params = section_filters(query.filters, "t", None)
        offset = offset_expr("t")
        group_cols = [("n." if c == "nm_municipio" else "t.") + c for c in group]
        select_group = ", ".join(group_cols)
        minute = f"(t.minuto_local + 60 * coalesce({offset}, 0)) // {query.interval} * {query.interval}"
        sql = f"""
            WITH {MUNICIPAL_OFFSET_CTE}, {MUNICIPALITY_NAMES_CTE}
            SELECT {select_group + "," if group else ""} {minute} AS minuto, t.habilitacao,
                   sum(t.qt_votos)::BIGINT AS votos
            FROM {TIMELINE} t
            LEFT JOIN fuso USING (ano, turno, uf, cd_municipio)
            LEFT JOIN nomes n USING (ano, turno, uf, cd_municipio)
            WHERE t.ano = ? AND t.turno = ? {"AND " + " AND ".join(where) if where else ""}
            GROUP BY ALL ORDER BY ALL
        """
        with self._connect() as con:
            self._require_urn_files(con, query.year, query.round)
            self._require(con, CSV_SECTIONS)
            rows = self._rows(con.execute(sql, [query.year, query.round, *params]))
        points: dict[tuple[Any, ...], TimelinePoint] = {}
        for r in rows:
            key = (*(r[c] for c in group), r["minuto"])
            point = points.get(key) or TimelinePoint(_clock(int(r["minuto"]) % 1440), 0, {}, _group(r, group))
            point.by_enablement[r["habilitacao"]] = int(r["votos"])
            points[key] = TimelinePoint(point.start, point.votes + int(r["votos"]), point.by_enablement, point.group)
        return list(points.values())

    def late_votes(self, query: LateVotesQuery) -> LateVotesReport:
        group = GROUP_COLUMNS[query.grouping]
        threshold = minutes_of(query.after)
        where, params = section_filters(query.filters, "u", None)
        offset = offset_expr("u")
        late_cte = f"""tardios AS (
            SELECT {", ".join(qualified(SECTION_KEY, "u"))}, u.qt_comparecimento,
                   {offset} AS horas,
                   coalesce(sum(t.qt_votos) FILTER (WHERE t.minuto_local + 60 * {offset} >= ?), 0) AS votos_tardios
            FROM {URN_SECTIONS} u
            LEFT JOIN fuso USING (ano, turno, uf, cd_municipio)
            LEFT JOIN {TIMELINE} t USING ({", ".join(SECTION_KEY)})
            WHERE u.ano = ? AND u.turno = ? {"AND " + " AND ".join(where) if where else ""}
            GROUP BY ALL
        )"""
        late_params = [threshold, query.year, query.round, *params]
        summary_sql = f"""
            WITH {MUNICIPAL_OFFSET_CTE}, {late_cte}
            SELECT count(*) FILTER (WHERE horas IS NOT NULL) AS secoes,
                   coalesce(sum(qt_comparecimento) FILTER (WHERE horas IS NOT NULL), 0)::BIGINT AS comparecimento,
                   coalesce(sum(votos_tardios), 0)::BIGINT AS tardios,
                   count(*) FILTER (WHERE horas IS NULL) AS sem_fuso
            FROM tardios
        """
        group_cols = [("n." if c == "nm_municipio" else "v.") + c for c in group]
        columns = ", ".join([*group_cols, "v.ds_tipo_votavel", "v.nr_votavel", "v.nm_votavel", "v.sg_partido"])
        votables_sql = f"""
            WITH {MUNICIPAL_OFFSET_CTE}, {late_cte}, {MUNICIPALITY_NAMES_CTE}
            SELECT {columns}, sum(v.qt_votos)::BIGINT AS votos_secoes,
                   sum(v.qt_votos * d.votos_tardios / nullif(d.qt_comparecimento, 0)) AS estimados
            FROM {VOTES} v
            JOIN tardios d USING ({", ".join(SECTION_KEY)})
            LEFT JOIN nomes n USING (ano, turno, uf, cd_municipio)
            WHERE v.cd_cargo = ? AND d.horas IS NOT NULL
            GROUP BY ALL ORDER BY {", ".join([*group_cols, "estimados DESC"])} LIMIT ? OFFSET ?
        """
        with self._connect() as con:
            self._require_urn_files(con, query.year, query.round)
            self._require(con, VOTES, CSV_SECTIONS, message="importe também os CSVs de boletins (votos por candidato)")
            [summary] = self._rows(con.execute(summary_sql, late_params))
            rows = self._rows(con.execute(votables_sql, [*late_params, query.office, query.limit, query.offset]))
        return LateVotesReport(
            after=query.after,
            summary=LateVotesSummary(
                summary["secoes"], summary["comparecimento"], summary["tardios"], summary["sem_fuso"]
            ),
            votables=[
                LateVoteAggregate(
                    votable_kind=r["ds_tipo_votavel"],
                    votable_number=r["nr_votavel"],
                    votable_name=r["nm_votavel"],
                    party=r["sg_partido"],
                    section_votes=r["votos_secoes"],
                    estimated_late_votes=round(float(r["estimados"] or 0), 2),
                    group=_group(r, group),
                )
                for r in rows
            ],
        )


def _csv_columns(con: duckdb.DuckDBPyConnection, table: str, columns: list[str]) -> dict[str, str]:
    types = dict(
        con.execute(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ?", [table]
        ).fetchall()
    )
    return {c: types[c] for c in columns}


def _write_urn_csvs(
    records: Iterator[SectionUrnRecord], year: int, round: int, source: str, sections: Path, timeline: Path
) -> int:
    count = 0
    with sections.open("w", newline="") as s_file, timeline.open("w", newline="") as t_file:
        s_out, t_out = csv.writer(s_file), csv.writer(t_file)
        s_out.writerow(_URN_SECTION_COLUMNS)
        t_out.writerow(_TIMELINE_COLUMNS)
        for r in records:
            key = [year, round, r.uf, r.municipality, r.zone, r.section]
            s_out.writerow([
                *key, r.polling_place, r.urn_kind, r.urn_number, r.software_version,
                r.opened_at, r.closed_at, r.issued_at, r.eligible_voters, r.eligible_in_section,
                r.eligible_in_transit, r.turnout, r.without_biometrics, r.enabled_by_biometrics,
                r.enabled_by_birth_year, r.log_votes, source,
            ])  # fmt: skip
            for minute, kinds in r.votes_by_quarter_hour.items():
                for kind, votes in kinds.items():
                    t_out.writerow([*key, minute, kind, votes])
            count += 1
    return count


def _section_report(year: int, round: int, rows: list[dict[str, Any]]) -> SectionVotesReport:
    first = rows[0]
    offices: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for r in rows:
        offices.setdefault((r["cd_eleicao"], r["cd_cargo"]), []).append(r)
    return SectionVotesReport(
        year=year,
        round=round,
        voting_event_code=first["cd_pleito"],
        uf=first["uf"],
        municipality=first["cd_municipio"],
        municipality_name=first["nm_municipio"],
        zone=first["nr_zona"],
        section=first["nr_secao"],
        polling_place=first["nr_local_votacao"],
        aggregated_sections=first["ds_secoes_agregadas"],
        urn=SectionUrn(
            kind=first["ds_tipo_urna"],
            number=first["nr_urna_efetivada"],
            load_code_1=first["cd_carga_1_urna_efetivada"],
            load_code_2=first["cd_carga_2_urna_efetivada"],
            flash_card=first["cd_flashcard_urna_efetivada"],
            loaded_at=_iso(first["dt_carga_urna_efetivada"]),
        ),
        opened_at=_iso(first["dt_abertura"]),
        closed_at=_iso(first["dt_encerramento"]),
        issued_at=_iso(first["dt_emissao_bu"]),
        received_at=_iso(first["dt_bu_recebido"]),
        biometric_not_enabled=first["qt_elei_biom_sem_habilitacao"],
        offices=tuple(
            SectionOfficeVotes(
                election_code=office_rows[0]["cd_eleicao"],
                election_name=office_rows[0]["ds_eleicao"],
                office_code=office_rows[0]["cd_cargo"],
                office_name=office_rows[0]["ds_cargo"],
                eligible_voters=office_rows[0]["qt_aptos"],
                turnout=office_rows[0]["qt_comparecimento"],
                abstentions=office_rows[0]["qt_abstencoes"],
                votes=tuple(
                    SectionVote(r["ds_tipo_votavel"], r["nr_votavel"], r["nm_votavel"], r["sg_partido"], r["qt_votos"])
                    for r in office_rows
                ),
            )
            for office_rows in offices.values()
        ),
        source_file=first["arquivo_origem"],
    )
