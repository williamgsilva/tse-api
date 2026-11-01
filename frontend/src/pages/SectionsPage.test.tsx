import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { mockApi, renderAt } from "../test/render";
import { SectionsPage } from "./SectionsPage";

const EVENTS = [
  {
    pleito: 3220,
    ciclo: "ele2026",
    ano: 2026,
    data: "2026-10-04",
    eleicoes: [{ codigo: 6257, nome: "Eleição Ordinária Federal - 2026 1º Turno", cargos: [] }],
  },
  {
    pleito: 3080,
    ciclo: "ele2024",
    ano: 2026,
    data: "2026-04-12",
    eleicoes: [{ codigo: 6120, nome: "Eleição Suplementar", cargos: [] }],
  },
];

describe("SectionsPage", () => {
  it("pede UF e município antes de listar", async () => {
    mockApi({ "/v1/eleicoes": EVENTS });
    renderAt(<SectionsPage />, "/secoes");
    expect(await screen.findByText(/Escolha a UF e o município/)).toBeInTheDocument();
    const turno = screen.getByLabelText("Turno");
    expect(within(turno).getAllByRole("option")).toHaveLength(1);
  });

  it("lista as seções do município agrupadas por zona com link para o boletim", async () => {
    mockApi({
      "/v1/eleicoes": EVENTS,
      "/v1/eleicoes/6257/municipios": [
        { uf: "ac", codigo: 1066, codigo_ibge: 1200393, nome: "PORTO WALTER", capital: false, zonas: [4] },
      ],
      "/v1/pleitos/3220/secoes/ac": {
        total: 2,
        proximo_cursor: null,
        secoes: [
          {
            uf: "ac",
            municipio: 1066,
            nome_municipio: "PORTO WALTER",
            zona: 4,
            secao: 77,
            atualizado_em: null,
          },
          {
            uf: "ac",
            municipio: 1066,
            nome_municipio: "PORTO WALTER",
            zona: 4,
            secao: 78,
            atualizado_em: null,
          },
        ],
      },
    });
    renderAt(<SectionsPage />, "/secoes?pleito=3220&uf=ac&municipio=1066");
    expect(await screen.findByRole("heading", { name: /PORTO WALTER · 2 seções/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Seção 77, zona 4" })).toHaveAttribute(
      "href",
      "/secoes/3220/ac/1066/4/77",
    );
  });
});
