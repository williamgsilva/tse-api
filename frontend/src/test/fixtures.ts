import type { FeatureCollection, Geometry } from "geojson";

import type { SubdivisionResult, VotingEvent } from "../api/types";

function square(x: number, y: number, properties: Record<string, unknown>) {
  return {
    type: "Feature" as const,
    properties,
    geometry: {
      type: "Polygon" as const,
      coordinates: [
        [
          [x, y],
          [x + 1, y],
          [x + 1, y + 1],
          [x, y + 1],
          [x, y],
        ],
      ],
    },
  };
}

export const BRAZIL: FeatureCollection<Geometry, Record<string, unknown>> = {
  type: "FeatureCollection",
  features: [
    square(-70, -10, { uf: "ac", regiao: "norte", codigo_ibge: 12 }),
    square(-47, -23, { uf: "sp", regiao: "sudeste", codigo_ibge: 35 }),
  ],
};

export const ACRE: FeatureCollection<Geometry, Record<string, unknown>> = {
  type: "FeatureCollection",
  features: [square(-70, -10, { codigo_ibge: 1200393 }), square(-69, -10, { codigo_ibge: 1200203 })],
};

export const EVENTS = [
  {
    pleito: 3220,
    ciclo: "ele2026",
    ano: 2026,
    data: "2026-10-04",
    eleicoes: [
      {
        codigo: 6257,
        nome: "Eleição Ordinária Federal - 2026 1º Turno",
        turno: 1,
        tipo: 8,
        pleito: 3220,
        ciclo: "ele2026",
        ano: 2026,
        data: "2026-10-04",
        codigo_segundo_turno: 6258,
        cargos: [{ codigo: 1, nome: "Presidente", tipo: "majoritario", abrangencias: ["br"] }],
      },
      {
        codigo: 6259,
        nome: "Eleição Ordinária Estadual - 2026 1º Turno",
        turno: 1,
        tipo: 1,
        pleito: 3220,
        ciclo: "ele2026",
        ano: 2026,
        data: "2026-10-04",
        codigo_segundo_turno: 6260,
        cargos: [{ codigo: 3, nome: "Governador", tipo: "majoritario", abrangencias: ["br"] }],
      },
    ],
  },
] as VotingEvent[];

const totals = (eleitorado: number, comparecimento: number) => ({
  eleitorado: {
    total: eleitorado,
    comparecimento,
    abstencao: eleitorado - comparecimento,
    percentual_comparecimento: (100 * comparecimento) / eleitorado,
    percentual_abstencao: (100 * (eleitorado - comparecimento)) / eleitorado,
  },
  votos: {
    total: comparecimento,
    validos: comparecimento - 10,
    nominais: null,
    legenda: null,
    brancos: 4,
    nulos: 6,
    percentual_brancos: null,
    percentual_nulos: null,
  },
});

const candidate = (numero: number, nome: string, partido: string, votos: number, percentual: number) => ({
  numero,
  nome_urna: nome,
  partido,
  votos,
  percentual,
  eleito: false,
  situacao: null,
});

export const STATES: SubdivisionResult[] = [
  {
    tipo_abrangencia: "uf",
    codigo: "ac",
    codigo_ibge: 12,
    nome: "AC",
    totalizacao_finalizada: true,
    totais: totals(100, 80),
    candidatos: [candidate(22, "FLAVIO BOLSONARO", "PL", 50, 71.4), candidate(13, "LULA", "PT", 20, 28.6)],
  },
  {
    tipo_abrangencia: "uf",
    codigo: "sp",
    codigo_ibge: 35,
    nome: "SP",
    totalizacao_finalizada: true,
    totais: totals(1000, 900),
    candidatos: [candidate(13, "LULA", "PT", 500, 56.2), candidate(22, "FLAVIO BOLSONARO", "PL", 390, 43.8)],
  },
];

export const ACRE_MUNICIPALITIES: SubdivisionResult[] = [
  {
    ...(STATES[0] as SubdivisionResult),
    tipo_abrangencia: "mu",
    codigo: "1066",
    codigo_ibge: 1200393,
    nome: "PORTO WALTER",
  },
  {
    ...(STATES[0] as SubdivisionResult),
    tipo_abrangencia: "mu",
    codigo: "1074",
    codigo_ibge: 1200203,
    nome: "CRUZEIRO DO SUL",
    candidatos: [candidate(13, "LULA", "PT", 30, 60), candidate(22, "FLAVIO BOLSONARO", "PL", 20, 40)],
  },
];
