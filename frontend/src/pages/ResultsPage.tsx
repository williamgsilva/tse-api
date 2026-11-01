import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useElections, useMunicipalities, useResult } from "../api/hooks";
import type { Candidate, Election, ElectionResult } from "../api/types";
import { SelectField, TextField } from "../components/Field";
import { Composition, HBarChart } from "../components/Charts";
import { Stat } from "../components/Stat";
import { Empty, ErrorMessage, Loading } from "../components/Status";
import { VoteBar } from "../components/VoteBar";
import { formatDateTime, formatInt, formatPercent } from "../lib/format";
import { colorScale } from "../lib/colors";
import { UFS, ufName } from "../lib/ufs";

const YEAR = 2026;
const PRESIDENT = 1;
const PAGE = 50;

function numberParam(params: URLSearchParams, key: string): number | null {
  const value = params.get(key);
  return value && /^\d+$/.test(value) ? Number(value) : null;
}

function defaultElection(elections: Election[]): Election | undefined {
  return elections.find((e) => e.turno === 2 && e.cargos.some((c) => c.codigo === PRESIDENT)) ?? elections[0];
}

function scopeOptions(election: Election | undefined, cargo: number | null) {
  const office = election?.cargos.find((c) => c.codigo === cargo);
  const restricted = office?.abrangencias.filter((a) => a !== "br") ?? [];
  const ufs = restricted.length > 0 ? UFS.filter((uf) => restricted.includes(uf.sigla)) : UFS;
  const options = ufs.map((uf) => ({ value: uf.sigla, label: uf.nome }));
  return cargo === PRESIDENT ? [{ value: "br", label: "Brasil" }, ...options] : options;
}

export function ResultsPage() {
  const [params, setParams] = useSearchParams();
  const { elections, isPending, error, refetch } = useElections(YEAR);

  const election =
    elections.find((e) => e.codigo === numberParam(params, "eleicao")) ?? defaultElection(elections);
  const cargo = numberParam(params, "cargo") ?? election?.cargos[0]?.codigo ?? null;
  const scopes = scopeOptions(election, cargo);
  const uf = scopes.some((s) => s.value === params.get("uf")) ? params.get("uf") : (scopes[0]?.value ?? null);
  const municipio = numberParam(params, "municipio");

  const municipalities = useMunicipalities(election?.codigo ?? null, uf);
  const result = useResult(election?.codigo ?? null, uf, cargo, uf === "br" ? null : municipio);

  function update(changes: Record<string, string | number | null>) {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value === null) next.delete(key);
      else next.set(key, String(value));
    }
    setParams(next, { replace: true });
  }

  if (isPending) return <Loading label="Carregando eleições…" />;
  if (error) return <ErrorMessage error={error} onRetry={() => void refetch()} />;

  return (
    <>
      <header className="page__header">
        <span className="eyebrow">Totalização oficial</span>
        <h1>Resultados</h1>
        <p className="lead">Votos totalizados por cargo, no Brasil, numa UF ou num município.</p>
      </header>

      <form className="filters" aria-label="Filtros do resultado" onSubmit={(e) => e.preventDefault()}>
        <SelectField
          label="Eleição"
          value={election?.codigo ?? null}
          options={elections.map((e) => ({ value: e.codigo, label: e.nome }))}
          onChange={(value) => update({ eleicao: value, cargo: null, uf: null, municipio: null })}
        />
        <SelectField
          label="Cargo"
          value={cargo}
          options={(election?.cargos ?? []).map((c) => ({ value: c.codigo, label: c.nome }))}
          onChange={(value) => update({ cargo: value, uf: null, municipio: null })}
        />
        <SelectField
          label="Abrangência"
          value={uf}
          options={scopes}
          onChange={(value) => update({ uf: value, municipio: null })}
        />
        <SelectField
          label="Município"
          value={municipio}
          placeholder={uf === "br" ? "—" : "Toda a UF"}
          disabled={uf === "br" || municipalities.isPending}
          options={(municipalities.data ?? [])
            .slice()
            .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))
            .map((m) => ({ value: m.codigo, label: m.nome }))}
          onChange={(value) => update({ municipio: value })}
        />
      </form>

      {result.isPending && <Loading label="Carregando resultado…" />}
      {result.error && <ErrorMessage error={result.error} onRetry={() => void result.refetch()} />}
      {result.data && (
        <ResultView
          result={result.data}
          scopeLabel={
            municipio
              ? `${municipalities.data?.find((m) => m.codigo === municipio)?.nome ?? municipio} (${uf?.toUpperCase()})`
              : uf === "br"
                ? "Brasil"
                : ufName(uf ?? "")
          }
        />
      )}
    </>
  );
}

function ResultView({ result, scopeLabel }: { result: ElectionResult; scopeLabel: string }) {
  const { secoes, eleitorado, votos } = result.totais;
  const office = result.cargos[0];
  return (
    <section aria-labelledby="resultado-titulo">
      <div className="section-heading">
        <h2 id="resultado-titulo">
          {office?.nome} · {scopeLabel}
        </h2>
        <p className="muted">
          {result.totalizacao_finalizada ? "Totalização finalizada" : "Totalização em andamento"} · atualizado
          em {formatDateTime(result.atualizado_em)}
        </p>
      </div>
      <dl className="stats">
        <Stat
          label="Seções totalizadas"
          value={formatPercent(secoes?.percentual_totalizadas)}
          detail={`${formatInt(secoes?.totalizadas)} de ${formatInt(secoes?.total)}`}
        />
        <Stat
          label="Comparecimento"
          value={formatInt(eleitorado?.comparecimento)}
          detail={`${formatPercent(eleitorado?.percentual_comparecimento)} do eleitorado`}
        />
        <Stat
          label="Abstenção"
          value={formatInt(eleitorado?.abstencao)}
          detail={formatPercent(eleitorado?.percentual_abstencao)}
        />
        <Stat label="Votos válidos" value={formatInt(votos?.validos)} />
        <Stat
          label="Brancos"
          value={formatInt(votos?.brancos)}
          detail={formatPercent(votos?.percentual_brancos)}
        />
        <Stat label="Nulos" value={formatInt(votos?.nulos)} detail={formatPercent(votos?.percentual_nulos)} />
      </dl>
      {office && <ResultCharts result={result} />}
      {office ? (
        <CandidatesTable candidates={office.candidatos} seats={office.vagas} />
      ) : (
        <Empty>Sem candidatos.</Empty>
      )}
    </section>
  );
}

function situationClass(candidate: Candidate): string {
  if (candidate.eleito) return "badge badge--elected";
  if (candidate.situacao?.includes("2º turno")) return "badge badge--runoff";
  return "badge";
}

export function CandidatesTable({ candidates, seats }: { candidates: Candidate[]; seats: number | null }) {
  const [search, setSearch] = useState("");
  const [visible, setVisible] = useState(PAGE);
  const filtered = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("pt-BR");
    if (!term) return candidates;
    return candidates.filter((c) =>
      [c.nome_urna, c.nome, c.partido, String(c.numero)].some((v) =>
        v?.toLocaleLowerCase("pt-BR").includes(term),
      ),
    );
  }, [candidates, search]);
  const shown = filtered.slice(0, visible);

  return (
    <div className="card">
      <div className="card__toolbar">
        <p className="muted">
          {formatInt(candidates.length)} candidaturas{seats ? ` · ${formatInt(seats)} vaga(s)` : ""}
        </p>
        {candidates.length > 10 && (
          <TextField
            label="Buscar candidato"
            type="search"
            value={search}
            placeholder="nome, partido ou número"
            onChange={(value) => {
              setSearch(value);
              setVisible(PAGE);
            }}
          />
        )}
      </div>
      <div className="table-wrap">
        <table className="table">
          <caption className="visually-hidden">Votos por candidatura</caption>
          <thead>
            <tr>
              <th scope="col">Nº</th>
              <th scope="col">Candidatura</th>
              <th scope="col" className="num">
                Votos
              </th>
              <th scope="col">% válidos</th>
              <th scope="col">Situação</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((c) => (
              <tr key={`${c.numero}-${c.nome}`}>
                <td className="mono">{c.numero}</td>
                <td>
                  <strong>{c.nome_urna}</strong>
                  <span className="muted block">
                    {c.partido}
                    {c.composicao && c.composicao !== c.partido ? ` · ${c.composicao}` : ""}
                  </span>
                </td>
                <td className="num">{formatInt(c.votos)}</td>
                <td>
                  <VoteBar percent={c.percentual ?? 0} highlight={c.eleito} />
                </td>
                <td>
                  <span className={situationClass(c)}>{c.situacao ?? "—"}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {filtered.length === 0 && <Empty>Nenhuma candidatura encontrada.</Empty>}
      {filtered.length > visible && (
        <button
          type="button"
          className="button button--ghost"
          onClick={() => setVisible((v) => v + PAGE * 4)}
        >
          Mostrar mais ({formatInt(filtered.length - visible)} restantes)
        </button>
      )}
    </div>
  );
}

function ResultCharts({ result }: { result: ElectionResult }) {
  const office = result.cargos[0];
  if (!office) return null;
  const parties: string[] = [];
  for (const c of office.candidatos) if (c.partido && !parties.includes(c.partido)) parties.push(c.partido);
  const color = colorScale(parties);
  const { eleitorado, votos } = result.totais;
  return (
    <div className="grid-2">
      <section className="card" aria-labelledby="ranking-titulo">
        <h3 id="ranking-titulo" className="card__title">
          Mais votados
        </h3>
        <HBarChart
          label="Mais votados"
          items={office.candidatos.slice(0, 10).map((c) => ({
            id: `${c.numero}-${c.nome}`,
            label: c.nome_urna ?? String(c.numero),
            detail: c.partido,
            value: c.votos,
            percent: c.percentual,
            color: color(c.partido),
            badge: c.eleito ? "eleito" : null,
          }))}
        />
      </section>
      <section className="card" aria-labelledby="composicao-titulo">
        <h3 id="composicao-titulo" className="card__title">
          Para onde foram os votos
        </h3>
        <Composition
          label="Composição do eleitorado"
          parts={[
            { id: "validos", label: "Válidos", value: votos?.validos ?? 0, color: "var(--series-1)" },
            { id: "brancos", label: "Brancos", value: votos?.brancos ?? 0, color: "var(--series-4)" },
            { id: "nulos", label: "Nulos", value: votos?.nulos ?? 0, color: "var(--series-2)" },
            {
              id: "abstencao",
              label: "Abstenção",
              value: eleitorado?.abstencao ?? 0,
              color: "var(--series-other)",
            },
          ]}
        />
      </section>
    </div>
  );
}
