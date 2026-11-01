import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { mockApi, renderAt } from "../test/render";
import { AggregateTable, OpenDataPage } from "./OpenDataPage";

describe("OpenDataPage", () => {
  it("lista importações e consulta a votação agrupada", async () => {
    const fetch = mockApi({
      "/v1/dados-abertos/importacoes": [
        { ano: 2026, turno: 1, uf: "AC", arquivo: "bweb_1t_AC.csv", linhas: 258052, secoes: 2270 },
      ],
      "/v1/dados-abertos/2026/1/votacao/1": [
        { uf: "AC", tipo: "Nominal", numero: 22, nome: "FLAVIO BOLSONARO", partido: "PL", votos: 302807 },
      ],
    });
    renderAt(<OpenDataPage />);
    expect(await screen.findByText("258.052")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Agrupar"), "uf");
    await userEvent.click(screen.getByRole("button", { name: "Consultar" }));
    expect(await screen.findByText("302.807")).toBeInTheDocument();
    const lastUrl = String(fetch.mock.calls.at(-1)?.[0]);
    expect(lastUrl).toContain("agrupar=uf");
    expect(lastUrl).toContain("limit=500");
  });

  it("orienta a importar quando a base está vazia", async () => {
    mockApi({ "/v1/dados-abertos/importacoes": [] });
    renderAt(<OpenDataPage />);
    expect(await screen.findByText(/Nada importado ainda/)).toBeInTheDocument();
  });

  it("tabela agregada vazia", () => {
    renderAt(<AggregateTable rows={[]} grouping="votavel" />);
    expect(screen.getByText(/Nenhum voto encontrado/)).toBeInTheDocument();
  });
});
