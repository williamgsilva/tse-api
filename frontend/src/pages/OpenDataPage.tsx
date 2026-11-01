import { useState, type FormEvent } from "react";

import { ApiError } from "../api/client";
import { useAggregate, useImports, type AggregateParams } from "../api/hooks";
import type { Grouping, VoteAggregate } from "../api/types";
import { SelectField, TextField } from "../components/Field";
import { Empty, ErrorMessage, Loading } from "../components/Status";
import { formatInt, pad } from "../lib/format";
import { UFS } from "../lib/ufs";

const OFFICES = [
  { value: 1, label: "Presidente" },
  { value: 3, label: "Governador" },
  { value: 5, label: "Senador" },
  { value: 6, label: "Deputado Federal" },
  { value: 7, label: "Deputado Estadual" },
  { value: 8, label: "Deputado Distrital" },
];

const GROUPINGS: { value: Grouping; label: string }[] = [
  { value: "votavel", label: "Só por votável" },
  { value: "local", label: "Por local de votação" },
  { value: "uf", label: "Por UF" },
  { value: "municipio", label: "Por município" },
  { value: "zona", label: "Por zona" },
  { value: "secao", label: "Por seção" },
];

function optionalNumber(value: string): number | null {
  return /^\d+$/.test(value.trim()) ? Number(value) : null;
}

export function OpenDataPage() {
  const imports = useImports();
  const [form, setForm] = useState({
    turno: 1,
    cargo: 1,
    agrupar: "votavel" as Grouping,
    uf: "",
    municipio: "",
    votavel: "",
  });
  const [query, setQuery] = useState<AggregateParams | null>(null);
  const aggregate = useAggregate(query);

  function submit(event: FormEvent) {
    event.preventDefault();
    setQuery({
      ano: 2026,
      turno: form.turno,
      cargo: form.cargo,
      agrupar: form.agrupar,
      uf: form.uf || undefined,
      municipio: optionalNumber(form.municipio),
      votavel: optionalNumber(form.votavel),
      limit: 500,
    });
  }

  const emptyDatabase = imports.error instanceof ApiError && imports.error.status === 503;

  return (
    <>
      <header className="page__header">
        <span className="eyebrow">Portal de Dados Abertos</span>
        <h1>Dados abertos</h1>
        <p className="lead">
          Somas sobre os CSVs de boletim de urna do Portal de Dados Abertos do TSE, importados para a base
          local com <code>make ingest</code>.
        </p>
      </header>

      <section className="card" aria-labelledby="importacoes-titulo">
        <h2 id="importacoes-titulo" className="card__title">
          Bases importadas
        </h2>
        {imports.isPending && <Loading />}
        {imports.error && !emptyDatabase && <ErrorMessage error={imports.error} />}
        {(emptyDatabase || imports.data?.length === 0) && (
          <Empty>
            Nada importado ainda. Rode, por exemplo,{" "}
            <code>make ingest ARGS="--turno 1 2 --uf AC --fonte ambos"</code>.
          </Empty>
        )}
        {imports.data && imports.data.length > 0 && (
          <div className="table-wrap">
            <table className="table table--compact">
              <thead>
                <tr>
                  <th scope="col">Fonte</th>
                  <th scope="col">Ano</th>
                  <th scope="col">Turno</th>
                  <th scope="col">UF</th>
                  <th scope="col" className="num">
                    Seções
                  </th>
                  <th scope="col" className="num">
                    Linhas
                  </th>
                  <th scope="col">Arquivo</th>
                </tr>
              </thead>
              <tbody>
                {imports.data.map((d) => (
                  <tr key={`${d.tipo}-${d.ano}-${d.turno}-${d.uf}`}>
                    <td>{d.tipo === "urnas" ? "Arquivos de urna" : "CSV de boletins"}</td>
                    <td>{d.ano}</td>
                    <td>{d.turno}º</td>
                    <td>{d.uf}</td>
                    <td className="num">{formatInt(d.secoes)}</td>
                    <td className="num">{formatInt(d.linhas)}</td>
                    <td className="mono muted">{d.arquivo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section aria-labelledby="consulta-titulo">
        <h2 id="consulta-titulo" className="section-heading">
          Votação somada
        </h2>
        <form className="filters" onSubmit={submit}>
          <SelectField
            label="Turno"
            value={form.turno}
            options={[
              { value: 1, label: "1º turno" },
              { value: 2, label: "2º turno" },
            ]}
            onChange={(v) => setForm({ ...form, turno: v ?? 1 })}
          />
          <SelectField
            label="Cargo"
            value={form.cargo}
            options={OFFICES}
            onChange={(v) => setForm({ ...form, cargo: v ?? 1 })}
          />
          <SelectField
            label="Agrupar"
            value={form.agrupar}
            options={GROUPINGS}
            onChange={(v) => setForm({ ...form, agrupar: v ?? "votavel" })}
          />
          <SelectField
            label="UF"
            value={form.uf || null}
            placeholder="Todas importadas"
            options={UFS.map((u) => ({ value: u.sigla, label: u.nome }))}
            onChange={(v) => setForm({ ...form, uf: v ?? "" })}
          />
          <TextField
            label="Município (código TSE)"
            type="number"
            value={form.municipio}
            onChange={(v) => setForm({ ...form, municipio: v })}
          />
          <TextField
            label="Número do votável"
            type="number"
            value={form.votavel}
            onChange={(v) => setForm({ ...form, votavel: v })}
          />
          <div className="field field--action">
            <button type="submit" className="button">
              Consultar
            </button>
          </div>
        </form>
        {aggregate.isFetching && <Loading label="Somando votos…" />}
        {aggregate.error && <ErrorMessage error={aggregate.error} />}
        {aggregate.data && <AggregateTable rows={aggregate.data} grouping={query?.agrupar ?? "votavel"} />}
      </section>
    </>
  );
}

function place(row: VoteAggregate): string {
  const parts = [
    row.uf,
    row.nome_municipio,
    row.zona !== undefined ? `Zona ${pad(row.zona, 4)}` : undefined,
    row.secao !== undefined ? `Seção ${pad(row.secao, 4)}` : undefined,
  ];
  return parts.filter(Boolean).join(" · ");
}

export function AggregateTable({ rows, grouping }: { rows: VoteAggregate[]; grouping: Grouping }) {
  if (rows.length === 0) return <Empty>Nenhum voto encontrado com esses filtros.</Empty>;
  return (
    <div className="card table-wrap">
      <table className="table table--compact">
        <thead>
          <tr>
            {grouping !== "votavel" && <th scope="col">Local</th>}
            <th scope="col">Votável</th>
            <th scope="col">Partido</th>
            <th scope="col" className="num">
              Votos
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${place(row)}-${row.tipo}-${row.numero}-${index}`}>
              {grouping !== "votavel" && <td>{place(row)}</td>}
              <td>
                <strong>{row.nome}</strong> <span className="muted mono">{row.numero}</span>
              </td>
              <td>{row.partido ?? "—"}</td>
              <td className="num">{formatInt(row.votos)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
