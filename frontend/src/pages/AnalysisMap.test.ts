import { describe, expect, it } from "vitest";

import { lateShareByMunicipality } from "./AnalysisPage";

describe("lateShareByMunicipality", () => {
  it("calcula a fatia de votos a partir do corte por município", () => {
    const shares = lateShareByMunicipality(
      [
        { grupo: { municipio: 1 }, inicio: "16:45", votos: 90 },
        { grupo: { municipio: 1 }, inicio: "17:00", votos: 10 },
        { grupo: { municipio: 2 }, inicio: "08:00", votos: 5 },
        { grupo: {}, inicio: "17:00", votos: 5 },
      ],
      "17:00",
    );
    expect(Object.fromEntries(shares)).toEqual({ 1: 10, 2: 0 });
  });
});
