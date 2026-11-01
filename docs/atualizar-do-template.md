# Receber atualizações do template

Projetos criados a partir do template **não recebem melhorias automaticamente**. Este guia
mostra como trazê-las (CI, segurança, prompts, skills, padrões) sem perder o que é do projeto.

## Pré-requisito

O `init-project.sh` já cria o remote `template` quando o histórico é reiniciado. Confira:

```bash
git remote -v                       # deve listar "template"
# se não existir:
git remote add template https://github.com/<dono>/<repo-do-template>.git
```

## Opção 1 — Trazer arquivos específicos (recomendado)

Mais seguro: você escolhe exatamente o que atualizar.

```bash
git fetch template
git checkout -b chore/atualizar-template
# ver o que mudou no template desde a última atualização
git diff HEAD template/main --stat -- .github .claude docs/prompts docs/standards .pre-commit-config.yaml
# trazer arquivos/pastas que são "do template" (não personalizados pelo projeto)
git checkout template/main -- .github/workflows/security.yml docs/prompts .claude/skills
# para quem usa uma stack: use template/lang/<stack> no lugar de template/main
```

Revise o diff (`git diff --staged`), rode `make check` e abra um PR.

## Opção 2 — Merge completo

Útil quando o projeto ainda está muito próximo do template.

```bash
git fetch template
git checkout -b chore/atualizar-template
git merge template/main --allow-unrelated-histories   # apenas na primeira vez precisa da flag
```

Espere conflitos em arquivos personalizados (`README.md`, `AGENTS.md`, `Makefile`,
`overview.md`): mantenha o conteúdo do projeto e incorpore só as melhorias.

## O que normalmente atualizar × manter

| Atualizar do template | Manter do projeto |
| --------------------- | ----------------- |
| `.github/workflows/*`, `.pre-commit-config.yaml`, `.github/dependabot.yml` (base) | `README.md`, `CHANGELOG.md`, `docs/architecture/*`, `docs/specs/*`, `docs/glossario.md` |
| `docs/prompts/*`, `.claude/skills/*`, `.claude/hooks/*` | `AGENTS.md` (incorpore regras novas manualmente) |
| `docs/standards/*` (se o projeto não personalizou) | `Makefile` e `.claude/settings.json` (compare e incorpore) |

## Alternativa: Copier

[Copier](https://copier.readthedocs.io) gera projetos a partir de templates e **aplica
atualizações depois** (`copier update`) com merge de três vias. Vale a pena se você criar
muitos projetos. Exige converter os `{{PLACEHOLDERS}}` em perguntas do `copier.yml` (ver o
roadmap do template no README).

## Frequência

Uma vez por trimestre, ou quando sair uma correção de segurança no template.
