export const UFS: { sigla: string; nome: string }[] = [
  { sigla: "ac", nome: "Acre" },
  { sigla: "al", nome: "Alagoas" },
  { sigla: "am", nome: "Amazonas" },
  { sigla: "ap", nome: "Amapá" },
  { sigla: "ba", nome: "Bahia" },
  { sigla: "ce", nome: "Ceará" },
  { sigla: "df", nome: "Distrito Federal" },
  { sigla: "es", nome: "Espírito Santo" },
  { sigla: "go", nome: "Goiás" },
  { sigla: "ma", nome: "Maranhão" },
  { sigla: "mg", nome: "Minas Gerais" },
  { sigla: "ms", nome: "Mato Grosso do Sul" },
  { sigla: "mt", nome: "Mato Grosso" },
  { sigla: "pa", nome: "Pará" },
  { sigla: "pb", nome: "Paraíba" },
  { sigla: "pe", nome: "Pernambuco" },
  { sigla: "pi", nome: "Piauí" },
  { sigla: "pr", nome: "Paraná" },
  { sigla: "rj", nome: "Rio de Janeiro" },
  { sigla: "rn", nome: "Rio Grande do Norte" },
  { sigla: "ro", nome: "Rondônia" },
  { sigla: "rr", nome: "Roraima" },
  { sigla: "rs", nome: "Rio Grande do Sul" },
  { sigla: "sc", nome: "Santa Catarina" },
  { sigla: "se", nome: "Sergipe" },
  { sigla: "sp", nome: "São Paulo" },
  { sigla: "to", nome: "Tocantins" },
  { sigla: "zz", nome: "Exterior" },
];

export function ufName(sigla: string): string {
  return UFS.find((uf) => uf.sigla === sigla.toLowerCase())?.nome ?? sigla.toUpperCase();
}
