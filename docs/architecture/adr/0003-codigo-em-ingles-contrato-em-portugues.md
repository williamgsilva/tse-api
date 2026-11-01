# 0003 — Escrever o código em inglês e o contrato da API em português

- **Status:** Aceito
- **Data:** 2026-10-30
- **Decisores:** @williamgsilva

## Contexto

O padrão do template ([codigo.md](../../standards/codigo.md)) pede identificadores em inglês.
O domínio, porém, é definido pelo TSE em português (pleito, seção, boletim de urna, votável,
abrangência), e os usuários da API são brasileiros e conhecem esses termos. A [api.md](../../standards/api.md)
pede escolher um padrão de nomes para o JSON e registrá-lo em ADR.

## Opções consideradas

1. **Tudo em inglês** (código, rotas e JSON). Segue o template à risca, mas obriga quem usa a API
   a traduzir de volta os termos oficiais do TSE.
2. **Tudo em português.** O contrato fica fiel ao TSE, mas o código foge do padrão do template.
3. **Código em inglês, contrato em português.** Rotas e campos do JSON usam os termos do TSE, e o
   código usa os nomes em inglês. O glossário faz a ponte.

## Decisão

Opção 3.

- Rotas e campos do JSON em **português, `snake_case`**, sem acento (`/v1/pleitos/{pleito}/secoes/...`,
  `nome_urna`, `proximo_cursor`). Mensagens de erro em português.
- Classes, funções, módulos e atributos em **inglês** (`VotingEvent`, `BallotReport`, `SectionKey`).
- A tradução fica só na borda HTTP: os schemas em `interfaces/schemas.py` herdam de `ApiSchema` e
  usam `pt("nome_no_json")` (alias de serialização do pydantic).
- Exceção: o SQL da base local mantém os nomes de coluna do CSV do TSE (`nr_votavel`, `qt_votos`),
  porque assim fica fácil conferir os dados contra o arquivo original.

## Consequências

- **Positivas:** o contrato fala a língua do usuário e do TSE; o código segue o template; o OpenAPI
  (`/docs`) mostra os nomes em português.
- **Negativas / trade-offs:** cada campo existe com dois nomes. Qualquer campo novo exige o alias no
  schema e, se for termo de negócio, uma entrada no [glossário](../../glossario.md).
- **O que precisa ser feito:** manter o glossário atualizado com a coluna "Nome no código".
