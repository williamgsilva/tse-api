import type { Election, SubdivisionResult, Totals, VotingEvent } from "../api/types";

export type Candidate = SubdivisionResult["candidatos"][number];

/** Eleições ordinárias (federal e estadual) de um turno e o código da eleição de cada cargo. */
export function officesOfRound(events: VotingEvent[], turno: number) {
  const elections: Election[] = events
    .flatMap((e) => e.eleicoes)
    .filter((e) => e.turno === turno && e.nome.includes("Ordinária") && !e.nome.includes("Municipal"));
  const offices = new Map<number, { codigo: number; nome: string; eleicao: Election }>();
  for (const election of elections) {
    for (const office of election.cargos) {
      if (!offices.has(office.codigo))
        offices.set(office.codigo, { codigo: office.codigo, nome: office.nome, eleicao: election });
    }
  }
  return [...offices.values()].sort((a, b) => a.codigo - b.codigo);
}

/** Partidos ordenados pelo total de votos somado nas subdivisões (ordem estável para as cores). */
export function partyOrder(areas: SubdivisionResult[]): string[] {
  const votes = new Map<string, number>();
  for (const area of areas) {
    for (const c of area.candidatos) {
      if (c.partido) votes.set(c.partido, (votes.get(c.partido) ?? 0) + c.votos);
    }
  }
  return [...votes.entries()].sort((a, b) => b[1] - a[1]).map(([party]) => party);
}

export function leader(area: SubdivisionResult | undefined): Candidate | undefined {
  return area?.candidatos[0];
}

/** Quantas subdivisões cada partido lidera, do maior para o menor. */
export function leadersCount(areas: SubdivisionResult[]): { partido: string; areas: number }[] {
  const counts = new Map<string, number>();
  for (const area of areas) {
    const party = leader(area)?.partido;
    if (party) counts.set(party, (counts.get(party) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([partido, n]) => ({ partido, areas: n }))
    .sort((a, b) => b.areas - a.areas);
}

function add(a: number | null | undefined, b: number | null | undefined): number {
  return (a ?? 0) + (b ?? 0);
}

/** Soma várias subdivisões (ex.: as UFs de uma região): votos por candidato e totais. */
export function aggregate(areas: SubdivisionResult[]): { candidates: Candidate[]; totals: Totals } {
  const byNumber = new Map<string, Candidate>();
  let eleitorado = 0;
  let comparecimento = 0;
  let validos = 0;
  let brancos = 0;
  let nulos = 0;
  for (const area of areas) {
    for (const c of area.candidatos) {
      const id = `${c.numero}-${c.nome_urna}`;
      const current = byNumber.get(id);
      byNumber.set(id, { ...c, votos: add(current?.votos, c.votos), eleito: false, situacao: null });
    }
    eleitorado += area.totais.eleitorado?.total ?? 0;
    comparecimento += area.totais.eleitorado?.comparecimento ?? 0;
    validos += area.totais.votos?.validos ?? 0;
    brancos += area.totais.votos?.brancos ?? 0;
    nulos += area.totais.votos?.nulos ?? 0;
  }
  const candidates = [...byNumber.values()]
    .map((c) => ({ ...c, percentual: validos ? (100 * c.votos) / validos : null }))
    .sort((a, b) => b.votos - a.votos);
  return {
    candidates,
    totals: {
      eleitorado: {
        total: eleitorado,
        comparecimento,
        abstencao: eleitorado - comparecimento,
        percentual_comparecimento: eleitorado ? (100 * comparecimento) / eleitorado : null,
        percentual_abstencao: eleitorado ? (100 * (eleitorado - comparecimento)) / eleitorado : null,
      },
      votos: {
        total: validos + brancos + nulos,
        validos,
        nominais: null,
        legenda: null,
        brancos,
        nulos,
        percentual_brancos: null,
        percentual_nulos: null,
      },
    },
  };
}

export function turnoutPercent(area: SubdivisionResult | undefined): number | null {
  return area?.totais.eleitorado?.percentual_comparecimento ?? null;
}
