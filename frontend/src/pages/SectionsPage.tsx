import { Link, useSearchParams } from "react-router-dom";

import { useMunicipalities, useSections, useVotingEvents } from "../api/hooks";
import type { VotingEvent } from "../api/types";
import { SelectField } from "../components/Field";
import { Empty, ErrorMessage, Loading } from "../components/Status";
import { formatDateTime, formatInt, pad } from "../lib/format";
import { UFS } from "../lib/ufs";

const YEAR = 2026;

function numberParam(params: URLSearchParams, key: string): number | null {
  const value = params.get(key);
  return value && /^\d+$/.test(value) ? Number(value) : null;
}

/** Pleitos com eleição ordinária (os de suplementares isoladas ficam de fora). */
function ordinaryEvents(events: VotingEvent[]): VotingEvent[] {
  return events.filter((event) => event.eleicoes.some((e) => e.nome.includes("Ordinária")));
}

function referenceElection(event: VotingEvent | undefined) {
  return event?.eleicoes.find((e) => e.nome.includes("Federal")) ?? event?.eleicoes[0];
}

export function SectionsPage() {
  const [params, setParams] = useSearchParams();
  const events = useVotingEvents(YEAR);
  const options = ordinaryEvents(events.data ?? []);

  const event = options.find((e) => e.pleito === numberParam(params, "pleito")) ?? options[0];
  const uf = params.get("uf") ?? null;
  const municipio = numberParam(params, "municipio");
  const zona = numberParam(params, "zona");

  const municipalities = useMunicipalities(referenceElection(event)?.codigo ?? null, uf);
  const municipality = municipalities.data?.find((m) => m.codigo === municipio);
  const sections = useSections(event?.pleito ?? null, uf, municipio, zona);

  function update(changes: Record<string, string | number | null>) {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value === null) next.delete(key);
      else next.set(key, String(value));
    }
    setParams(next, { replace: true });
  }

  if (events.isPending) return <Loading label="Carregando pleitos…" />;
  if (events.error) return <ErrorMessage error={events.error} onRetry={() => void events.refetch()} />;

  return (
    <>
      <header className="page__header">
        <span className="eyebrow">Arquivos oficiais das urnas</span>
        <h1>Seções e boletins de urna</h1>
        <p className="lead">
          Escolha a seção eleitoral para ver o boletim de urna, lido do arquivo oficial assinado que a urna
          transmitiu ao TSE.
        </p>
      </header>

      <form className="filters" aria-label="Localizar seção" onSubmit={(e) => e.preventDefault()}>
        <SelectField
          label="Turno"
          value={event?.pleito ?? null}
          options={options.map((e) => ({
            value: e.pleito,
            label: `${formatDateTime(e.data)} (pleito ${e.pleito})`,
          }))}
          onChange={(value) => update({ pleito: value })}
        />
        <SelectField
          label="UF"
          value={uf}
          placeholder="Escolha a UF"
          options={UFS.map((u) => ({ value: u.sigla, label: u.nome }))}
          onChange={(value) => update({ uf: value, municipio: null, zona: null })}
        />
        <SelectField
          label="Município"
          value={municipio}
          placeholder={uf ? "Escolha o município" : "—"}
          disabled={!uf || municipalities.isPending}
          options={(municipalities.data ?? [])
            .slice()
            .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))
            .map((m) => ({ value: m.codigo, label: m.nome }))}
          onChange={(value) => update({ municipio: value, zona: null })}
        />
        <SelectField
          label="Zona"
          value={zona}
          placeholder="Todas"
          disabled={!municipality}
          options={(municipality?.zonas ?? []).map((z) => ({ value: z, label: `Zona ${pad(z, 4)}` }))}
          onChange={(value) => update({ zona: value })}
        />
      </form>

      {municipalities.error && <ErrorMessage error={municipalities.error} />}
      {!municipio && <Empty>Escolha a UF e o município para listar as seções.</Empty>}
      {municipio && sections.isPending && <Loading label="Carregando seções…" />}
      {sections.error && <ErrorMessage error={sections.error} onRetry={() => void sections.refetch()} />}
      {sections.data && event && uf && municipio && (
        <section aria-labelledby="secoes-titulo">
          <div className="section-heading">
            <h2 id="secoes-titulo">
              {municipality?.nome ?? `Município ${municipio}`} · {formatInt(sections.data.total)} seções
            </h2>
          </div>
          {sections.data.total === 0 ? (
            <Empty>Nenhuma seção com arquivos publicados.</Empty>
          ) : (
            <ZoneGroups pleito={event.pleito} uf={uf} sections={sections.data.secoes} />
          )}
        </section>
      )}
    </>
  );
}

function ZoneGroups({
  pleito,
  uf,
  sections,
}: {
  pleito: number;
  uf: string;
  sections: { municipio: number; zona: number; secao: number }[];
}) {
  const zones = new Map<number, number[]>();
  for (const s of sections) zones.set(s.zona, [...(zones.get(s.zona) ?? []), s.secao]);
  return (
    <>
      {[...zones.entries()].map(([zona, numbers]) => (
        <div key={zona} className="card">
          <h3 className="card__title">
            Zona {pad(zona, 4)} <span className="muted">· {numbers.length} seções</span>
          </h3>
          <ul className="section-grid">
            {numbers.map((secao) => (
              <li key={secao}>
                <Link
                  className="section-chip"
                  to={`/secoes/${pleito}/${uf}/${sections[0]?.municipio}/${zona}/${secao}`}
                  aria-label={`Seção ${secao}, zona ${zona}`}
                >
                  {pad(secao, 4)}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </>
  );
}
