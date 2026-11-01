import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { mockApi, renderAt } from "../test/render";
import { AnalysisPage, groupLabel, TurnoutView } from "./AnalysisPage";

const TOTAL = {
  grupo: {},
  secoes: 2270,
  aptos: 613742,
  comparecimento: 488330,
  abstencoes: 125412,
  percentual_comparecimento: 79.566,
  habilitados_biometria: 446083,
  habilitados_ano_nascimento: 24369,
  sem_biometria: 17878,
  secoes_com_arquivos_urna: 2270,
  primeira_abertura: "2026-10-04T08:00:01",
  ultimo_encerramento: "2026-10-04T19:49:34",
};

const LATE = {
  apos: "17:00",
  metodo: "ESTIMATIVA. O voto é secreto.",
  resumo: { secoes: 2270, comparecimento: 488330, votos_apos: 8441, secoes_sem_fuso: 0 },
  votaveis: [
    {
      grupo: {},
      tipo: "Nominal",
      numero: 22,
      nome: "FLAVIO BOLSONARO",
      partido: "PL",
      votos_nas_secoes: 302807,
      votos_apos_estimados: 5006.23,
    },
  ],
};

describe("AnalysisPage", () => {
  it("consulta comparecimento, horários e votos após 17h", async () => {
    const fetch = mockApi({
      "/v1/dados-abertos/2026/1/comparecimento": [TOTAL],
      "/v1/dados-abertos/2026/1/horarios": [
        { grupo: {}, inicio: "17:00", votos: 7405, por_habilitacao: { biometria: 6719 } },
      ],
      "/v1/dados-abertos/2026/1/votos-apos/1": LATE,
    });
    renderAt(<AnalysisPage />);
    await userEvent.click(screen.getByRole("button", { name: "Analisar" }));

    expect(await screen.findByText("488.330")).toBeInTheDocument();
    expect(screen.getByText("446.083")).toBeInTheDocument();
    expect(await screen.findByText("8.441")).toBeInTheDocument();
    expect(screen.getByText("5.006")).toBeInTheDocument();
    expect(screen.getByText("Estimativa, não contagem")).toBeInTheDocument();
    expect(await screen.findByRole("img", { name: /a cada 15 minutos/ })).toBeInTheDocument();
    const urls = fetch.mock.calls.map((c) => String(c[0]));
    expect(urls.some((u) => u.includes("/votos-apos/1?") && u.includes("apos=17%3A00"))).toBe(true);
  });

  it("orienta a importar o pacote de urnas quando não há horários", async () => {
    mockApi(
      {
        "/v1/dados-abertos/2026/1/comparecimento": [
          { ...TOTAL, secoes_com_arquivos_urna: 0, sem_biometria: null },
        ],
        "/v1/dados-abertos/2026/1/horarios": { title: "Base", status: 503, detail: "nenhum pacote" },
        "/v1/dados-abertos/2026/1/votos-apos/1": {
          title: "Base",
          status: 503,
          detail: "nenhum pacote de urnas",
        },
      },
      { "/v1/dados-abertos/2026/1/horarios": 503, "/v1/dados-abertos/2026/1/votos-apos/1": 503 },
    );
    renderAt(<AnalysisPage />);
    await userEvent.click(screen.getByRole("button", { name: "Analisar" }));
    expect(await screen.findByText(/Os horários vêm do pacote de arquivos de urna/)).toBeInTheDocument();
    expect(await screen.findByText("nenhum pacote de urnas")).toBeInTheDocument();
    expect(screen.getByText(/Biometria detalhada em 0 de 2.270 seções/)).toBeInTheDocument();
  });

  it("tabela agrupada e rótulos de grupo", () => {
    renderAt(
      <TurnoutView
        rows={[
          { ...TOTAL, grupo: { uf: "AC", municipio: 1007, nome_municipio: "BUJARI" } },
          { ...TOTAL, grupo: { uf: "AC", municipio: 1015, nome_municipio: "CAPIXABA" } },
        ]}
      />,
    );
    expect(screen.getByRole("table", { name: "Comparecimento agrupado" })).toHaveTextContent("AC · BUJARI");
    expect(groupLabel({ uf: "AC", municipio: 1, zona: 4, local: 1031, secao: 77 })).toBe(
      "AC · Município 1 · Zona 0004 · Local 1031 · Seção 0077",
    );
    expect(groupLabel({})).toBe("Total");
  });
});
