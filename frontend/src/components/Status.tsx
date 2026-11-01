import type { ReactNode } from "react";

import { ApiError } from "../api/client";

export function Loading({ label = "Carregando…" }: { label?: string }) {
  return (
    <p className="status status--loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" /> {label}
    </p>
  );
}

export function ErrorMessage({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const isApi = error instanceof ApiError;
  return (
    <div className="status status--error" role="alert">
      <strong>{isApi ? error.title : "Não foi possível carregar os dados"}</strong>
      <p>{isApi ? error.detail : error instanceof Error ? error.message : String(error)}</p>
      {isApi && error.traceId && <p className="status__trace">Código para suporte: {error.traceId}</p>}
      {onRetry && (
        <button type="button" className="button button--ghost" onClick={onRetry}>
          Tentar de novo
        </button>
      )}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="status status--empty">{children}</p>;
}
