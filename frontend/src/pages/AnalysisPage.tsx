import { useMemo, useState, type FormEvent } from "react";

import { ApiError } from "../api/client";
import {
  useLateVotes,
  useMesh,
  useMunicipalTimeline,
  useMunicipalTurnout,
  useMunicipalities,
  useTimeline,
  useTurnout,
  type AnalysisParams,
} from "../api/hooks";
import type { Group, Grouping, LateVotesReport, TurnoutAggregate } from "../api/types";
import { Segmented } from "../components/Charts";
import { SelectField } from "../components/Field";
import { GeoMap, type MapFeature } from "../components/GeoMap";
import { Stat } from "../components/Stat";
import { Empty, ErrorMessage, Loading } from "../components/Status";
import { TimelineChart } from "../components/TimelineChart";
import { CUTOFFS, formatDateTime, formatInt, formatPercent, pad, share } from "../lib/format";
import { sequentialColor } from "../lib/colors";
import { UFS, ufName } from "../lib/ufs";

const OFFICES = [
  { value: 1, label: "Presidente" },
  { value: 3, label: "Governador" },
  { value: 5, label: "Senador" },
  { value: 6, label: "Deputado Federal" },
  { value: 7, label: "Deputado Estadual" },
  { value: 8, label: "Deputado Distrital" },
];

const GROUPINGS: { value: Grouping; label: string }[] = [
  { value: "total", label: "Total" },
  { value: "uf", label: "Por UF" },
  { value: "municipio", label: "Por município" },
  { value: "zona", label: "Por zona" },
  { value: "local", label: "Por local de votação" },
  { value: "secao", label: "Por seção" },
];

// Eleição federal de cada turno: só para listar os municípios no filtro.
const REFERENCE_ELECTION: Record<number, number> = { 1: 6257, 2: 6258 };

export function groupLabel(group: Group): string {
  const parts = [
    group.uf,
    group.nome_municipio ?? (group.municipio !== undefined ? `Município ${group.municipio}` : undefined),
    group.zona !== undefined ? `Zona ${pad(group.zona, 4)}` : undefined,
    group.local !== undefined ? `Local ${group.local}` : undefined,
    group.secao !== undefined ? `Seção ${pad(group.secao, 4)}` : undefined,
  ];
  return parts.filter(Boolean).join(" · ") || "Total";
}

function isEmptyDatabase(error: unknown): boolean {
  return error instanceof ApiError && error.status === 503;
}

export function AnalysisPage() {
  const [form, setForm] = useState({
    turno: 1,
    uf: "",
    municipio: null as number | null,
    agrupar: "total" as Grouping,
    apos: "17:00",
    cargo: 1,
  });
  const [params, setParams] = useState<AnalysisParams | null>(null);
  const municipalities = useMunicipalities(REFERENCE_ELECTION[form.turno] ?? null, form.uf || null);
  const turnout = useTurnout(params);
  const timeline = useTimeline(params);
  const late = useLateVotes(params);

  function submit(event: FormEvent) {
    event.preventDefault();
    setParams({
      turno: form.turno,
      cargo: form.cargo,
      query: {
        agrupar: form.agrupar,
        uf: form.uf || undefined,
        municipio: form.municipio,
        apos: form.apos,
        limit: 1000,
      },
    });
  }

  return (
    <>
      <header className="page__header">
        <span className="eyebrow">Base local</span>
        <h1>Análises</h1>
        <p className="lead">
          Somas sobre todas as urnas importadas na base local: aptos, comparecimento, biometria, votos por
          horário e votos dados depois de um horário.
        </p>
      </header>

      <form className="filters" aria-label="Filtros da análise" onSubmit={submit}>
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
          label="UF"
          value={form.uf || null}
          placeholder="Todas importadas"
          options={UFS.map((u) => ({ value: u.sigla, label: u.nome }))}
          onChange={(v) => setForm({ ...form, uf: v ?? "", municipio: null })}
        />
        <SelectField
          label="Município"
          value={form.municipio}
          placeholder={form.uf ? "Todos" : "—"}
          disabled={!form.uf || municipalities.isPending}
          options={(municipalities.data ?? [])
            .slice()
            .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))
            .map((m) => ({ value: m.codigo, label: m.nome }))}
          onChange={(v) => setForm({ ...form, municipio: v })}
        />
        <SelectField
          label="Agrupar comparecimento"
          value={form.agrupar}
          options={GROUPINGS}
          onChange={(v) => setForm({ ...form, agrupar: v ?? "total" })}
        />
        <SelectField
          label="Votos a partir de (Brasília)"
          value={form.apos}
          options={CUTOFFS.map((c) => ({ value: c, label: c }))}
          onChange={(v) => setForm({ ...form, apos: v ?? "17:00" })}
        />
        <SelectField
          label="Cargo da estimativa"
          value={form.cargo}
          options={OFFICES}
          onChange={(v) => setForm({ ...form, cargo: v ?? 1 })}
        />
        <div className="field field--action">
          <button type="submit" className="button">
            Analisar
          </button>
        </div>
      </form>

      {!params && <Empty>Escolha os filtros e clique em Analisar.</Empty>}

      {params && (
        <section aria-labelledby="comparecimento-titulo">
          <h2 id="comparecimento-titulo" className="section-heading">
            Comparecimento e biometria
          </h2>
          {turnout.isPending && <Loading label="Somando seções…" />}
          {turnout.error && <ErrorMessage error={turnout.error} />}
          {turnout.data && <TurnoutView rows={turnout.data} />}
        </section>
      )}

      {params?.query.uf && (
        <AnalysisMap turno={params.turno} uf={params.query.uf} cutoff={params.query.apos ?? "17:00"} />
      )}

      {params && (
        <section aria-labelledby="horario-titulo">
          <h2 id="horario-titulo" className="section-heading">
            Votos por horário
          </h2>
          {timeline.isPending && <Loading label="Somando os logs das urnas…" />}
          {timeline.error &&
            (isEmptyDatabase(timeline.error) ? (
              <Empty>
                Os horários vêm do pacote de arquivos de urna. Importe com{" "}
                <code>make ingest ARGS="--turno 1 --uf AC --fonte urnas"</code>.
              </Empty>
            ) : (
              <ErrorMessage error={timeline.error} />
            ))}
          {timeline.data && timeline.data.length === 0 && <Empty>Sem votos para esses filtros.</Empty>}
          {timeline.data && timeline.data.length > 0 && (
            <div className="card">
              <TimelineChart
                buckets={timeline.data}
                marker={params.query.apos}
                title="Votos computados a cada 15 minutos (horário de Brasília)"
              />
            </div>
          )}
        </section>
      )}

      {params && (
        <section aria-labelledby="tardios-titulo">
          <h2 id="tardios-titulo" className="section-heading">
            Votos a partir das {params.query.apos}
          </h2>
          {late.isPending && <Loading label="Estimando…" />}
          {late.error && !isEmptyDatabase(late.error) && <ErrorMessage error={late.error} />}
          {late.error && isEmptyDatabase(late.error) && <Empty>{(late.error as ApiError).detail}</Empty>}
          {late.data && <LateVotesView report={late.data} />}
        </section>
      )}
    </>
  );
}

export function TurnoutView({ rows }: { rows: TurnoutAggregate[] }) {
  if (rows.length === 0) return <Empty>Nenhuma seção encontrada com esses filtros.</Empty>;
  const single = rows.length === 1 ? rows[0] : undefined;
  if (single) {
    const coverage = single.secoes_com_arquivos_urna;
    return (
      <>
        <dl className="stats">
          <Stat label="Seções" value={formatInt(single.secoes)} />
          <Stat label="Eleitores aptos" value={formatInt(single.aptos)} />
          <Stat
            label="Comparecimento"
            value={formatInt(single.comparecimento)}
            detail={formatPercent(single.percentual_comparecimento)}
          />
          <Stat label="Abstenção" value={formatInt(single.abstencoes)} />
          <Stat
            label="Habilitados por biometria"
            value={formatInt(single.habilitados_biometria)}
            detail={
              single.habilitados_biometria !== null
                ? formatPercent(share(single.habilitados_biometria, single.comparecimento))
                : undefined
            }
          />
          <Stat label="Por ano de nascimento" value={formatInt(single.habilitados_ano_nascimento)} />
          <Stat label="Sem biometria" value={formatInt(single.sem_biometria)} />
          <Stat
            label="Último voto"
            value={formatDateTime(single.ultimo_encerramento)}
            detail="horário de Brasília"
          />
        </dl>
        {coverage < single.secoes && (
          <p className="callout">
            Biometria detalhada em {formatInt(coverage)} de {formatInt(single.secoes)} seções: ela só existe
            nas UFs com o pacote de arquivos de urna importado.
          </p>
        )}
      </>
    );
  }
  return (
    <div className="card table-wrap">
      <table className="table table--compact">
        <caption className="visually-hidden">Comparecimento agrupado</caption>
        <thead>
          <tr>
            <th scope="col">Grupo</th>
            <th scope="col" className="num">
              Seções
            </th>
            <th scope="col" className="num">
              Aptos
            </th>
            <th scope="col" className="num">
              Comparecimento
            </th>
            <th scope="col" className="num">
              %
            </th>
            <th scope="col" className="num">
              Biometria
            </th>
            <th scope="col" className="num">
              Ano nasc.
            </th>
            <th scope="col" className="num">
              Sem biometria
            </th>
            <th scope="col">Último voto</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={groupLabel(r.grupo)}>
              <td>{groupLabel(r.grupo)}</td>
              <td className="num">{formatInt(r.secoes)}</td>
              <td className="num">{formatInt(r.aptos)}</td>
              <td className="num">{formatInt(r.comparecimento)}</td>
              <td className="num">{formatPercent(r.percentual_comparecimento)}</td>
              <td className="num">{formatInt(r.habilitados_biometria)}</td>
              <td className="num">{formatInt(r.habilitados_ano_nascimento)}</td>
              <td className="num">{formatInt(r.sem_biometria)}</td>
              <td className="mono">{formatDateTime(r.ultimo_encerramento)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function LateVotesView({ report }: { report: LateVotesReport }) {
  const { resumo } = report;
  return (
    <>
      <dl className="stats">
        <Stat
          label={`Votos a partir das ${report.apos}`}
          value={formatInt(resumo.votos_apos)}
          detail={`${formatPercent(share(resumo.votos_apos, resumo.comparecimento))} do comparecimento · contagem exata`}
        />
        <Stat label="Seções consideradas" value={formatInt(resumo.secoes)} />
      </dl>
      <div className="callout">
        <strong>Estimativa, não contagem</strong>
        {report.metodo}
        {resumo.secoes_sem_fuso > 0 &&
          ` ${formatInt(resumo.secoes_sem_fuso)} seções do exterior ficaram de fora.`}
      </div>
      {report.votaveis.length === 0 ? (
        <Empty>Sem votos por candidato: importe também os CSVs de boletins dessa UF.</Empty>
      ) : (
        <div className="card table-wrap">
          <table className="table table--compact">
            <caption className="visually-hidden">Estimativa de votos a partir de {report.apos}</caption>
            <thead>
              <tr>
                <th scope="col">Votável</th>
                <th scope="col">Partido</th>
                <th scope="col" className="num">
                  Votos nas seções
                </th>
                <th scope="col" className="num">
                  Estimados após {report.apos}
                </th>
              </tr>
            </thead>
            <tbody>
              {report.votaveis.map((v) => (
                <tr key={`${v.tipo}-${v.numero}`}>
                  <td>
                    <strong>{v.nome}</strong> <span className="muted mono">{v.numero}</span>
                  </td>
                  <td>{v.partido ?? "—"}</td>
                  <td className="num">{formatInt(v.votos_nas_secoes)}</td>
                  <td className="num">{formatInt(Math.round(v.votos_apos_estimados))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

type MapMetric = "comparecimento" | "biometria" | "tardios";

const METRICS: { value: MapMetric; label: string }[] = [
  { value: "comparecimento", label: "Comparecimento" },
  { value: "biometria", label: "Biometria" },
  { value: "tardios", label: "Votos após o corte" },
];

const ibgeId = (feature: MapFeature) => String(feature.properties.codigo_ibge ?? "");

/** Fatia de votos a partir do horário de corte, por município (a partir dos intervalos de 15 min). */
export function lateShareByMunicipality(
  points: { grupo: Group; inicio: string; votos: number }[],
  cutoff: string,
): Map<number, number> {
  const totals = new Map<number, { all: number; late: number }>();
  for (const p of points) {
    const code = p.grupo.municipio;
    if (code === undefined) continue;
    const entry = totals.get(code) ?? { all: 0, late: 0 };
    entry.all += p.votos;
    if (p.inicio >= cutoff) entry.late += p.votos;
    totals.set(code, entry);
  }
  return new Map([...totals.entries()].map(([code, t]) => [code, t.all ? (100 * t.late) / t.all : 0]));
}

function AnalysisMap({ turno, uf, cutoff }: { turno: number; uf: string; cutoff: string }) {
  const [metric, setMetric] = useState<MapMetric>("comparecimento");
  const mesh = useMesh(uf);
  const municipalities = useMunicipalities(REFERENCE_ELECTION[turno] ?? null, uf);
  const turnout = useMunicipalTurnout(turno, uf);
  const timeline = useMunicipalTimeline(turno, uf, metric === "tardios");

  const values = useMemo(() => {
    const byTse = new Map<number, number | null>();
    if (metric === "tardios") {
      for (const [code, share] of lateShareByMunicipality(timeline.data ?? [], cutoff))
        byTse.set(code, share);
    } else {
      for (const row of turnout.data ?? []) {
        const code = row.grupo.municipio;
        if (code === undefined) continue;
        byTse.set(
          code,
          metric === "comparecimento"
            ? row.percentual_comparecimento
            : row.habilitados_biometria !== null && row.comparecimento
              ? (100 * row.habilitados_biometria) / row.comparecimento
              : null,
        );
      }
    }
    const byIbge = new Map<string, { name: string; value: number | null }>();
    for (const m of municipalities.data ?? []) {
      if (m.codigo_ibge)
        byIbge.set(String(m.codigo_ibge), { name: m.nome, value: byTse.get(m.codigo) ?? null });
    }
    return byIbge;
  }, [metric, timeline.data, turnout.data, municipalities.data, cutoff]);

  const known = [...values.values()].map((v) => v.value).filter((v): v is number => v !== null);
  const min = known.length ? Math.min(...known) : 0;
  const max = known.length ? Math.max(...known) : 100;
  const pending =
    mesh.isPending ||
    municipalities.isPending ||
    turnout.isPending ||
    (metric === "tardios" && timeline.isPending);
  const label = METRICS.find((m) => m.value === metric)?.label ?? "";

  return (
    <section aria-labelledby="mapa-analise-titulo">
      <h2 id="mapa-analise-titulo" className="section-heading">
        Mapa de {ufName(uf)}
      </h2>
      <div className="card">
        <div className="card__toolbar">
          <Segmented label="Métrica do mapa" value={metric} options={METRICS} onChange={setMetric} />
        </div>
        {pending && <Loading label="Montando o mapa…" />}
        {timeline.error && metric === "tardios" && (
          <Empty>Os horários vêm do pacote de arquivos de urna; importe-o para ver este mapa.</Empty>
        )}
        {mesh.data && !pending && known.length === 0 && (
          <Empty>Sem dados desta métrica para {ufName(uf)} na base local.</Empty>
        )}
        {mesh.data && !pending && known.length > 0 && (
          <>
            <GeoMap
              geojson={mesh.data}
              areaId={ibgeId}
              areaLabel={(id) => {
                const area = values.get(id);
                return `${area?.name ?? id}: ${formatPercent(area?.value ?? null)}`;
              }}
              fill={(id) => sequentialColor(values.get(id)?.value, min, max)}
              tooltip={(id) => {
                const area = values.get(id);
                return (
                  <>
                    <strong>{area?.name ?? id}</strong>
                    {label}: {formatPercent(area?.value ?? null)}
                  </>
                );
              }}
              title={`${label} por município em ${ufName(uf)}`}
              height={460}
            />
            <div className="map__gradient" aria-label={`Legenda: ${label}`}>
              <span>{formatPercent(min)}</span>
              <span aria-hidden="true" />
              <span>{formatPercent(max)}</span>
            </div>
            {metric === "tardios" && (
              <p className="muted" style={{ fontSize: 13 }}>
                Percentual dos votos de cada município computados a partir das {cutoff} (horário de Brasília).
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}
