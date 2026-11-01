import { describe, expect, it } from "vitest";

import { EVENTS, STATES } from "../test/fixtures";
import { colorScale, OTHER, sequentialColor, SERIES } from "./colors";
import { aggregate, leader, leadersCount, officesOfRound, partyOrder, turnoutPercent } from "./results";

describe("results", () => {
  it("lista os cargos das eleições ordinárias do turno", () => {
    const offices = officesOfRound(EVENTS, 1);
    expect(offices.map((o) => [o.codigo, o.eleicao.codigo])).toEqual([
      [1, 6257],
      [3, 6259],
    ]);
    expect(officesOfRound(EVENTS, 2)).toEqual([]);
  });

  it("ordena partidos pelos votos somados e conta líderes", () => {
    expect(partyOrder(STATES)).toEqual(["PT", "PL"]);
    expect(leadersCount(STATES)).toEqual([
      { partido: "PL", areas: 1 },
      { partido: "PT", areas: 1 },
    ]);
    expect(leader(STATES[1])?.nome_urna).toBe("LULA");
  });

  it("soma estados de uma região", () => {
    const { candidates, totals } = aggregate(STATES);
    expect(candidates.map((c) => [c.nome_urna, c.votos])).toEqual([
      ["LULA", 520],
      ["FLAVIO BOLSONARO", 440],
    ]);
    expect(totals.eleitorado?.total).toBe(1100);
    expect(totals.eleitorado?.comparecimento).toBe(980);
    expect(totals.votos?.validos).toBe(960);
    expect(candidates[0]?.percentual).toBeCloseTo((100 * 520) / 960);
    expect(turnoutPercent(STATES[0])).toBe(80);
  });
});

describe("colors", () => {
  it("cor segue a ordem recebida e o resto vira Outros", () => {
    const color = colorScale(["PT", "PL"]);
    expect(color("PT")).toBe(SERIES[0]);
    expect(color("PL")).toBe(SERIES[1]);
    expect(color("NOVO")).toBe(OTHER);
    expect(color(null)).toBe("var(--series-empty)");
  });

  it("escala sequencial", () => {
    expect(sequentialColor(0, 0, 100)).toBe("var(--seq-1)");
    expect(sequentialColor(100, 0, 100)).toBe("var(--seq-7)");
    expect(sequentialColor(null, 0, 100)).toBe("var(--series-empty)");
  });
});
