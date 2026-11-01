---
name: loop-seguro
description: Executa uma tarefa de forma autônoma em iterações com limites rígidos (máximo de iterações, branch dedicada, checkpoint por commit, parada sem progresso, sem push/deploy). Use apenas para tarefas bem definidas com critério de pronto verificável.
argument-hint: "<tarefa> [--max N (padrão 10, teto 25)]"
disable-model-invocation: true
---

Pedido: $ARGUMENTS

Leia e siga `docs/prompts/10-loop-autonomo.md`. Resumo das regras obrigatórias:

1. **Antes de começar**, confirme comigo em uma mensagem: objetivo, critério de pronto
   verificável, limite de iterações (padrão 10, nunca acima de 25) e o que está fora de escopo.
   Sem critério de pronto verificável, recuse o loop e sugira `/planejar`.
2. Crie a branch `loop/<tarefa-curta>` a partir da branch atual. Nunca trabalhe na `main`.
3. A cada iteração: uma mudança pequena → `make check` → commit
   `chore(loop): iteração N/M - <resumo>` → registre o progresso.
4. **Pare imediatamente** quando: o critério de pronto for atingido; o limite de iterações
   acabar; 3 iterações seguidas falharem com o mesmo erro ou sem progresso; for preciso
   algo proibido abaixo; ou surgir dúvida de requisito.
5. **Proibido**: `git push`, deploy, migração em banco real, alterar `.github/`, `.claude/`,
   segredos ou `.env*`, instalar dependências novas sem perguntar, apagar testes para passar.
6. **Ao terminar** (por qualquer motivo): relatório com iterações usadas, o que foi feito,
   o que ficou pendente, bloqueios e como revisar (`git log main..HEAD`).

Se existir o plugin `ralph-wiggum`, nunca use `/ralph-loop` sem `--max-iterations`.
