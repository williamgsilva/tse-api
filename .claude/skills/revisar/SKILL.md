---
name: revisar
description: Revisão das mudanças da branch por ângulos (bugs, comportamento removido, chamadas cruzadas, falhas silenciosas, arquitetura, testes, eficiência, causa raiz) e revisão de segurança. Somente leitura; cada achado exige cenário de falha concreto.
argument-hint: "[geral | seguranca | tudo] [branch-base, padrão main]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git diff*), Bash(git log*), Bash(git status*), Bash(git show*)
---

Pedido: $ARGUMENTS (padrão: `tudo` contra `main`)

Siga exatamente os prompts de `docs/prompts/04-review.md` (leia o arquivo agora):

- `geral` → seção "Review geral (por ângulos)"
- `seguranca` → seção "Review de segurança"
- `tudo` → as duas, nessa ordem, em relatórios separados

Regras desta skill:

- Somente leitura: não corrija nada; apenas reporte.
- Achado sem cenário de falha concreto é descartado.
- No fim, pergunte quais achados devo corrigir.
- Para escolher entre esta skill e os reviews nativos/plugins, veja a tabela "Qual review usar?"
  em `docs/prompts/README.md`.
