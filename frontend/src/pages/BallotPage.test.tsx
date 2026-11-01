import { screen, within } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { mockApi, renderAt } from "../test/render";
import { BallotPage } from "./BallotPage";

const BASE = "/v1/pleitos/3220/secoes/ac/1066/4/77";

const BALLOT = {
  arquivo: "o03220ac0106600040077-bu.dat",
  uf: "ac",
  fase: "oficial",
  gerado_em: "2026-10-04T15:44:47",
  emitido_em: "2026-10-04T15:44:09",
  secao: { municipio: 1066, zona: 4, local: 1031, secao: 77 },
  urna: {
    tipo: "secao",
    tipo_arquivo: "votacaoUE",
    versao_votacao: "10.23.0.0",
    numero_interno: 2293919,
    numero_serie_flash_carga: "69B0E0BF",
    numero_serie_flash_votacao: "4C4AE502",
    codigo_carga: "093853352215815221270154",
    data_hora_carga: "2026-09-23T13:39:00",
  },
  comparecimento: 234,
  votacao: { abertura: "2026-10-04T06:06:52", encerramento: "2026-10-04T15:40:41" },
  sistema_apuracao: null,
  detalhamento_comparecimento: {
    sem_biometria: 9,
    habilitados_biometria: 212,
    habilitados_ano_nascimento: 13,
  },
  eleicoes: [
    {
      eleicao: 6257,
      nome: "Eleição Ordinária Federal - 2026 1º Turno",
      aptos: 289,
      aptos_secao: 289,
      aptos_transito: 0,
      cargos: [
        {
          codigo: 1,
          identificador: "presidente",
          nome: "Presidente",
          tipo: "majoritario",
          ordem_impressao: 5,
          comparecimento: 234,
          totais: { nominal: 202, legenda: 0, branco: 4, nulo: 13 },
          votos: [
            {
              tipo: "nominal",
              quantidade: 99,
              numero: 13,
              partido: 13,
              nome: "LULA",
              nome_completo: null,
              sigla_partido: "PT",
            },
            {
              tipo: "nominal",
              quantidade: 103,
              numero: 22,
              partido: 22,
              nome: "FLAVIO BOLSONARO",
              nome_completo: null,
              sigla_partido: "PL",
            },
            {
              tipo: "branco",
              quantidade: 4,
              numero: null,
              partido: null,
              nome: null,
              nome_completo: null,
              sigla_partido: null,
            },
            {
              tipo: "nulo",
              quantidade: 13,
              numero: null,
              partido: null,
              nome: null,
              nome_completo: null,
              sigla_partido: null,
            },
          ],
        },
      ],
    },
  ],
};

const STATUS = {
  pleito: 3220,
  uf: "ac",
  municipio: 1066,
  zona: 4,
  secao: 77,
  situacao: "Totalizada",
  atualizado_em: "2026-10-05T12:52:50",
  transmissoes: [
    {
      hash: "abc",
      situacao: "Totalizado",
      recebido_em: "2026-10-04T18:34:08",
      vigente: true,
      arquivos: [
        { nome: "o03220ac0106600040077-rdv.dat", tipo: "rdv", url_tse: "https://resultados.tse.jus.br/x" },
      ],
    },
  ],
};

describe("BallotPage", () => {
  it("mostra o boletim com votos ordenados e os arquivos da urna", async () => {
    mockApi({ [`${BASE}/boletim`]: BALLOT, [BASE]: STATUS });
    renderAt(
      <Routes>
        <Route path="/secoes/:pleito/:uf/:municipio/:zona/:secao" element={<BallotPage />} />
      </Routes>,
      "/secoes/3220/ac/1066/4/77",
    );

    const table = await screen.findByRole("table", { name: "Votos para Presidente" });
    const rows = within(table).getAllByRole("row");
    expect(rows[1]).toHaveTextContent("FLAVIO BOLSONARO");
    expect(rows[1]).toHaveTextContent("103");
    expect(rows[2]).toHaveTextContent("LULA");
    expect(rows[4]).toHaveTextContent("Branco");
    expect(screen.getByText("234")).toBeInTheDocument();
    expect(screen.getByText("04/10/2026 06:06:52")).toBeInTheDocument();

    const download = await screen.findByRole("link", { name: "Registro digital do voto (RDV)" });
    expect(download).toHaveAttribute("href", `${BASE}/arquivos/rdv`);
  });
});

const TIMELINE = {
  apos: "17:00",
  votos_apos: 22,
  comparecimento: 234,
  fonte_fuso: "uf",
  horarios: {
    horas_para_brasilia: 2,
    total_votos: 234,
    primeiro_voto: "2026-10-04T08:09:09",
    ultimo_voto: "2026-10-04T17:39:09",
    por_habilitacao: { biometria: 212, ano_nascimento: 13, sem_biometria: 9 },
    intervalos: [
      { inicio: "08:00", votos: 200, por_habilitacao: { biometria: 190, ano_nascimento: 10 } },
      { inicio: "17:00", votos: 22, por_habilitacao: { biometria: 20, sem_biometria: 2 } },
    ],
  },
  estimativa_por_cargo: [
    {
      codigo: 1,
      cargo: "Presidente",
      votos_tardios: 22,
      estimativas: [
        {
          tipo: "nominal",
          numero: 22,
          nome: "FLAVIO BOLSONARO",
          partido: "PL",
          votos_secao: 103,
          votos_tardios_estimados: 9.68,
        },
      ],
    },
  ],
};

describe("BallotPage · horários", () => {
  it("mostra votos após 17h, gráfico com tabela e estimativa rotulada", async () => {
    mockApi({ [`${BASE}/boletim`]: BALLOT, [BASE]: STATUS, [`${BASE}/horarios`]: TIMELINE });
    renderAt(
      <Routes>
        <Route path="/secoes/:pleito/:uf/:municipio/:zona/:secao" element={<BallotPage />} />
      </Routes>,
      "/secoes/3220/ac/1066/4/77",
    );
    const stat = (await screen.findByText("Votos a partir das 17:00")).closest(".stat");
    expect(stat).toHaveTextContent("22");
    expect(stat).toHaveTextContent("9,4% do comparecimento");
    expect(screen.getByText("Estimativa, não contagem")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Votos a cada 15 minutos/ })).toBeInTheDocument();
    const table = screen.getByRole("table", { name: /Votos a cada 15 minutos/ });
    expect(within(table).getAllByRole("row")).toHaveLength(3);
    expect(screen.getByRole("table", { name: /Estimativa de votos/ })).toHaveTextContent("9,7");
  });
});
