# 0005 — Criar o frontend como SPA React servida pela própria API

- **Status:** Aceito
- **Data:** 2026-10-30
- **Decisores:** @williamgsilva

## Contexto

O projeto precisa de uma interface web para consultar os resultados, navegar pelas seções e ler os
boletins de urna. As páginas são de leitura, sem login e sem necessidade de SEO no início.

## Opções consideradas

1. **Next.js (SSR)**: dá SEO e renderização no servidor, mas exige outro runtime em produção (Node) e
   duplica a camada HTTP.
2. **HTML/JS sem build servido pela API**: é simples, mas sem tipagem e difícil de crescer.
3. **SPA React + Vite + TypeScript em `frontend/`**: tem tipagem, testes (Vitest + Testing Library) e cache
   de requisições (TanStack Query). Em produção, o build estático é servido pela própria API.

## Decisão

Opção 3.

- Em desenvolvimento, `make dev` sobe o Vite (porta 5173) e repassa `/v1` e `/health` para a API (`make run`),
  sem CORS.
- Em produção, a API serve `frontend/dist` na raiz, com fallback para `index.html` (roteamento da SPA) e
  proteção contra *path traversal*. Prefixos reservados (`/v1`, `/health`, `/docs`) nunca caem no fallback.
- A imagem Docker única constrói o frontend num estágio Node e copia só o `dist`.
- O estado das telas fica na URL (`?eleicao=…&uf=…`), então dá para compartilhar links.

## Consequências

- **Positivas:** um deploy só, mesma origem (sem CORS), contrato tipado em `frontend/src/api/types.ts`.
- **Negativas / trade-offs:** sem SEO; os tipos do frontend são escritos à mão (não gerados do OpenAPI).
- **O que precisa ser feito:** avaliar gerar os tipos a partir de `/openapi.json` quando o contrato crescer.
