const integer = new Intl.NumberFormat("pt-BR");
const percent = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function formatInt(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : integer.format(value);
}

/** Percentual já em escala 0–100 (como o TSE publica). */
export function formatPercent(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${percent.format(value)}%`;
}

export function share(part: number, total: number): number {
  return total > 0 ? (part / total) * 100 : 0;
}

/** "2026-10-04T15:40:41" → "04/10/2026 15:40:41" (sem conversão de fuso: horário oficial da urna). */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}:\d{2}(?::\d{2})?))?/.exec(iso);
  if (!match) return iso;
  const [, y, m, d, time] = match;
  return `${d}/${m}/${y}${time ? ` ${time}` : ""}`;
}

export function pad(value: number, size: number): string {
  return String(value).padStart(size, "0");
}

const VOTE_KIND: Record<string, string> = {
  nominal: "Nominal",
  legenda: "Legenda",
  branco: "Branco",
  nulo: "Nulo",
};

export function voteKindLabel(kind: string): string {
  return VOTE_KIND[kind] ?? kind;
}

/** Horários de corte (Brasília) oferecidos nas análises de votos tardios; múltiplos de 15 min. */
export const CUTOFFS = ["15:00", "16:00", "16:30", "17:00", "17:15", "17:30", "18:00"];
