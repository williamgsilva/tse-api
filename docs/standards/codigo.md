# Padrões de código

Objetivo: código que **outra pessoa (ou você daqui a 6 meses) entende e muda com segurança.**

## Princípios

| Princípio | Na prática |
| --------- | ---------- |
| **KISS** | A solução mais simples que atende ao requisito. Sem abstração "para o futuro". |
| **YAGNI** | Não implemente o que não foi pedido. |
| **DRY (com moderação)** | Duplicação de *conhecimento* é ruim; duplicação acidental de código é aceitável até a 3ª vez (*rule of three*). |
| **SOLID** | Especialmente: responsabilidade única e inversão de dependência (portas). |
| **Composição > herança** | Herança só para relação "é-um" real e estável. |
| **Imutabilidade por padrão** | Value objects e DTOs imutáveis; mutação explícita e localizada. |
| **Fail fast** | Valide na borda; estado inválido não deve ser representável. |

## Nomes

- Nomes revelam intenção: `activeUsers`, não `list2`; `isExpired()`, não `check()`.
- Use o **vocabulário do negócio** (linguagem ubíqua do DDD) — o mesmo termo no código, nos testes e na conversa.
- Booleanos: `is/has/can/should`. Funções: verbo. Classes/tipos: substantivo.
- Sem abreviações obscuras. Exceções aceitas: `id`, `url`, `http`, `db`, `ctx`.
- Idioma do código: **inglês** (identificadores). Docs e mensagens ao usuário: conforme o produto.

## Funções e classes

- Função faz **uma coisa**; idealmente < 30 linhas; ≤ 3–4 parâmetros (mais que isso → objeto).
- Evite parâmetros booleanos que mudam o comportamento (`send(true)`) — crie duas funções.
- Retorno antecipado (*guard clauses*) em vez de `if` aninhado.
- Complexidade ciclomática baixa (configure limite no linter, ex.: 10).

## Comentários

- O código diz **o quê/como**; comentário diz **por quê** (decisão, restrição, link de issue).
- Proibido: código comentado, comentários que repetem o código, `TODO` sem issue (`TODO(#123): ...`).
- APIs públicas documentadas no padrão da linguagem (docstring, JSDoc, GoDoc, Javadoc…).

## Erros

- Nunca engolir erros (`catch {}` vazio). Trate, enriqueça com contexto ou propague.
- Erros de **domínio** são tipados (ex.: `InsufficientBalance`) e fazem parte do contrato.
- Erros de **infraestrutura** são traduzidos na borda — o domínio não conhece `SQLException`.
- Mensagem ao usuário ≠ mensagem de log. Não vaze stack trace/detalhes internos na resposta.

## Logs

- Estruturados (JSON), com `level`, `timestamp`, `message`, `trace_id` e campos de contexto.
- Níveis: `error` (ação necessária), `warn` (anômalo mas tratado), `info` (eventos de negócio), `debug` (diagnóstico).
- **Nunca** logar segredos, tokens, senhas, documentos ou dados pessoais completos.

## Configuração

- Via variáveis de ambiente ([12-factor](https://12factor.net/pt_br/config)), validadas na inicialização (falha se faltar).
- Nada de configuração "mágica" espalhada: um único módulo `shared/config`.

## Dependências externas

Antes de adicionar uma biblioteca, verifique:

1. Realmente precisa? (a stdlib resolve?)
2. Licença compatível (MIT/Apache-2.0/BSD preferidas).
3. Mantida? (commits recentes, issues respondidas, [OpenSSF Scorecard](https://scorecard.dev)).
4. Tamanho e dependências transitivas.
5. Versão fixada no lockfile.

## Formatação

Automática e não discutível: o formatter da linguagem decide. Configurado no
pre-commit e validado na CI.
