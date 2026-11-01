# Prompts reutilizáveis

Prompts testados para cada fase do projeto. Copie, preencha os `<campos>` e use com
qualquer assistente (Claude Code, Copilot Chat, Cursor…). Melhore-os conforme aprender.

| Arquivo | Fase | Uso |
| ------- | ---- | --- |
| [01-descoberta.md](01-descoberta.md) | Descoberta | IA entrevista você para levantar requisitos |
| [02-arquitetura.md](02-arquitetura.md) | Arquitetura | Comparar opções e gerar ADR |
| [03-feature.md](03-feature.md) | Desenvolvimento | Planejar e implementar uma feature com testes |
| [04-review.md](04-review.md) | Revisão | Code review por ângulos + review de segurança |
| [05-legado.md](05-legado.md) | Correção | Diagnosticar e adequar um projeto existente a este template |
| [06-plano.md](06-plano.md) | Desenvolvimento | Plano "decisão completa", em modo somente leitura |
| [07-verificar.md](07-verificar.md) | Verificação | Provar que a mudança funciona executando o sistema |
| [08-estudo.md](08-estudo.md) | Aprendizado | A IA ensina e você implementa as decisões de design |
| [09-spec.md](09-spec.md) | Especificação | Feature média/grande: requisitos → design → tarefas, com aprovação a cada fase |
| [10-loop-autonomo.md](10-loop-autonomo.md) | Automação | Loop autônomo com limites rígidos de iterações e escopo |

Fluxo sugerido por tarefa:

- **Pequena:** `06-plano` → `03-feature` → `make check` → `07-verificar` → `04-review` → PR.
- **Média/grande:** `09-spec` (requisitos → design → tarefas) → uma tarefa por vez → `07-verificar` → `04-review` → PR.
- **Mecânica e repetitiva:** `10-loop-autonomo` (com limite) → `04-review` → PR.

## Skills do projeto (Claude Code)

Os prompts acima também existem como comandos em [`.claude/skills/`](../../.claude/skills/).
Cada skill apenas aponta para o prompt correspondente, que continua sendo a fonte única.

| Comando | Prompt | Observação |
| ------- | ------ | ---------- |
| `/planejar <tarefa>` | 06-plano | Somente leitura |
| `/spec <feature>` · `/spec executar <feature> <n>` | 09-spec | Para a cada fase e pede aprovação |
| `/revisar [geral\|seguranca\|tudo]` | 04-review | Somente leitura; não corrige sozinho |
| `/verificar` | 07-verificar | Evidência para o PR |
| `/adr <decisão>` | 02-arquitetura | Cria o ADR numerado |
| `/loop-seguro <tarefa> [--max N]` | 10-loop-autonomo | Padrão 10, teto 25 iterações |
| `/estudar <tema>` | 08-estudo | Você escreve as decisões de design |

### Proteções determinísticas (`.claude/`)

| Camada | O que faz | Limitação |
| ------ | --------- | --------- |
| `permissions.deny` em [settings.json](../../.claude/settings.json) | Bloqueia as ferramentas Read/Edit em `.env*`, `secrets/`, `*.pem`/`*.key`; bloqueia `git push --force` e `sudo`; desativa `--dangerously-skip-permissions` | Regras Read/Edit **não** valem para o Bash; regras com pipe não funcionam (cada parte do comando é avaliada separadamente) |
| `permissions.ask` | Pede confirmação para `curl`, `wget`, `git push`, `git reset --hard`, `rm -r(f)`, `docker`, `kubectl`, `terraform` e edições em `.github/` e `.claude/` | Mais confirmações durante o trabalho |
| Hook [protect-secrets.sh](../../.claude/hooks/protect-secrets.sh) (PreToolUse) | Bloqueia comandos de shell que citam `.env*`, `secrets/` ou chaves (`cat .env`, `source .env`…) | Baseado em texto; um comando ofuscado de propósito pode escapar |
| Hook [format.sh](../../.claude/hooks/format.sh) (PostToolUse) | Roda `make format` após cada edição da IA | Inativo até a stack implementar `make format` |
| Sandbox (`sandbox.enabled`) | Isola os comandos do Bash (arquivos e rede); aplica as regras de leitura também no shell | No Linux exige `bubblewrap` e `socat`; sem eles, só um aviso e os comandos rodam fora do sandbox |

Ajustes pessoais (sem afetar o time) vão em `.claude/settings.local.json`, ignorado pelo git.

## Boas práticas de prompt

1. **Contexto → tarefa → restrições → formato de saída.** Nessa ordem.
2. **Peça o plano antes do código** e revise o plano.
3. **Uma tarefa por vez**, com critério de pronto verificável ("`make check` passa").
4. **Peça para perguntar** quando faltar informação, em vez de supor.
5. **Referencie arquivos** em vez de colar conteúdo (o agente lê `AGENTS.md` sozinho).
6. **Exija justificativa** para escolhas (bibliotecas, padrões) — e confira as fontes.
7. **Achado sem cenário concreto não é achado.** Peça sempre "com a entrada X acontece Y".

## Recursos nativos do Claude Code

| Recurso | O que faz |
| ------- | --------- |
| Plan mode (Shift+Tab) | Planeja em modo somente leitura antes de alterar arquivos |
| `/code-review` | Review de bugs e qualidade das mudanças da branch |
| `/security-review` | Review de segurança das mudanças da branch |
| `/simplify` | Limpeza: reuso, simplificação, eficiência (não procura bugs) |
| `/sandbox` | Mostra o estado do sandbox e as dependências que faltam |
| `/init` | Cria ou revisa o CLAUDE.md |
| `/config` → Output style *Learning* / *Explanatory* | Modo de aprendizado (ver 08-estudo.md) |
| Skill `skill-creator` | Cria skills próprias do projeto em `.claude/skills/` |

## Qual review usar?

| Situação | Use |
| -------- | --- |
| Todo PR, antes do review humano | `/revisar tudo` (critérios do projeto: arquitetura, padrões, falhas silenciosas, segurança) |
| Segunda opinião de segurança em mudança sensível | `/security-review` (nativo) |
| PR grande ou com muita lógica de erro/tipos/testes | `/pr-review-toolkit:review-pr` (plugin) |
| Revisão de PR no GitHub, com comentários na linha | Plugin `code-review` ou `/code-review` (nativo) |
| Só limpar o código, sem caçar bugs | `/simplify` |

Nenhum deles substitui o review humano: são filtros antes dele.

## Plugins oficiais recomendados

Do repositório oficial [anthropics/claude-code](https://github.com/anthropics/claude-code/tree/main/plugins).
Instale com `/plugin` (marketplace oficial) e use conforme a necessidade:

| Plugin | Para quê |
| ------ | -------- |
| `feature-dev` | `/feature-dev`: fluxo guiado de feature (exploração com agentes, perguntas, arquitetura, implementação, review) |
| `pr-review-toolkit` | Agentes especializados de review, incluindo `silent-failure-hunter` (erros engolidos) e análise de testes |
| `security-guidance` | Hook que alerta padrões perigosos (injeção de comando, XSS, eval, desserialização) durante a edição |
| `commit-commands` | `/commit`, `/commit-push-pr`, `/clean_gone` |
| `hookify` | Transforma "nunca faça X" em hook que bloqueia de verdade |
| `ralph-wiggum` | Loop autônomo — **somente** com `--max-iterations` (ver 10-loop-autonomo.md) |

> Regra geral: o que **não pode** falhar vira hook ou permissão em `.claude/settings.json`;
> instrução em prompt é orientação, não garantia.

## Fontes para estudar prompts e skills

- Oficiais (preferir): [anthropics/skills](https://github.com/anthropics/skills),
  [documentação do Claude Code](https://docs.claude.com/en/docs/claude-code/overview),
  [system prompts publicados pela Anthropic](https://platform.claude.com/docs/en/release-notes/system-prompts),
  [guia de prompt engineering](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview),
  [Building effective agents](https://www.anthropic.com/research/building-effective-agents).
- Livro aberto (MIT): [The Interactive Book of Prompting](https://prompts.chat) do
  [f/prompts.chat](https://github.com/f/prompts.chat) — capítulos de context engineering, agentes
  e skills, harnesses, MCP e programação. O site também oferece biblioteca de prompts (CC0),
  servidor MCP e plugin para o Claude Code; os prompts da comunidade têm qualidade variável.
- Agentes open source (licença aberta, leia direto na fonte):
  [Cline](https://github.com/cline/cline), [OpenAI Codex CLI](https://github.com/openai/codex),
  [Gemini CLI](https://github.com/google-gemini/gemini-cli).
- Comunidade (não oficial, autenticidade não garantida, direitos dos textos pertencem às
  empresas): [asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks),
  [x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools)
  (destaque: o fluxo de spec do Kiro, base do 09-spec.md).
  Use para estudar padrões; não copie textos para o projeto.
