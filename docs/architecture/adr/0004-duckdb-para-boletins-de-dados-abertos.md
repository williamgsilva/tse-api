# 0004 — Usar DuckDB local para os boletins de urna dos dados abertos

- **Status:** Aceito
- **Data:** 2026-10-30
- **Decisores:** @williamgsilva

## Contexto

O TSE publica os boletins de urna de duas formas:

1. **Portal de resultados**: um arquivo binário assinado (ASN.1) por seção. É ótimo para consultar uma
   seção, mas somar o país inteiro exigiria cerca de 470 mil downloads por turno.
2. **Portal de Dados Abertos**: um CSV por UF e turno (dataset `resultados-<ano>-boletim-de-urna`), com
   uma linha por votável, cargo e seção. Só o Acre tem 258 mil linhas no 1º turno, e o Brasil passa de
   dezenas de milhões.

Para somar votos por UF, município, zona ou seção, os dados precisam ficar numa base local.
A carga é eventual (após cada turno) e as consultas são analíticas e só de leitura.

## Opções consideradas

1. **PostgreSQL**: robusto e multiusuário, mas precisa de servidor, credenciais e migrações. O padrão de
   acesso (carga em lote + agregações) não aproveita o que ele tem de melhor.
2. **SQLite**: um arquivo só, mas a ingestão e os `GROUP BY` sobre dezenas de milhões de linhas são lentos.
3. **DuckDB**: um arquivo só e colunar. Lê o CSV direto (`read_csv`, latin-1), carrega o Acre em ~2 s e
   agrega rápido. Não há servidor nem credenciais.

## Decisão

Opção 3. A tabela `votos_secao` é carregada por `make ingest` (CLI `tse-ingest`). Cada carga substitui as
linhas daquele (ano, turno, UF) numa transação, depois de conferir o SHA-512 publicado pelo TSE. A API abre a
base **somente leitura**. Durante uma importação (o DuckDB aceita um processo escrevendo), os endpoints
`/v1/dados-abertos` respondem 503.

**Adendo (2026-10-30):** a base passou a receber também o pacote "Arquivos transmitidos para totalização"
(BU e log de cada urna). Tabelas novas: `urnas_secao` (uma linha por seção, com a biometria detalhada do BU),
`votos_horario` (votos por quarto de hora local e tipo de habilitação, contados no log) e `secoes_csv`
(uma linha por seção derivada do CSV, para não reagrupar milhões de linhas a cada consulta). Os registros
das urnas são gravados num CSV temporário e carregados com `read_csv` (muito mais rápido que `INSERT`).
O fuso de cada município é deduzido na consulta pela mediana do primeiro voto (a votação começa às 8h de
Brasília em todo o país), o que cobre o oeste do Amazonas e Fernando de Noronha sem tabela manual.

## Consequências

- **Positivas:** nenhuma infraestrutura extra; a carga é idempotente; as consultas são parametrizadas e rápidas.
- **Negativas / trade-offs:** um único processo escreve por vez; a base não serve para vários nós da API
  sem cópia do arquivo; o Brasil inteiro ocupa alguns GB em `data/`.
- **O que precisa ser feito:** se a API rodar em várias réplicas, publicar a base como artefato de leitura
  (ou migrar para um banco servidor) e registrar num novo ADR.
