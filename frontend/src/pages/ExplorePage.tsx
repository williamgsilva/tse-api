import { useCallback, useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { useMesh, useMunicipalities, useResult, useSubdivisions, useVotingEvents } from "../api/hooks";
import type { Election, SubdivisionResult, Totals } from "../api/types";
import { Composition, HBarChart, Segmented, type BarItem } from "../components/Charts";
import { GeoMap, type MapFeature } from "../components/GeoMap";
import { Stat } from "../components/Stat";
import { Empty, ErrorMessage, Loading } from "../components/Status";
import { colorScale, OTHER, sequentialColor } from "../lib/colors";
import { formatInt, formatPercent, pad } from "../lib/format";
import { REGIONS, regionName, regionOf, type RegionKey } from "../lib/regions";
import {
  aggregate,
  leader,
  leadersCount,
  officesOfRound,
  partyOrder,
  turnoutPercent,
  type Candidate,
} from "../lib/results";
import { ufName } from "../lib/ufs";

const YEAR = 2026;
const PRESIDENT = 1;
type ColorMode = "lider" | "comparecimento";

function numberParam(params: URLSearchParams, name: string): number | null {
  const value = params.get(name);
  return value && /^\d+$/.test(value) ? Number(value) : null;
}

const stateId = (feature: MapFeature) => String(feature.properties.uf ?? "");
const municipalityId = (feature: MapFeature) => String(feature.properties.codigo_ibge ?? "");

function candidateBars(
  candidates: Candidate[],
  color: (party: string | null | undefined) => string,
): BarItem[] {
  return candidates.slice(0, 10).map((c) => ({
    id: `${c.numero}-${c.nome_urna}`,
    label: c.nome_urna ?? String(c.numero),
    detail: c.partido,
    value: c.votos,
    percent: c.percentual,
    color: color(c.partido),
    badge: c.eleito ? "eleito" : null,
  }));
}

export function ExplorePage() {
  const [params, setParams] = useSearchParams();
  const events = useVotingEvents(YEAR);

  const turno = numberParam(params, "turno") === 2 ? 2 : 1;
  const offices = useMemo(() => officesOfRound(events.data ?? [], turno), [events.data, turno]);
  const office = offices.find((o) => o.codigo === numberParam(params, "cargo")) ?? offices[0];
  const election: Election | undefined = office?.eleicao;
  const cargo = office?.codigo ?? null;
  const uf = params.get("uf");
  const region = (params.get("regiao") as RegionKey | null) ?? (uf ? (regionOf(uf) ?? null) : null);
  const municipalityIbge = params.get("municipio");
  const mode: ColorMode = params.get("cor") === "comparecimento" ? "comparecimento" : "lider";

  // Cores dos partidos: ordem do Brasil inteiro, para não mudarem ao navegar entre níveis.
  const national = useSubdivisions(election?.codigo ?? null, "br", cargo, cargo === PRESIDENT ? 20 : 3);
  const local = useSubdivisions(election?.codigo ?? null, uf, cargo, 3);
  const mesh = useMesh(uf ?? "br");
  const order = useMemo(() => partyOrder(national.data ?? []), [national.data]);
  const color = useMemo(() => colorScale(order), [order]);

  const areas = uf ? local.data : national.data;
  const byArea = useMemo(() => {
    const map = new Map<string, SubdivisionResult>();
    for (const area of areas ?? []) map.set(uf ? String(area.codigo_ibge) : area.codigo, area);
    return map;
  }, [areas, uf]);
  const turnoutRange = useMemo(() => {
    const values = (areas ?? []).map(turnoutPercent).filter((v): v is number => v !== null);
    return values.length ? { min: Math.min(...values), max: Math.max(...values) } : { min: 0, max: 100 };
  }, [areas]);

  const update = useCallback(
    (changes: Record<string, string | number | null>) => {
      const next = new URLSearchParams(params);
      for (const [name, value] of Object.entries(changes)) {
        if (value === null) next.delete(name);
        else next.set(name, String(value));
      }
      setParams(next, { replace: false });
    },
    [params, setParams],
  );

  const fill = useCallback(
    (id: string) => {
      const area = byArea.get(id);
      if (!area) return "var(--series-empty)";
      if (mode === "comparecimento")
        return sequentialColor(turnoutPercent(area), turnoutRange.min, turnoutRange.max);
      return color(leader(area)?.partido);
    },
    [byArea, mode, color, turnoutRange],
  );

  const tooltip = useCallback(
    (id: string) => {
      const area = byArea.get(id);
      const name = uf ? (area?.nome ?? "Município") : ufName(id);
      if (!area) return <strong>{name}</strong>;
      const first = leader(area);
      return (
        <>
          <strong>{name}</strong>
          {first && (
            <span className="block">
              {first.nome_urna} ({first.partido}) · {formatPercent(first.percentual)}
            </span>
          )}
          <span className="block muted">Comparecimento {formatPercent(turnoutPercent(area))}</span>
        </>
      );
    },
    [byArea, uf],
  );

  if (events.isPending) return <Loading label="Carregando eleições…" />;
  if (events.error) return <ErrorMessage error={events.error} onRetry={() => void events.refetch()} />;

  const focus = !uf && region ? (REGIONS.find((r) => r.id === region)?.ufs ?? []) : [];
  const selectedMunicipality = municipalityIbge ? byArea.get(municipalityIbge) : undefined;
  const loadingAreas = uf ? local.isPending : national.isPending;
  const areasError = uf ? local.error : national.error;

  return (
    <>
      <header className="page__header">
        <span className="eyebrow">Eleições 2026</span>
        <h1>Mapa dos resultados</h1>
        <p className="lead">
          Escolha o turno e o cargo, clique numa região, num estado e num município. Do município você chega
          às zonas, às seções e ao boletim de cada urna.
        </p>
      </header>

      <div className="toolbar">
        <Segmented
          label="Turno"
          value={turno}
          options={[
            { value: 1, label: "1º turno" },
            { value: 2, label: "2º turno" },
          ]}
          onChange={(value) => update({ turno: value, cargo: null, municipio: null })}
        />
        <Segmented
          label="Cargo"
          value={cargo ?? 0}
          options={offices.map((o) => ({ value: o.codigo, label: o.nome }))}
          onChange={(value) => update({ cargo: value, municipio: null })}
        />
        <Segmented
          label="Cor do mapa"
          value={mode}
          options={[
            { value: "lider", label: "Partido líder" },
            { value: "comparecimento", label: "Comparecimento" },
          ]}
          onChange={(value) => update({ cor: value === "lider" ? null : value })}
        />
      </div>

      <nav aria-label="Nível do mapa">
        <ol className="crumbs">
          <li>
            {region || uf ? (
              <button type="button" onClick={() => update({ regiao: null, uf: null, municipio: null })}>
                Brasil
              </button>
            ) : (
              <span aria-current="page">Brasil</span>
            )}
          </li>
          {region && (
            <li>
              {uf ? (
                <button type="button" onClick={() => update({ regiao: region, uf: null, municipio: null })}>
                  {regionName(region)}
                </button>
              ) : (
                <span aria-current="page">{regionName(region)}</span>
              )}
            </li>
          )}
          {uf && (
            <li>
              {selectedMunicipality ? (
                <button type="button" onClick={() => update({ municipio: null })}>
                  {ufName(uf)}
                </button>
              ) : (
                <span aria-current="page">{ufName(uf)}</span>
              )}
            </li>
          )}
          {selectedMunicipality && (
            <li>
              <span aria-current="page">{selectedMunicipality.nome}</span>
            </li>
          )}
        </ol>
      </nav>

      <div className="grid-2">
        <section className="card" aria-labelledby="mapa-titulo">
          <div className="card__toolbar">
            <h2 id="mapa-titulo" className="card__title" style={{ margin: 0 }}>
              {uf
                ? `${ufName(uf)} por município`
                : region
                  ? `${regionName(region)} por estado`
                  : "Brasil por estado"}
            </h2>
            {!uf && (
              <ul className="chips" aria-label="Regiões">
                {REGIONS.map((r) => (
                  <li key={r.id}>
                    <button
                      type="button"
                      className="chip"
                      aria-pressed={region === r.id}
                      onClick={() => update({ regiao: region === r.id ? null : r.id })}
                    >
                      {r.name}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {mesh.error && <ErrorMessage error={mesh.error} />}
          {areasError && <ErrorMessage error={areasError} />}
          {(mesh.isPending || loadingAreas) && (
            <Loading
              label={
                uf
                  ? "Carregando os resultados de cada município (a primeira consulta de um estado grande leva alguns segundos)…"
                  : "Carregando o mapa…"
              }
            />
          )}
          {mesh.data && !loadingAreas && (
            <>
              <GeoMap
                geojson={mesh.data}
                areaId={uf ? municipalityId : stateId}
                areaLabel={(id) => (uf ? (byArea.get(id)?.nome ?? `Município ${id}`) : ufName(id))}
                fill={fill}
                tooltip={tooltip}
                focus={focus}
                zoomToFocus={focus.length > 0}
                selected={uf ? municipalityIbge : null}
                onSelect={(id) =>
                  uf
                    ? update({ municipio: id === municipalityIbge ? null : id })
                    : update({ uf: id, regiao: regionOf(id) ?? null, municipio: null })
                }
                title={uf ? `Mapa de ${ufName(uf)} por município` : "Mapa do Brasil por estado"}
              />
              <MapLegend mode={mode} areas={areas ?? []} color={color} range={turnoutRange} />
            </>
          )}
        </section>

        <div className="panel-sticky">
          {selectedMunicipality && election && uf ? (
            <MunicipalityPanel
              election={election}
              uf={uf}
              area={selectedMunicipality}
              cargo={cargo}
              color={color}
            />
          ) : uf && election ? (
            <ScopePanel election={election} uf={uf} cargo={cargo} color={color} title={ufName(uf)} />
          ) : region ? (
            <RegionPanel
              region={region}
              areas={(national.data ?? []).filter((a) => focus.includes(a.codigo))}
              cargo={cargo}
              color={color}
            />
          ) : election && cargo === PRESIDENT ? (
            <ScopePanel election={election} uf="br" cargo={cargo} color={color} title="Brasil" />
          ) : (
            <LeadersPanel areas={national.data ?? []} color={color} />
          )}
        </div>
      </div>
    </>
  );
}

function MapLegend({
  mode,
  areas,
  color,
  range,
}: {
  mode: ColorMode;
  areas: SubdivisionResult[];
  color: (party: string | null | undefined) => string;
  range: { min: number; max: number };
}) {
  if (mode === "comparecimento") {
    return (
      <div className="map__gradient" aria-label="Legenda: comparecimento">
        <span>{formatPercent(range.min)}</span>
        <span aria-hidden="true" />
        <span>{formatPercent(range.max)}</span>
      </div>
    );
  }
  const counts = leadersCount(areas);
  return (
    <ul className="map__legend" aria-label="Legenda: partido do líder">
      {counts.slice(0, 8).map((c) => (
        <li key={c.partido}>
          <span className="chart__swatch" style={{ background: color(c.partido) }} aria-hidden="true" />
          {c.partido} <strong>{c.areas}</strong>
        </li>
      ))}
      {counts.length > 8 && (
        <li>
          <span className="chart__swatch" style={{ background: OTHER }} aria-hidden="true" />
          Outros
        </li>
      )}
      <li>
        <span className="chart__swatch" style={{ background: "var(--series-empty)" }} aria-hidden="true" />
        Sem resultado
      </li>
    </ul>
  );
}

function Summary({ totals }: { totals: Totals }) {
  const e = totals.eleitorado;
  const v = totals.votos;
  return (
    <>
      <dl className="stats stats--compact">
        <Stat label="Eleitorado" value={formatInt(e?.total)} />
        <Stat
          label="Comparecimento"
          value={formatPercent(e?.percentual_comparecimento)}
          detail={formatInt(e?.comparecimento)}
        />
        <Stat
          label="Abstenção"
          value={formatPercent(e?.percentual_abstencao)}
          detail={formatInt(e?.abstencao)}
        />
      </dl>
      <Composition
        label="Composição dos votos"
        parts={[
          { id: "validos", label: "Válidos", value: v?.validos ?? 0, color: "var(--series-1)" },
          { id: "brancos", label: "Brancos", value: v?.brancos ?? 0, color: "var(--series-4)" },
          { id: "nulos", label: "Nulos", value: v?.nulos ?? 0, color: "var(--series-2)" },
          { id: "abstencao", label: "Abstenção", value: e?.abstencao ?? 0, color: "var(--series-other)" },
        ]}
      />
    </>
  );
}

function ScopePanel({
  election,
  uf,
  cargo,
  color,
  title,
}: {
  election: Election;
  uf: string;
  cargo: number | null;
  color: (party: string | null | undefined) => string;
  title: string;
}) {
  const result = useResult(election.codigo, uf, cargo, null);
  const office = result.data?.cargos[0];
  return (
    <section className="card" aria-labelledby="painel-titulo">
      <h2 id="painel-titulo" className="card__title">
        {title} · {office?.nome ?? "Resultado"}
      </h2>
      {result.isPending && <Loading />}
      {result.error && <ErrorMessage error={result.error} />}
      {result.data && office && (
        <>
          <Summary totals={result.data.totais} />
          <h3 className="card__title" style={{ marginTop: 16 }}>
            Candidatos {office.vagas && office.vagas > 1 ? `(${office.vagas} vagas)` : ""}
          </h3>
          <HBarChart label={`Candidatos a ${office.nome}`} items={candidateBars(office.candidatos, color)} />
          <p style={{ marginTop: 16 }}>
            <Link
              className="button button--small"
              to={`/resultados?eleicao=${election.codigo}&cargo=${cargo}&uf=${uf}`}
            >
              Resultado completo
            </Link>
          </p>
        </>
      )}
    </section>
  );
}

function RegionPanel({
  region,
  areas,
  cargo,
  color,
}: {
  region: RegionKey;
  areas: SubdivisionResult[];
  cargo: number | null;
  color: (party: string | null | undefined) => string;
}) {
  if (areas.length === 0) return <Empty>Sem resultados na região para este cargo.</Empty>;
  const { candidates, totals } = aggregate(areas);
  return (
    <section className="card" aria-labelledby="regiao-titulo">
      <h2 id="regiao-titulo" className="card__title">
        Região {regionName(region)}
      </h2>
      <p className="card__subtitle">Soma dos {areas.length} estados da região</p>
      <Summary totals={totals} />
      {cargo === PRESIDENT ? (
        <>
          <h3 className="card__title" style={{ marginTop: 16 }}>
            Candidatos
          </h3>
          <HBarChart label="Candidatos na região" items={candidateBars(candidates, color)} />
        </>
      ) : (
        <LeadersTable areas={areas} color={color} />
      )}
    </section>
  );
}

function LeadersPanel({
  areas,
  color,
}: {
  areas: SubdivisionResult[];
  color: (party: string | null | undefined) => string;
}) {
  if (areas.length === 0) return <Empty>Sem resultados para este cargo.</Empty>;
  return (
    <section className="card" aria-labelledby="lideres-titulo">
      <h2 id="lideres-titulo" className="card__title">
        Mais votado em cada estado
      </h2>
      <p className="card__subtitle">Clique num estado no mapa para ver o resultado completo.</p>
      <LeadersTable areas={areas} color={color} />
    </section>
  );
}

function LeadersTable({
  areas,
  color,
}: {
  areas: SubdivisionResult[];
  color: (party: string | null | undefined) => string;
}) {
  return (
    <div className="table-wrap">
      <table className="table table--compact">
        <caption className="visually-hidden">Mais votado por estado</caption>
        <thead>
          <tr>
            <th scope="col">UF</th>
            <th scope="col">Mais votado</th>
            <th scope="col" className="num">
              %
            </th>
          </tr>
        </thead>
        <tbody>
          {areas.map((area) => {
            const first = leader(area);
            return (
              <tr key={area.codigo}>
                <td>{ufName(area.codigo)}</td>
                <td>
                  <span
                    className="chart__swatch"
                    style={{ background: color(first?.partido), marginRight: 6 }}
                    aria-hidden="true"
                  />
                  {first?.nome_urna} <span className="muted">{first?.partido}</span>
                </td>
                <td className="num">{formatPercent(first?.percentual)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function MunicipalityPanel({
  election,
  uf,
  area,
  cargo,
  color,
}: {
  election: Election;
  uf: string;
  area: SubdivisionResult;
  cargo: number | null;
  color: (party: string | null | undefined) => string;
}) {
  const municipio = Number(area.codigo);
  const result = useResult(election.codigo, uf, cargo, municipio);
  const municipalities = useMunicipalities(election.codigo, uf);
  const zones = municipalities.data?.find((m) => m.codigo === municipio)?.zonas ?? [];
  const office = result.data?.cargos[0];
  const sections = (zona?: number) =>
    `/secoes?pleito=${election.pleito}&uf=${uf}&municipio=${municipio}${zona ? `&zona=${zona}` : ""}`;
  return (
    <section className="card" aria-labelledby="municipio-titulo">
      <h2 id="municipio-titulo" className="card__title">
        {area.nome}
      </h2>
      <p className="card__subtitle">
        {ufName(uf)} · código TSE {pad(municipio, 5)}
        {area.codigo_ibge ? ` · IBGE ${area.codigo_ibge}` : ""}
      </p>
      {result.isPending && <Loading />}
      {result.error && <ErrorMessage error={result.error} />}
      {result.data && office && (
        <>
          <Summary totals={result.data.totais} />
          <h3 className="card__title" style={{ marginTop: 16 }}>
            {office.nome}
          </h3>
          <HBarChart
            label={`Candidatos a ${office.nome} em ${area.nome}`}
            items={candidateBars(office.candidatos, color)}
          />
        </>
      )}
      <h3 className="card__title" style={{ marginTop: 18 }}>
        Zonas e seções
      </h3>
      <ul className="chips" aria-label="Zonas eleitorais">
        {zones.map((zona) => (
          <li key={zona}>
            <Link className="chip" to={sections(zona)}>
              Zona {pad(zona, 4)}
            </Link>
          </li>
        ))}
      </ul>
      <p style={{ marginTop: 12 }}>
        <Link className="button button--small" to={sections()}>
          Ver todas as seções e boletins
        </Link>
      </p>
    </section>
  );
}
