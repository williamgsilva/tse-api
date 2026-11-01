---
name: planejar
description: Cria um plano "decisão completa" para uma tarefa não trivial, somente lendo o código (sem editar nada). Use antes de implementar features, refatorações ou correções que tocam vários arquivos.
argument-hint: "<tarefa ou issue #N>"
allowed-tools: Read, Grep, Glob, Bash(git log*), Bash(git diff*), Bash(git status*)
---

Tarefa: $ARGUMENTS

Siga exatamente o prompt de `docs/prompts/06-plano.md` (leia o arquivo agora).
Regras desta skill:

- Somente leitura: não edite, não crie arquivos, não rode formatter ou migração.
- Siga `AGENTS.md` e `docs/standards/`.
- Se a tarefa for grande (várias features ou mais de um módulo), recomende usar `/spec`.
- Termine com o plano no formato do prompt e aguarde aprovação antes de qualquer alteração.
