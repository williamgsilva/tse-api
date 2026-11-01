// Contrato da API (/v1). Campos em português, como no JSON (ADR 0003).

export interface Office {
  codigo: number;
  nome: string;
  tipo: "majoritario" | "proporcional" | "consulta" | string;
  abrangencias: string[];
}

export interface Election {
  codigo: number;
  nome: string;
  turno: number;
  tipo: number;
  pleito: number;
  ciclo: string;
  ano: number;
  data: string;
  codigo_segundo_turno: number | null;
  cargos: Office[];
}

export interface VotingEvent {
  pleito: number;
  ciclo: string;
  ano: number;
  data: string;
  eleicoes: Election[];
}

export interface Municipality {
  uf: string;
  codigo: number;
  codigo_ibge: number | null;
  nome: string;
  capital: boolean;
  zonas: number[];
}

export interface Totals {
  secoes?: { total: number | null; totalizadas: number | null; percentual_totalizadas: number | null } | null;
  eleitorado?: {
    total: number | null;
    comparecimento: number | null;
    abstencao: number | null;
    percentual_comparecimento: number | null;
    percentual_abstencao: number | null;
  } | null;
  votos?: {
    total: number | null;
    validos: number | null;
    nominais: number | null;
    legenda: number | null;
    brancos: number | null;
    nulos: number | null;
    percentual_brancos: number | null;
    percentual_nulos: number | null;
  } | null;
}

export interface Candidate {
  numero: number | null;
  nome: string | null;
  nome_urna: string | null;
  partido: string | null;
  numero_partido: number | null;
  agremiacao: string | null;
  composicao: string | null;
  votos: number;
  percentual: number | null;
  eleito: boolean;
  situacao: string | null;
  destinacao_votos: string | null;
  vices_suplentes: {
    tipo: string | null;
    nome: string | null;
    nome_urna: string | null;
    partido: string | null;
  }[];
}

export interface OfficeResult {
  codigo: number | null;
  nome: string | null;
  vagas: number | null;
  quociente_eleitoral: number | null;
  candidatos: Candidate[];
}

export interface ElectionResult {
  eleicao: number | null;
  turno: number | null;
  tipo_abrangencia: string | null;
  codigo_abrangencia: string | null;
  atualizado_em: string | null;
  totalizacao_finalizada: boolean;
  totais: Totals;
  cargos: OfficeResult[];
}

export interface SectionSummary {
  uf: string;
  municipio: number;
  nome_municipio: string | null;
  zona: number;
  secao: number;
  atualizado_em: string | null;
}

export interface SectionPage {
  total: number;
  proximo_cursor: string | null;
  secoes: SectionSummary[];
}

export interface UrnFile {
  nome: string;
  tipo: string;
  url_tse: string;
}

export interface SectionStatus {
  pleito: number;
  uf: string;
  municipio: number;
  zona: number;
  secao: number;
  situacao: string | null;
  atualizado_em: string | null;
  transmissoes: {
    hash: string;
    situacao: string | null;
    recebido_em: string | null;
    vigente: boolean;
    arquivos: UrnFile[];
  }[];
}

export interface BallotVote {
  tipo: "nominal" | "legenda" | "branco" | "nulo" | string;
  quantidade: number;
  numero: number | null;
  partido: number | null;
  nome: string | null;
  nome_completo: string | null;
  sigla_partido: string | null;
}

export interface BallotOffice {
  codigo: number;
  identificador: string;
  nome: string | null;
  tipo: string;
  ordem_impressao: number;
  comparecimento: number;
  totais: Record<string, number>;
  votos: BallotVote[];
}

export interface BallotReport {
  arquivo: string | null;
  uf: string | null;
  fase: string;
  gerado_em: string | null;
  emitido_em: string | null;
  secao: { municipio: number; zona: number; local: number; secao: number };
  urna: {
    tipo: string;
    tipo_arquivo: string;
    versao_votacao: string;
    numero_interno: number;
    numero_serie_flash_carga: string;
    numero_serie_flash_votacao: string;
    codigo_carga: string;
    data_hora_carga: string | null;
  };
  comparecimento: number;
  votacao: { abertura: string | null; encerramento: string | null } | null;
  sistema_apuracao: Record<string, unknown> | null;
  detalhamento_comparecimento: {
    sem_biometria: number;
    habilitados_biometria: number;
    habilitados_ano_nascimento: number;
  } | null;
  eleicoes: {
    eleicao: number;
    nome: string | null;
    aptos: number;
    aptos_secao: number;
    aptos_transito: number;
    cargos: BallotOffice[];
  }[];
}

export interface ImportedDataset {
  tipo: "boletins" | "urnas";
  ano: number;
  turno: number;
  uf: string;
  arquivo: string;
  linhas: number;
  secoes: number;
}

export type Grouping = "total" | "votavel" | "uf" | "municipio" | "zona" | "local" | "secao";

export interface VoteAggregate {
  uf?: string;
  municipio?: number;
  nome_municipio?: string;
  zona?: number;
  secao?: number;
  tipo: string | null;
  numero: number | null;
  nome: string | null;
  partido: string | null;
  votos: number;
}

export interface Problem {
  type: string;
  title: string;
  status: number;
  detail?: string | null;
  traceId?: string | null;
}

export type Enablement = "biometria" | "ano_nascimento" | "sem_biometria";

export interface TimelineBucket {
  inicio: string;
  votos: number;
  por_habilitacao: Partial<Record<Enablement, number>>;
}

export interface LateVoteEstimate {
  tipo: string;
  numero: number | null;
  nome: string | null;
  partido: string | null;
  votos_secao: number;
  votos_tardios_estimados: number;
}

export interface SectionVoteTimeline {
  apos: string;
  votos_apos: number;
  comparecimento: number;
  fonte_fuso: "uf" | "desconhecido";
  horarios: {
    horas_para_brasilia: number | null;
    total_votos: number;
    primeiro_voto: string | null;
    ultimo_voto: string | null;
    por_habilitacao: Partial<Record<Enablement, number>>;
    intervalos: TimelineBucket[];
  };
  estimativa_por_cargo: {
    codigo: number;
    cargo: string | null;
    votos_tardios: number;
    estimativas: LateVoteEstimate[];
  }[];
}

export type Group = Partial<{
  uf: string;
  municipio: number;
  nome_municipio: string | null;
  zona: number;
  local: number;
  secao: number;
}>;

export interface TurnoutAggregate {
  grupo: Group;
  secoes: number;
  aptos: number;
  comparecimento: number;
  abstencoes: number;
  percentual_comparecimento: number | null;
  habilitados_biometria: number | null;
  habilitados_ano_nascimento: number | null;
  sem_biometria: number | null;
  secoes_com_arquivos_urna: number;
  primeira_abertura: string | null;
  ultimo_encerramento: string | null;
}

export interface TimelinePoint extends TimelineBucket {
  grupo: Group;
}

export interface LateVotesReport {
  apos: string;
  metodo: string;
  resumo: { secoes: number; comparecimento: number; votos_apos: number; secoes_sem_fuso: number };
  votaveis: {
    grupo: Group;
    tipo: string | null;
    numero: number | null;
    nome: string | null;
    partido: string | null;
    votos_nas_secoes: number;
    votos_apos_estimados: number;
  }[];
}

export interface SubdivisionResult {
  tipo_abrangencia: "uf" | "mu";
  codigo: string;
  codigo_ibge: number | null;
  nome: string;
  totalizacao_finalizada: boolean;
  totais: Totals;
  candidatos: {
    numero: number | null;
    nome_urna: string | null;
    partido: string | null;
    votos: number;
    percentual: number | null;
    eleito: boolean;
    situacao: string | null;
  }[];
}
