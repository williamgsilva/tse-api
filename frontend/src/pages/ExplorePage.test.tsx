import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { SubdivisionResult } from "../api/types";
import { ACRE, ACRE_MUNICIPALITIES, BRAZIL, EVENTS, STATES } from "../test/fixtures";
import { mockApi, renderAt } from "../test/render";
import { ExplorePage } from "./ExplorePage";

const RESULT = {
  eleicao: 6257,
  turno: 1,
  tipo_abrangencia: "br",
  codigo_abrangencia: "br",
  atualizado_em: "2026-10-05T12:51:05",
  totalizacao_finalizada: true,
  totais: (STATES[1] as SubdivisionResult).totais,
  cargos: [
    {
      codigo: 1,
      nome: "Presidente",
      vagas: 1,
      quociente_eleitoral: null,
      candidatos: [
        {
          numero: 13,
          nome: "LUIZ",
          nome_urna: "LULA",
          partido: "PT",
          votos: 500,
          percentual: 56.2,
          eleito: false,
        },
      ],
    },
  ],
};

const ROUTES = {
  "/v1/eleicoes": EVENTS,
  "/v1/mapas/brasil": BRAZIL,
  "/v1/mapas/ac": ACRE,
  "/v1/eleicoes/6257/resultados/br/1/subdivisoes": STATES,
  "/v1/eleicoes/6257/resultados/ac/1/subdivisoes": ACRE_MUNICIPALITIES,
  "/v1/eleicoes/6257/resultados/br/1": RESULT,
  "/v1/eleicoes/6257/resultados/ac/1": RESULT,
  "/v1/eleicoes/6257/municipios": [
    { uf: "ac", codigo: 1074, codigo_ibge: 1200203, nome: "CRUZEIRO DO SUL", capital: false, zonas: [4, 8] },
  ],
};

describe("ExplorePage", () => {
  it("mostra o Brasil por estado com legenda de líderes e o resultado nacional", async () => {
    mockApi(ROUTES);
    renderAt(<ExplorePage />);
    expect(await screen.findByRole("button", { name: "São Paulo" })).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Legenda: partido do líder" })).toHaveTextContent("PT 1");
    expect(await screen.findByRole("list", { name: "Candidatos a Presidente" })).toHaveTextContent("LULA");
    expect(screen.getByText("Brasil", { selector: "[aria-current]" })).toBeInTheDocument();
  });

  it("navega por região, estado e município até as zonas", async () => {
    mockApi(ROUTES);
    renderAt(<ExplorePage />);
    await userEvent.click(await screen.findByRole("button", { name: "Norte" }));
    expect(await screen.findByRole("heading", { name: "Região Norte" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "São Paulo" })).toHaveClass("map__area--dimmed");

    await userEvent.click(screen.getByRole("button", { name: "Acre" }));
    const city = await screen.findByRole("button", { name: "CRUZEIRO DO SUL" });
    await userEvent.click(city);
    expect(await screen.findByRole("heading", { name: "CRUZEIRO DO SUL" })).toBeInTheDocument();
    const zones = await screen.findByRole("list", { name: "Zonas eleitorais" });
    expect(within(zones).getByRole("link", { name: "Zona 0004" })).toHaveAttribute(
      "href",
      "/secoes?pleito=3220&uf=ac&municipio=1074&zona=4",
    );
    const crumbs = screen.getByRole("navigation", { name: "Nível do mapa" });
    expect(crumbs).toHaveTextContent("BrasilNorteAcreCRUZEIRO DO SUL");
  });

  it("colore por comparecimento com legenda em gradiente", async () => {
    mockApi(ROUTES);
    renderAt(<ExplorePage />, "/?cor=comparecimento");
    expect(await screen.findByLabelText("Legenda: comparecimento")).toHaveTextContent("80,00%");
  });
});
