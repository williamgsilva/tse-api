import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";
import { mockApi, renderAt } from "./test/render";

describe("App", () => {
  it("renderiza o layout com navegação e a rota de dados abertos", async () => {
    mockApi({ "/v1/dados-abertos/importacoes": [] });
    renderAt(<App />, "/dados-abertos");
    expect(screen.getByRole("navigation", { name: "Principal" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Dados abertos" })).toHaveClass("active");
    expect(await screen.findByRole("heading", { level: 1, name: "Dados abertos" })).toBeInTheDocument();
  });

  it("mostra página não encontrada", () => {
    renderAt(<App />, "/rota/inexistente");
    expect(screen.getByRole("heading", { name: "Página não encontrada" })).toBeInTheDocument();
  });
});
