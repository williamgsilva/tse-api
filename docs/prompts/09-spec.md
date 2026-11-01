# 09 — Spec: desenvolvimento guiado por especificação

Para features **médias e grandes** (várias telas/endpoints, mais de um módulo, regras de
negócio relevantes). Para tarefas pequenas, use [06-plano.md](06-plano.md).

Cada feature ganha uma pasta versionada com três arquivos, aprovados **um de cada vez**:

```text
docs/specs/<feature>/
├── requirements.md   # O QUÊ: histórias e critérios de aceite verificáveis
├── design.md         # COMO: arquitetura, dados, interfaces, erros, testes
└── tasks.md          # PASSOS: lista de tarefas pequenas, em ordem, rastreadas
```

## Formato dos critérios de aceite (QUANDO / ENTÃO)

Cada critério descreve um comportamento observável e testável:

| Tipo | Forma |
| ---- | ----- |
| Evento | **QUANDO** <evento> **ENTÃO** o sistema **DEVE** <resposta> |
| Condição | **SE** <condição> **ENTÃO** o sistema **DEVE** <resposta> |
| Evento + condição | **QUANDO** <evento> **E** <condição> **ENTÃO** o sistema **DEVE** <resposta> |
| Estado | **ENQUANTO** <estado> o sistema **DEVE** <comportamento> |
| Indesejado | **SE** <falha/entrada inválida> **ENTÃO** o sistema **DEVE** <tratamento> |

Exemplo: *QUANDO o usuário enviar o formulário de cadastro com e-mail já existente ENTÃO o
sistema DEVE responder 409 sem revelar se a conta está ativa.*

## Prompt

```text
Feature: <nome-da-feature> — <descrição em 2–3 frases>

Siga AGENTS.md e docs/standards/. Trabalhe em docs/specs/<nome-da-feature>/, uma fase por vez.
Ao final de cada fase, PARE e peça minha aprovação explícita. Sem aprovação, não avance.

FASE 1 — requirements.md
- Introdução (problema, usuários, fora de escopo).
- Requisitos numerados, cada um com história ("Como <papel>, quero <ação>, para <benefício>")
  e critérios de aceite no formato QUANDO/SE … ENTÃO o sistema DEVE …
- Inclua casos de erro, limites, permissões e requisitos não funcionais com números.
- Liste dúvidas abertas em vez de supor.

FASE 2 — design.md (só depois de aprovar a fase 1)
- Visão geral e módulos afetados (domain/application/infrastructure/interfaces).
- Modelo de dados, contratos de API/eventos, portas e adaptadores.
- Tratamento de erros, segurança, observabilidade, performance.
- Se a feature é sensível (auth, dados pessoais, pagamentos, integrações, LLM): seção de
  modelagem de ameaças seguindo docs/security/threat-model.md (STRIDE).
- Mudança de banco: plano expand → contract (docs/standards/dados-e-migracoes.md).
- Estratégia de testes ligada aos critérios de aceite (qual teste prova qual critério).
- Decisões relevantes → proponha ADR (docs/architecture/adr/).

FASE 3 — tasks.md (só depois de aprovar a fase 2)
- Checklist numerado (1, 1.1, 1.2…) de tarefas pequenas (cada uma vira 1 commit ou PR pequeno),
  em ordem de dependência, começando pelos testes/domínio.
- Cada tarefa cita os requisitos que atende (ex.: "Req. 2.1, 2.3") e o arquivo/camada.
- Apenas tarefas de código e testes (nada de "fazer deploy" ou "falar com o time").

EXECUÇÃO (quando eu pedir "executar tarefa N")
- Releia requirements.md, design.md e tasks.md antes de começar.
- Faça somente a tarefa pedida, rode `make check`, marque [x] em tasks.md e pare.
```

> No Claude Code: `/spec <feature>` e `/spec executar <feature> <tarefa>`.
