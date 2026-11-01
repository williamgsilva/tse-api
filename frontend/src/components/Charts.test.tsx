import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { applyTheme, readTheme } from "../lib/theme";
import { Composition, HBarChart, Segmented } from "./Charts";
import { ThemeToggle } from "./ThemeToggle";

describe("Charts", () => {
  it("barras horizontais com valor e percentual diretos", () => {
    render(
      <HBarChart
        label="Candidatos"
        items={[
          { id: "13", label: "LULA", detail: "PT", value: 600, percent: 60, color: "red", badge: "eleito" },
          { id: "22", label: "FLAVIO", detail: "PL", value: 400, color: "blue" },
        ]}
      />,
    );
    const items = screen.getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("LULAPT eleito60060,00%");
    expect(items[1]).toHaveTextContent("40,00%");
  });

  it("composição em barra 100% com legenda", () => {
    render(
      <Composition
        label="Votos"
        parts={[
          { id: "a", label: "Válidos", value: 90, color: "red" },
          { id: "b", label: "Nulos", value: 10, color: "blue" },
        ]}
      />,
    );
    expect(screen.getAllByRole("listitem")[1]).toHaveTextContent("Nulos: 10 (10,00%)");
    const { container } = render(<Composition label="vazio" parts={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("controle segmentado é um grupo de rádio", async () => {
    const onChange = vi.fn();
    render(
      <Segmented
        label="Turno"
        value={1}
        options={[
          { value: 1, label: "1º" },
          { value: 2, label: "2º" },
        ]}
        onChange={onChange}
      />,
    );
    expect(screen.getByRole("group", { name: "Turno" })).toBeInTheDocument();
    await userEvent.click(screen.getByLabelText("2º"));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("seletor de tema grava a escolha", async () => {
    render(<ThemeToggle />);
    await userEvent.click(screen.getByRole("button", { name: "Tema escuro" }));
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");
    expect(readTheme()).toBe("dark");
    applyTheme("system");
    expect(document.documentElement).not.toHaveAttribute("data-theme");
  });
});
