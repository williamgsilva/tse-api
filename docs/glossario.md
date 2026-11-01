# Glossário (linguagem ubíqua)

Termos do **negócio** usados no código, nos testes, na documentação e nas conversas.
Um termo, um significado. Se o time usa duas palavras para a mesma coisa, escolha uma aqui.

A IA também consulta este arquivo: termos bem definidos geram nomes de código corretos.
Rotas e JSON usam o termo em português; o código usa o nome em inglês ([ADR 0003](architecture/adr/0003-codigo-em-ingles-contrato-em-portugues.md)).

| Termo (JSON/rota) | Definição | Nome no código | Módulo | Não confundir com |
| ----------------- | --------- | -------------- | ------ | ----------------- |
| Ciclo (`ciclo`) | Agrupamento anual usado nos caminhos do TSE (ex.: `ele2026`) | `cycle` | elections | Ano da eleição suplementar (pode pertencer a outro ciclo) |
| Pleito (`pleito`) | Uma data de votação. Os arquivos de urna são organizados por pleito (3220 = 1º turno de 2026, 3221 = 2º turno) | `VotingEvent` | elections, ballots | Eleição |
| Eleição (`eleicao`) | Conjunto de cargos disputados num pleito (6257 = federal 1º turno, 6259 = estadual 1º turno). Resultados são por eleição | `Election` | elections | Pleito |
| Cargo (`cargo`) | Cargo em disputa ou pergunta de consulta popular (1 Presidente, 3 Governador, 5 Senador, 6 Dep. Federal, 7 Dep. Estadual, 8 Dep. Distrital) | `Office` | elections, ballots | — |
| Abrangência (`abrangencia`) | Recorte geográfico de um resultado: `br`, UF (`sp`) ou município (`mu`) | `scope` | elections | UF |
| UF (`uf`) | Sigla da unidade da federação em minúsculas; `zz` = exterior | `uf` | shared | — |
| Município (`municipio`) | Código **do TSE** com 5 dígitos (ex.: 71072 = São Paulo). O código IBGE vem em `codigo_ibge` | `municipality` | todos | Código IBGE |
| Zona eleitoral (`zona`) | Unidade da Justiça Eleitoral que agrupa seções | `zone` | ballots, open_data | — |
| Seção eleitoral (`secao`) | Local onde uma urna recebe os votos de um grupo de eleitores | `SectionKey` (uf, município, zona, seção) | ballots, open_data | Local de votação |
| Local de votação (`local`) | Prédio onde ficam uma ou mais seções | `polling_place` / `local` | ballots, open_data | Seção |
| Boletim de urna — BU (`boletim`) | Resultado oficial de uma urna: aptos, comparecimento e votos por cargo, assinado digitalmente | `BallotReport` | ballots | Resultado totalizado |
| Transmissão (`transmissoes`) | Conjunto de arquivos enviados pela urna, identificado por um hash. A vigente é a última totalizada | `UrnFileSet` | ballots | — |
| Arquivo de urna (`arquivos`) | BU (`bu`), registro digital do voto (`rdv`), log (`log`) e assinatura (`vota`) | `UrnFile` | ballots | — |
| Votável (`votavel`) | Quem recebe voto num cargo: candidato (nominal), partido (legenda), branco ou nulo | `VoteCount` / `votable` | ballots, open_data | Candidato |
| Voto nominal / legenda / branco / nulo | Tipos de voto da urna (`tipo`) | `kind` | ballots | — |
| Aptos (`aptos`) | Eleitores habilitados a votar naquela seção (inclui trânsito) | `eligible_voters` | ballots | Comparecimento |
| Comparecimento (`comparecimento`) | Eleitores que votaram | `turnout` | elections, ballots | Votos válidos |
| Totalização | Soma oficial dos BUs feita pelo TSE | `ElectionResult` / `is_final` | elections | Apuração da seção |
| Log da urna (`log`) | Registro de eventos da urna. Tem a hora de cada voto e o tipo de habilitação, nunca o candidato | `UrnLogReader`, `VoteEvent` | ballots | RDV |
| Habilitação (`por_habilitacao`) | Como o eleitor foi liberado para votar: `biometria`, `ano_nascimento` (tinha biometria, mas a digital falhou) ou `sem_biometria` | `enablement` | ballots, open_data | — |
| Votos após um horário (`votos_apos`) | Votos computados a partir de um horário de Brasília: o total é exato (log); a divisão por candidato é **estimativa** | `count_after`, `LateVotesReport` | ballots, open_data | — |
| Pacote de urnas (`--fonte urnas`) | ZIP por UF e turno com BU, log, RDV e assinatura de todas as seções | `DatasetKind.URN_FILES` | open_data | CSV de boletins |
| Região (`regiao`) | Agrupamento de UFs do IBGE: Norte, Nordeste, Centro-Oeste, Sudeste, Sul | `REGIONS`, `region_of` | shared | — |
| Subdivisão (`subdivisoes`) | Cada UF de um resultado nacional ou cada município de um resultado estadual | `SubdivisionResult` | elections | Abrangência |
| Malha (`mapas`) | Limites geográficos (GeoJSON) do IBGE, ligados ao TSE pelo código IBGE | `Mesh` | geography | — |
| Dados abertos (`dados-abertos`) | CSVs de BU por UF e turno do Portal de Dados Abertos, importados para a base local | `DatasetFile`, `VoteRepository` | open_data | Portal de resultados |

## Regras

- Adicione o termo **antes** de criar a classe/tabela/endpoint com esse nome.
- Nome no código em inglês (ver [codigo.md](standards/codigo.md)); definição em português.
- O mesmo termo pode ter significados diferentes em módulos (bounded contexts) diferentes:
  registre um por linha, indicando o módulo.
