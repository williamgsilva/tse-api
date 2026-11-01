import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TimelineChart } from "./TimelineChart";

const BUCKETS = [
  { inicio: "08:00", votos: 30, por_habilitacao: { biometria: 20, ano_nascimento: 6, sem_biometria: 4 } },
  { inicio: "08:15", votos: 10, por_habilitacao: { biometria: 10 } },
  { inicio: "17:00", votos: 5, por_habilitacao: { sem_biometria: 5 } },
];

describe("TimelineChart", () => {
  it("desenha barras empilhadas, legenda, linha de corte e tabela", () => {
    const { container } = render(<TimelineChart buckets={BUCKETS} marker="17:00" title="Votos" />);
    expect(container.querySelectorAll(".chart__fill")).toHaveLength(5);
    expect(screen.getByRole("list", { name: "Legenda" })).toHaveTextContent("Biometria");
    expect(container.querySelector(".chart__marker")).not.toBeNull();
    expect(screen.getByText("08h")).toBeInTheDocument();
    expect(screen.getAllByRole("row")).toHaveLength(4);
  });

  it("mostra o detalhamento ao passar o mouse", () => {
    const { container } = render(<TimelineChart buckets={BUCKETS} title="Votos" />);
    const bar = container.querySelector(".chart__bar");
    expect(bar).not.toBeNull();
    fireEvent.mouseEnter(bar as Element);
    expect(screen.getByRole("status")).toHaveTextContent("08:00 · 30 votos");
    expect(screen.getByRole("status")).toHaveTextContent("Ano de nascimento: 6");
    fireEvent.mouseLeave(bar as Element);
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("não desenha nada sem dados", () => {
    const { container } = render(<TimelineChart buckets={[]} title="Votos" />);
    expect(container).toBeEmptyDOMElement();
  });
});
