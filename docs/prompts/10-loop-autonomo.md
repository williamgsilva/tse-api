# 10 — Loop autônomo com limites

Loops autônomos (o agente repete a tarefa até concluir) economizam tempo em trabalho
repetitivo e bem definido — por exemplo, migrar N arquivos para um padrão ou corrigir todos
os erros de lint. Sem limites, eles **gastam tokens sem fim, podem entrar em ciclo e fazer
estragos**. O plugin oficial `ralph-wiggum` roda **sem limite por padrão**.

## Quando usar (e quando não)

| Use | Não use |
| --- | ------- |
| Tarefa mecânica com critério de pronto verificável (`make check` passa, contagem de erros chega a 0) | Decisão de design, requisito ambíguo, regra de negócio nova |
| Escopo fechado (lista de arquivos/módulos) | "Melhore o projeto", "deixe mais rápido" sem métrica |
| Mudanças fáceis de revisar e reverter | Migração de dados, infraestrutura, segurança, pagamento |

## Regras obrigatórias

1. **Critério de pronto verificável** definido antes de começar. Sem ele, não há loop.
2. **Limite de iterações**: padrão 10, teto 25. Nunca ilimitado.
3. **Isolamento**: branch dedicada `loop/<tarefa>`; de preferência em devcontainer/sandbox
   (veja o `.devcontainer` com firewall do repositório oficial `anthropics/claude-code`).
4. **Checkpoint por iteração**: `make check` + commit `chore(loop): iteração N/M - <resumo>`.
   Desfazer qualquer passo fica trivial (`git revert` ou `git reset` na branch do loop).
5. **Parada por falta de progresso**: 3 iterações seguidas com o mesmo erro ou sem avanço → parar e reportar.
6. **Proibido no loop**: `git push`, deploy, migração em banco real, alterar `.github/`,
   `.claude/`, `.env*`/segredos, adicionar dependências sem aprovação, apagar ou enfraquecer
   testes para "passar".
7. **Relatório final obrigatório**: iterações usadas, feito, pendente, bloqueios, como revisar.
8. **Revisão humana sempre**: o resultado do loop passa por `/revisar` + PR normal.

As proibições de push forçado, leitura de `.env` e afins também estão em
`.claude/settings.json` (bloqueio determinístico, que o agente não consegue ignorar).

## Prompt

```text
Tarefa autônoma: <descrição>
Critério de pronto (verificável): <ex.: `make check` passa e `grep -r "oldApi(" src/` não retorna nada>
Escopo: <arquivos/módulos permitidos>. Fora de escopo: <o que não tocar>.
Limite: <N> iterações (máx. 25).

Regras: siga docs/prompts/10-loop-autonomo.md. Crie a branch loop/<nome>. A cada iteração:
1 mudança pequena → `make check` → commit "chore(loop): iteração i/N - <resumo>".
Pare ao atingir o critério, ao fim do limite, após 3 iterações sem progresso, se precisar de
algo proibido ou se surgir dúvida de requisito. Ao parar, entregue o relatório final.
```

## Opções de execução

| Forma | Como limitar |
| ----- | ------------ |
| Skill do template `/loop-seguro` | Limite e regras já embutidos |
| Plugin `ralph-wiggum` | **Sempre** `/ralph-loop "<prompt>" --max-iterations 10 --completion-promise "PRONTO"`; `/cancel-ralph` para parar |
| Headless/CI (`claude -p`) | Rodar em container descartável, sem credenciais de produção, com timeout do job e `--max-turns` |
