import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import { useBallot, useSectionStatus, useSectionTimeline } from "../api/hooks";
import type { BallotOffice, BallotReport, SectionStatus, SectionVoteTimeline } from "../api/types";
import { SelectField } from "../components/Field";
import { Stat } from "../components/Stat";
import { TimelineChart } from "../components/TimelineChart";
import { ErrorMessage, Loading } from "../components/Status";
import { VoteBar } from "../components/VoteBar";
import { CUTOFFS, formatDateTime, formatInt, pad, share, voteKindLabel } from "../lib/format";
import { ufName } from "../lib/ufs";

const FILE_LABELS: Record<string, string> = {
  bu: "Boletim de urna (BU)",
  rdv: "Registro digital do voto (RDV)",
  log: "Log da urna",
  vota: "Assinatura digital",
};

function useSectionParams() {
  const params = useParams();
  const toNumber = (key: string) => Number(params[key] ?? NaN);
  return {
    pleito: toNumber("pleito"),
    uf: (params.uf ?? "").toLowerCase(),
    municipio: toNumber("municipio"),
    zona: toNumber("zona"),
    secao: toNumber("secao"),
  };
}

export function BallotPage() {
  const { pleito, uf, municipio, zona, secao } = useSectionParams();
  const ballot = useBallot(pleito, uf, municipio, zona, secao);
  const status = useSectionStatus(pleito, uf, municipio, zona, secao);
  const back = `/secoes?pleito=${pleito}&uf=${uf}&municipio=${municipio}&zona=${zona}`;

  return (
    <>
      <nav aria-label="Trilha" className="breadcrumb">
        <Link to={back}>← Seções do município</Link>
      </nav>
      <header className="page__header">
        <h1>
          Seção {pad(secao, 4)} · Zona {pad(zona, 4)}
        </h1>
        <p className="lead">
          {ufName(uf)} · município {pad(municipio, 5)} (código TSE) · pleito {pleito}
        </p>
      </header>
      {ballot.isPending && <Loading label="Lendo o boletim de urna…" />}
      {ballot.error && <ErrorMessage error={ballot.error} onRetry={() => void ballot.refetch()} />}
      {ballot.data && <BallotView report={ballot.data} />}
      {ballot.data && (
        <SectionTimeline pleito={pleito} uf={uf} municipio={municipio} zona={zona} secao={secao} />
      )}
      {status.data && <UrnFiles status={status.data} />}
    </>
  );
}

function BallotView({ report }: { report: BallotReport }) {
  const eligible = report.eleicoes[0]?.aptos ?? 0;
  const breakdown = report.detalhamento_comparecimento;
  return (
    <>
      <dl className="stats">
        <Stat label="Eleitores aptos" value={formatInt(eligible)} />
        <Stat
          label="Comparecimento"
          value={formatInt(report.comparecimento)}
          detail={`${share(report.comparecimento, eligible).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}% dos aptos`}
        />
        <Stat label="Abertura" value={formatDateTime(report.votacao?.abertura)} />
        <Stat label="Encerramento" value={formatDateTime(report.votacao?.encerramento)} />
        {breakdown && (
          <Stat
            label="Habilitados por biometria"
            value={formatInt(breakdown.habilitados_biometria)}
            detail={`${formatInt(breakdown.habilitados_ano_nascimento)} por ano de nascimento · ${formatInt(breakdown.sem_biometria)} sem biometria`}
          />
        )}
      </dl>

      <details className="card">
        <summary className="card__title">Dados da urna</summary>
        <dl className="kv">
          <dt>Número interno</dt>
          <dd className="mono">{report.urna.numero_interno}</dd>
          <dt>Tipo</dt>
          <dd>{report.urna.tipo}</dd>
          <dt>Software de votação</dt>
          <dd>{report.urna.versao_votacao}</dd>
          <dt>Código de carga</dt>
          <dd className="mono">{report.urna.codigo_carga}</dd>
          <dt>Carga em</dt>
          <dd>{formatDateTime(report.urna.data_hora_carga)}</dd>
          <dt>Emissão do BU</dt>
          <dd>{formatDateTime(report.emitido_em)}</dd>
          <dt>Local de votação</dt>
          <dd className="mono">{report.secao.local}</dd>
          <dt>Arquivo</dt>
          <dd className="mono">{report.arquivo}</dd>
        </dl>
      </details>

      {report.eleicoes.map((election) => (
        <section key={election.eleicao} aria-labelledby={`eleicao-${election.eleicao}`}>
          <h2 id={`eleicao-${election.eleicao}`} className="section-heading">
            {election.nome ?? `Eleição ${election.eleicao}`}
          </h2>
          <div className="office-grid">
            {election.cargos
              .slice()
              .sort((a, b) => a.codigo - b.codigo)
              .map((office) => (
                <OfficeCard key={office.codigo} office={office} />
              ))}
          </div>
        </section>
      ))}
    </>
  );
}

export function OfficeCard({ office }: { office: BallotOffice }) {
  const total = Object.values(office.totais).reduce((sum, n) => sum + n, 0);
  const votes = office.votos.slice().sort((a, b) => b.quantidade - a.quantidade);
  return (
    <article className="card" aria-labelledby={`cargo-${office.codigo}`}>
      <h3 id={`cargo-${office.codigo}`} className="card__title">
        {office.nome ?? office.identificador}
      </h3>
      <p className="muted">
        {formatInt(office.totais.nominal)} nominais · {formatInt(office.totais.legenda)} legenda ·{" "}
        {formatInt(office.totais.branco)} brancos · {formatInt(office.totais.nulo)} nulos
      </p>
      <div className="table-wrap">
        <table className="table table--compact">
          <caption className="visually-hidden">Votos para {office.nome ?? office.identificador}</caption>
          <thead>
            <tr>
              <th scope="col">Votável</th>
              <th scope="col" className="num">
                Votos
              </th>
              <th scope="col">% da seção</th>
            </tr>
          </thead>
          <tbody>
            {votes.map((vote) => (
              <tr key={`${vote.tipo}-${vote.numero ?? ""}`}>
                <td>
                  {vote.tipo === "nominal" ? (
                    <>
                      <strong>{vote.nome ?? `Candidato ${vote.numero}`}</strong>
                      <span className="muted block">
                        {vote.numero} · {vote.sigla_partido ?? vote.partido}
                      </span>
                    </>
                  ) : vote.tipo === "legenda" ? (
                    <>
                      <strong>Legenda {vote.sigla_partido ?? vote.numero}</strong>
                      <span className="muted block">{vote.numero}</span>
                    </>
                  ) : (
                    <strong>{voteKindLabel(vote.tipo)}</strong>
                  )}
                </td>
                <td className="num">{formatInt(vote.quantidade)}</td>
                <td>
                  <VoteBar percent={share(vote.quantidade, total)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

function UrnFiles({ status }: { status: SectionStatus }) {
  const current = status.transmissoes.find((t) => t.vigente);
  if (!current) return null;
  return (
    <section className="card" aria-labelledby="arquivos-titulo">
      <h2 id="arquivos-titulo" className="card__title">
        Arquivos originais da urna
      </h2>
      <p className="muted">
        Situação: {status.situacao ?? "—"} · recebido em {formatDateTime(current.recebido_em)}
      </p>
      <ul className="file-list">
        {current.arquivos.map((file) => (
          <li key={file.nome}>
            <a
              href={api.urnFileUrl(
                status.pleito,
                status.uf,
                status.municipio,
                status.zona,
                status.secao,
                file.tipo,
              )}
            >
              {FILE_LABELS[file.tipo] ?? file.tipo}
            </a>
            <span className="muted mono"> {file.nome}</span>
            <a className="muted" href={file.url_tse} rel="noreferrer" target="_blank">
              (no TSE)
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}

function SectionTimeline(props: {
  pleito: number;
  uf: string;
  municipio: number;
  zona: number;
  secao: number;
}) {
  const [cutoff, setCutoff] = useState("17:00");
  const timeline = useSectionTimeline(
    props.pleito,
    props.uf,
    props.municipio,
    props.zona,
    props.secao,
    cutoff,
  );
  return (
    <section className="card" aria-labelledby="horarios-titulo">
      <h2 id="horarios-titulo" className="card__title">
        Votos por horário
      </h2>
      <p className="muted">
        Contados no log da urna. O log registra a hora de cada voto e como o eleitor foi habilitado, nunca o
        candidato escolhido.
      </p>
      {timeline.isPending && <Loading label="Lendo o log da urna…" />}
      {timeline.error && <ErrorMessage error={timeline.error} />}
      {timeline.data && <TimelineView data={timeline.data} cutoff={cutoff} onCutoff={setCutoff} />}
    </section>
  );
}

export function TimelineView({
  data,
  cutoff,
  onCutoff,
}: {
  data: SectionVoteTimeline;
  cutoff: string;
  onCutoff: (value: string) => void;
}) {
  const president = data.estimativa_por_cargo.find((c) => c.codigo === 1) ?? data.estimativa_por_cargo[0];
  const local = data.fonte_fuso === "desconhecido";
  return (
    <>
      <dl className="stats">
        <Stat
          label={`Votos a partir das ${cutoff}`}
          value={formatInt(data.votos_apos)}
          detail={`${share(data.votos_apos, data.comparecimento).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}% do comparecimento`}
        />
        <Stat label="Primeiro voto" value={formatDateTime(data.horarios.primeiro_voto)} />
        <Stat label="Último voto" value={formatDateTime(data.horarios.ultimo_voto)} />
      </dl>
      {local && (
        <p className="callout">Seção no exterior: horários no fuso local do país, não de Brasília.</p>
      )}
      <TimelineChart
        buckets={data.horarios.intervalos}
        marker={cutoff}
        title={`Votos a cada 15 minutos (horário ${local ? "local" : "de Brasília"})`}
      />
      <div className="card__toolbar">
        <SelectField
          label="Horário de corte (Brasília)"
          value={cutoff}
          options={CUTOFFS.map((c) => ({ value: c, label: c }))}
          onChange={(value) => onCutoff(value ?? "17:00")}
        />
      </div>
      {president && president.votos_tardios > 0 && (
        <>
          <div className="callout">
            <strong>Estimativa, não contagem</strong>O voto é secreto. Os {formatInt(president.votos_tardios)}{" "}
            votos dados a partir das {cutoff} foram distribuídos na mesma proporção dos votos da seção para{" "}
            {president.cargo ?? "o cargo"}.
          </div>
          <div className="table-wrap">
            <table className="table table--compact">
              <caption className="visually-hidden">Estimativa de votos a partir de {cutoff}</caption>
              <thead>
                <tr>
                  <th scope="col">Votável</th>
                  <th scope="col" className="num">
                    Votos na seção
                  </th>
                  <th scope="col" className="num">
                    Estimados após {cutoff}
                  </th>
                </tr>
              </thead>
              <tbody>
                {president.estimativas.map((e) => (
                  <tr key={`${e.tipo}-${e.numero ?? ""}`}>
                    <td>{e.nome ?? voteKindLabel(e.tipo)}</td>
                    <td className="num">{formatInt(e.votos_secao)}</td>
                    <td className="num">
                      {e.votos_tardios_estimados.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
