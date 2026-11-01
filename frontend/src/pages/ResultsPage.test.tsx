import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { mockApi, renderAt } from "../test/render";
import { ResultsPage } from "./ResultsPage";

const EVENTS = [
  {
    pleito: 3221,
    ciclo: "ele2026",
    ano: 2026,
    data: "2026-10-25",
    eleicoes: [
      {
        codigo: 6258,
        nome: "Eleição Ordinária Federal - 2026 2º Turno",
        turno: 2,
        tipo: 8,
        pleito: 3221,
        ciclo: "ele2026",
        ano: 2026,
        data: "2026-10-25",
        codigo_segundo_turno: null,
        cargos: [{ codigo: 1, nome: "Presidente", tipo: "majoritario", abrangencias: ["br"] }],
      },
    ],
  },
];

const candidate = (numero: number, nome: string, votos: number, percentual: number, eleito: boolean) => ({
  numero,
  nome,
  nome_urna: nome,
  partido: numero === 13 ? "PT" : "PL",
  numero_partido: numero,
  agremiacao: null,
  composicao: null,
  votos,
  percentual,
  eleito,
  situacao: eleito ? "Eleito" : "Não eleito",
  destinacao_votos: "Válido",
  vices_suplentes: [],
});

const RESULT = {
  eleicao: 6258,
  turno: 2,
  tipo_abrangencia: "br",
  codigo_abrangencia: "br",
  atualizado_em: "2026-10-25T23:26:38",
  totalizacao_finalizada: true,
  totais: {
    secoes: { total: 10, totalizadas: 10, percentual_totalizadas: 100 },
    eleitorado: null,
    votos: {
      total: 100,
      validos: 90,
      nominais: 90,
      legenda: 0,
      brancos: 4,
      nulos: 6,
      percentual_brancos: 4,
      percentual_nulos: 6,
    },
  },
  cargos: [
    {
      codigo: 1,
      nome: "Presidente",
      vagas: 1,
      quociente_eleitoral: null,
      candidatos: [
        candidate(13, "LULA", 64256232, 51.79, true),
        candidate(22, "FLAVIO BOLSONARO", 59826041, 48.21, false),
      ],
    },
  ],
};

describe("ResultsPage", () => {
  it("mostra o resultado nacional do 2º turno por padrão", async () => {
    mockApi({ "/v1/eleicoes": EVENTS, "/v1/eleicoes/6258/resultados/br/1": RESULT });
    renderAt(<ResultsPage />);

    const table = await screen.findByRole("table", { name: "Votos por candidatura" });
    const rows = within(table).getAllByRole("row");
    expect(rows[1]).toHaveTextContent("LULA");
    expect(rows[1]).toHaveTextContent("64.256.232");
    expect(rows[1]).toHaveTextContent("Eleito");
    expect(screen.getByRole("heading", { name: /Presidente · Brasil/ })).toBeInTheDocument();
    expect(screen.getByLabelText("Abrangência")).toHaveValue("br");
  });

  it("mostra o erro da API", async () => {
    mockApi({ "/v1/eleicoes": EVENTS });
    renderAt(<ResultsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Não encontrado");
  });

  it("filtra candidaturas pela busca", async () => {
    const many = Array.from({ length: 12 }, (_, i) =>
      candidate(1000 + i, `CANDIDATO ${i}`, 100 - i, 1, false),
    );
    mockApi({
      "/v1/eleicoes": EVENTS,
      "/v1/eleicoes/6258/resultados/br/1": { ...RESULT, cargos: [{ ...RESULT.cargos[0], candidatos: many }] },
    });
    renderAt(<ResultsPage />);
    await userEvent.type(await screen.findByLabelText("Buscar candidato"), "CANDIDATO 11");
    const table = screen.getByRole("table", { name: "Votos por candidatura" });
    expect(within(table).getAllByRole("row")).toHaveLength(2);
  });
});
