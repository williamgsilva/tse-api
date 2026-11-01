export type RegionKey = "norte" | "nordeste" | "centro-oeste" | "sudeste" | "sul";

export const REGIONS: { id: RegionKey; name: string; ufs: string[] }[] = [
  { id: "norte", name: "Norte", ufs: ["ac", "am", "ap", "pa", "ro", "rr", "to"] },
  { id: "nordeste", name: "Nordeste", ufs: ["al", "ba", "ce", "ma", "pb", "pe", "pi", "rn", "se"] },
  { id: "centro-oeste", name: "Centro-Oeste", ufs: ["df", "go", "ms", "mt"] },
  { id: "sudeste", name: "Sudeste", ufs: ["es", "mg", "rj", "sp"] },
  { id: "sul", name: "Sul", ufs: ["pr", "rs", "sc"] },
];

export function regionOf(uf: string): RegionKey | undefined {
  return REGIONS.find((r) => r.ufs.includes(uf.toLowerCase()))?.id;
}

export function regionName(id: RegionKey): string {
  return REGIONS.find((r) => r.id === id)?.name ?? id;
}
