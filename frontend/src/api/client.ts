import type { FeatureCollection, Geometry } from "geojson";

import type {
  BallotReport,
  ElectionResult,
  Grouping,
  ImportedDataset,
  LateVotesReport,
  Municipality,
  Problem,
  SectionPage,
  SectionStatus,
  SectionVoteTimeline,
  SubdivisionResult,
  TimelinePoint,
  TurnoutAggregate,
  VoteAggregate,
  VotingEvent,
} from "./types";

export const API_PREFIX = "/v1";

/** Erro da API no formato Problem Details (RFC 9457). */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly title: string,
    readonly detail: string | null,
    readonly traceId: string | null,
  ) {
    super(detail ?? title);
    this.name = "ApiError";
  }
}

type Query = Record<string, string | number | null | undefined>;

/** Filtros e agrupamento das análises sobre a base local (comparecimento, horários, votos após). */
export type AnalysisQuery = {
  agrupar?: Grouping;
  uf?: string;
  municipio?: number | null;
  zona?: number | null;
  intervalo?: number;
  apos?: string;
  encerramento_apos?: string;
  limit?: number;
};

export function buildUrl(path: string, query: Query = {}): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== null && value !== undefined && value !== "") params.set(key, String(value));
  }
  const qs = params.toString();
  return `${API_PREFIX}${path}${qs ? `?${qs}` : ""}`;
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const problem = (await response.json()) as Partial<Problem>;
    return new ApiError(
      response.status,
      problem.title ?? response.statusText,
      problem.detail ?? null,
      problem.traceId ?? null,
    );
  } catch {
    return new ApiError(response.status, response.statusText || "Erro na API", null, null);
  }
}

export async function getJson<T>(path: string, query?: Query, signal?: AbortSignal): Promise<T> {
  const response = await fetch(buildUrl(path, query), { signal, headers: { Accept: "application/json" } });
  if (!response.ok) throw await toApiError(response);
  return (await response.json()) as T;
}

const sectionPath = (pleito: number, uf: string, municipio: number, zona: number, secao: number) =>
  `/pleitos/${pleito}/secoes/${uf}/${municipio}/${zona}/${secao}`;

export const api = {
  votingEvents: (ano: number, signal?: AbortSignal) => getJson<VotingEvent[]>("/eleicoes", { ano }, signal),

  municipalities: (eleicao: number, uf: string, signal?: AbortSignal) =>
    getJson<Municipality[]>(`/eleicoes/${eleicao}/municipios`, { uf }, signal),

  result: (eleicao: number, uf: string, cargo: number, municipio?: number | null, signal?: AbortSignal) =>
    getJson<ElectionResult>(`/eleicoes/${eleicao}/resultados/${uf}/${cargo}`, { municipio }, signal),

  subdivisions: (eleicao: number, uf: string, cargo: number, limite: number, signal?: AbortSignal) =>
    getJson<SubdivisionResult[]>(
      `/eleicoes/${eleicao}/resultados/${uf}/${cargo}/subdivisoes`,
      { limite },
      signal,
    ),

  /** ``br`` = Brasil por UF; sigla da UF = municípios da UF. */
  mesh: (scope: string, signal?: AbortSignal) =>
    getJson<FeatureCollection<Geometry, Record<string, unknown>>>(
      `/mapas/${scope === "br" ? "brasil" : scope}`,
      undefined,
      signal,
    ),

  sections: (pleito: number, uf: string, municipio: number, zona: number | null, signal?: AbortSignal) =>
    getJson<SectionPage>(`/pleitos/${pleito}/secoes/${uf}`, { municipio, zona, limit: 10000 }, signal),

  sectionStatus: (
    pleito: number,
    uf: string,
    municipio: number,
    zona: number,
    secao: number,
    signal?: AbortSignal,
  ) => getJson<SectionStatus>(sectionPath(pleito, uf, municipio, zona, secao), undefined, signal),

  ballot: (
    pleito: number,
    uf: string,
    municipio: number,
    zona: number,
    secao: number,
    signal?: AbortSignal,
  ) => getJson<BallotReport>(`${sectionPath(pleito, uf, municipio, zona, secao)}/boletim`, undefined, signal),

  sectionTimeline: (
    pleito: number,
    uf: string,
    municipio: number,
    zona: number,
    secao: number,
    apos: string,
    signal?: AbortSignal,
  ) =>
    getJson<SectionVoteTimeline>(
      `${sectionPath(pleito, uf, municipio, zona, secao)}/horarios`,
      { apos },
      signal,
    ),

  turnout: (ano: number, turno: number, query: AnalysisQuery, signal?: AbortSignal) =>
    getJson<TurnoutAggregate[]>(`/dados-abertos/${ano}/${turno}/comparecimento`, query, signal),

  timeline: (ano: number, turno: number, query: AnalysisQuery, signal?: AbortSignal) =>
    getJson<TimelinePoint[]>(`/dados-abertos/${ano}/${turno}/horarios`, query, signal),

  lateVotes: (ano: number, turno: number, cargo: number, query: AnalysisQuery, signal?: AbortSignal) =>
    getJson<LateVotesReport>(`/dados-abertos/${ano}/${turno}/votos-apos/${cargo}`, query, signal),

  urnFileUrl: (pleito: number, uf: string, municipio: number, zona: number, secao: number, tipo: string) =>
    buildUrl(`${sectionPath(pleito, uf, municipio, zona, secao)}/arquivos/${tipo}`),

  imports: (signal?: AbortSignal) =>
    getJson<ImportedDataset[]>("/dados-abertos/importacoes", undefined, signal),

  aggregate: (
    params: {
      ano: number;
      turno: number;
      cargo: number;
      agrupar: Grouping;
      uf?: string;
      municipio?: number | null;
      zona?: number | null;
      votavel?: number | null;
      limit?: number;
    },
    signal?: AbortSignal,
  ) => {
    const { ano, turno, cargo, ...query } = params;
    return getJson<VoteAggregate[]>(`/dados-abertos/${ano}/${turno}/votacao/${cargo}`, query, signal);
  },
};
