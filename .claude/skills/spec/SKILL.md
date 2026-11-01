---
name: spec
description: Desenvolvimento guiado por especificação para features médias e grandes. Gera requirements.md (critérios QUANDO/ENTÃO), design.md e tasks.md em docs/specs/<feature>/, com aprovação a cada fase, e depois executa as tarefas uma a uma.
argument-hint: "<nome-da-feature> [descrição] | executar <nome-da-feature> [tarefa]"
disable-model-invocation: true
---

Pedido: $ARGUMENTS

Siga exatamente o processo de `docs/prompts/09-spec.md` (leia o arquivo agora).

- Uma fase por vez: requisitos → design → tarefas. Pare ao fim de cada fase e peça aprovação.
- No design de feature sensível, inclua a modelagem de ameaças (`docs/security/threat-model.md`).
- Ao executar ("executar ..."), releia os três arquivos antes de cada tarefa, faça uma
  tarefa por vez, rode `make check`, marque a tarefa como concluída em `tasks.md` e pare.
- Nunca pule a aprovação, mesmo que o pedido diga para seguir direto.
