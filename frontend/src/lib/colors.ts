/** Cores categóricas em ordem fixa (validadas para daltonismo). A 9ª categoria em diante vira "Outros". */
export const SERIES = [1, 2, 3, 4, 5, 6, 7, 8].map((n) => `var(--series-${n})`);
export const OTHER = "var(--series-other)";
export const EMPTY = "var(--series-empty)";
export const SEQUENTIAL = [1, 2, 3, 4, 5, 6, 7].map((n) => `var(--seq-${n})`);

/**
 * Atribui uma cor a cada categoria pela ordem recebida (ex.: partidos do maior para o menor).
 * A cor segue a entidade: quem chama passa uma ordem estável (a do Brasil inteiro), não a do recorte.
 */
export function colorScale(ordered: string[]): (category: string | null | undefined) => string {
  const colors = new Map(
    ordered.slice(0, SERIES.length).map((category, i) => [category, SERIES[i] ?? OTHER]),
  );
  return (category) => (category ? (colors.get(category) ?? OTHER) : EMPTY);
}

/** Cor sequencial para um valor entre ``min`` e ``max`` (7 degraus de um único matiz). */
export function sequentialColor(value: number | null | undefined, min: number, max: number): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EMPTY;
  const t = max > min ? (value - min) / (max - min) : 0.5;
  const index = Math.min(SEQUENTIAL.length - 1, Math.max(0, Math.floor(t * SEQUENTIAL.length)));
  return SEQUENTIAL[index] ?? EMPTY;
}
