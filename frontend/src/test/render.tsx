import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

export function renderAt(ui: ReactElement, path = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

/** Simula a API: cada rota (prefixo do caminho, sem query string) devolve um corpo JSON. */
export function mockApi(routes: Record<string, unknown>, status: Record<string, number> = {}) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = new URL(String(input), "http://localhost");
    const key = Object.keys(routes)
      .sort((a, b) => b.length - a.length)
      .find((route) => url.pathname === route);
    if (!key) {
      return new Response(JSON.stringify({ title: "Não encontrado", status: 404, detail: url.pathname }), {
        status: 404,
      });
    }
    return new Response(JSON.stringify(routes[key]), { status: status[key] ?? 200 });
  });
}
