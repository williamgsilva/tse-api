import { describe, expect, it, vi } from "vitest";

import { ApiError, api, buildUrl } from "./client";

describe("buildUrl", () => {
  it("monta a query ignorando valores vazios", () => {
    expect(buildUrl("/eleicoes", { ano: 2026, uf: "", municipio: null, zona: undefined })).toBe(
      "/v1/eleicoes?ano=2026",
    );
    expect(buildUrl("/x")).toBe("/v1/x");
  });
});

describe("getJson", () => {
  it("converte Problem Details em ApiError", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          title: "Seção sem arquivos de urna publicados",
          status: 404,
          detail: "x",
          traceId: "abc",
        }),
        { status: 404 },
      ),
    );
    const error = await api.ballot(3220, "ac", 1066, 4, 78).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 404,
      title: "Seção sem arquivos de urna publicados",
      traceId: "abc",
    });
  });

  it("tolera resposta de erro sem JSON", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("bad gateway", { status: 502, statusText: "Bad Gateway" }),
    );
    await expect(api.imports()).rejects.toMatchObject({ status: 502, title: "Bad Gateway" });
  });

  it("monta a URL de download do arquivo da urna", () => {
    expect(api.urnFileUrl(3220, "ac", 1066, 4, 77, "rdv")).toBe(
      "/v1/pleitos/3220/secoes/ac/1066/4/77/arquivos/rdv",
    );
  });
});
