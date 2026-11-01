import { useQuery } from "@tanstack/react-query";

import { api, type AnalysisQuery } from "./client";
import type { Election, Grouping } from "./types";

// Dados publicados pelo TSE quase não mudam depois da totalização: cache longo no cliente.
const STALE = 10 * 60 * 1000;

export function useVotingEvents(ano: number) {
  return useQuery({
    queryKey: ["voting-events", ano],
    queryFn: ({ signal }) => api.votingEvents(ano, signal),
    staleTime: STALE,
  });
}

/** Eleições ordinárias primeiro (as suplementares e consultas vêm depois). */
export function useElections(ano: number) {
  const query = useVotingEvents(ano);
  const elections: Election[] = (query.data ?? [])
    .flatMap((event) => event.eleicoes)
    .sort(
      (a, b) =>
        Number(b.nome.includes("Ordinária")) - Number(a.nome.includes("Ordinária")) || a.codigo - b.codigo,
    );
  return { ...query, elections };
}

export function useMunicipalities(eleicao: number | null, uf: string | null) {
  return useQuery({
    queryKey: ["municipalities", eleicao, uf],
    queryFn: ({ signal }) => api.municipalities(eleicao as number, uf as string, signal),
    enabled: eleicao !== null && uf !== null && uf !== "br",
    staleTime: STALE,
  });
}

export function useResult(
  eleicao: number | null,
  uf: string | null,
  cargo: number | null,
  municipio: number | null,
) {
  return useQuery({
    queryKey: ["result", eleicao, uf, cargo, municipio],
    queryFn: ({ signal }) => api.result(eleicao as number, uf as string, cargo as number, municipio, signal),
    enabled: eleicao !== null && uf !== null && cargo !== null,
    staleTime: STALE,
  });
}

export function useSections(
  pleito: number | null,
  uf: string | null,
  municipio: number | null,
  zona: number | null,
) {
  return useQuery({
    queryKey: ["sections", pleito, uf, municipio, zona],
    queryFn: ({ signal }) => api.sections(pleito as number, uf as string, municipio as number, zona, signal),
    enabled: pleito !== null && uf !== null && municipio !== null,
    staleTime: STALE,
  });
}

export function useBallot(pleito: number, uf: string, municipio: number, zona: number, secao: number) {
  return useQuery({
    queryKey: ["ballot", pleito, uf, municipio, zona, secao],
    queryFn: ({ signal }) => api.ballot(pleito, uf, municipio, zona, secao, signal),
    staleTime: Infinity,
  });
}

export function useSectionStatus(pleito: number, uf: string, municipio: number, zona: number, secao: number) {
  return useQuery({
    queryKey: ["section-status", pleito, uf, municipio, zona, secao],
    queryFn: ({ signal }) => api.sectionStatus(pleito, uf, municipio, zona, secao, signal),
    staleTime: STALE,
  });
}

export function useImports() {
  return useQuery({ queryKey: ["imports"], queryFn: ({ signal }) => api.imports(signal) });
}

export interface AggregateParams {
  ano: number;
  turno: number;
  cargo: number;
  agrupar: Grouping;
  uf?: string;
  municipio?: number | null;
  zona?: number | null;
  votavel?: number | null;
  limit?: number;
}

export function useAggregate(params: AggregateParams | null) {
  return useQuery({
    queryKey: ["aggregate", params],
    queryFn: ({ signal }) => api.aggregate(params as AggregateParams, signal),
    enabled: params !== null,
  });
}

export function useSectionTimeline(
  pleito: number,
  uf: string,
  municipio: number,
  zona: number,
  secao: number,
  apos: string,
) {
  return useQuery({
    queryKey: ["section-timeline", pleito, uf, municipio, zona, secao, apos],
    queryFn: ({ signal }) => api.sectionTimeline(pleito, uf, municipio, zona, secao, apos, signal),
    staleTime: Infinity,
  });
}

export interface AnalysisParams {
  turno: number;
  cargo: number;
  query: AnalysisQuery;
}

const ANALYSIS_YEAR = 2026;

export function useTurnout(params: AnalysisParams | null) {
  return useQuery({
    queryKey: ["turnout", params],
    queryFn: ({ signal }) =>
      api.turnout(ANALYSIS_YEAR, (params as AnalysisParams).turno, (params as AnalysisParams).query, signal),
    enabled: params !== null,
  });
}

export function useTimeline(params: AnalysisParams | null) {
  return useQuery({
    queryKey: ["timeline", params?.turno, params?.query.uf, params?.query.municipio, params?.query.zona],
    queryFn: ({ signal }) => {
      const { turno, query } = params as AnalysisParams;
      return api.timeline(
        ANALYSIS_YEAR,
        turno,
        { uf: query.uf, municipio: query.municipio, zona: query.zona, intervalo: 15 },
        signal,
      );
    },
    enabled: params !== null,
  });
}

export function useLateVotes(params: AnalysisParams | null) {
  return useQuery({
    queryKey: ["late-votes", params],
    queryFn: ({ signal }) => {
      const { turno, cargo, query } = params as AnalysisParams;
      return api.lateVotes(ANALYSIS_YEAR, turno, cargo, { ...query, agrupar: "total", limit: 50 }, signal);
    },
    enabled: params !== null,
  });
}

// Malhas e resultados por subdivisão quase nunca mudam depois da totalização.
const LONG = 60 * 60 * 1000;

export function useMesh(scope: string | null) {
  return useQuery({
    queryKey: ["mesh", scope],
    queryFn: ({ signal }) => api.mesh(scope as string, signal),
    enabled: scope !== null,
    staleTime: Infinity,
  });
}

export function useSubdivisions(eleicao: number | null, uf: string | null, cargo: number | null, limite = 3) {
  return useQuery({
    queryKey: ["subdivisions", eleicao, uf, cargo, limite],
    queryFn: ({ signal }) =>
      api.subdivisions(eleicao as number, uf as string, cargo as number, limite, signal),
    enabled: eleicao !== null && uf !== null && cargo !== null,
    staleTime: LONG,
  });
}

export function useMunicipalTurnout(turno: number, uf: string | null) {
  return useQuery({
    queryKey: ["turnout-municipal", turno, uf],
    queryFn: ({ signal }) =>
      api.turnout(ANALYSIS_YEAR, turno, { agrupar: "municipio", uf: uf as string, limit: 10000 }, signal),
    enabled: uf !== null,
  });
}

export function useMunicipalTimeline(turno: number, uf: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ["timeline-municipal", turno, uf],
    queryFn: ({ signal }) =>
      api.timeline(ANALYSIS_YEAR, turno, { agrupar: "municipio", uf: uf as string, intervalo: 15 }, signal),
    enabled: uf !== null && enabled,
  });
}
