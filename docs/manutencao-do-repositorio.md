# Manutenção do repositório

O repositório é **público** e aberto a contribuições, sempre por **branch nova + pull request**. Nem o
mantenedor faz push direto na `main`. Este documento é para quem administra o repositório no GitHub.

## Publicar e configurar (uma vez)

1. Ferramentas locais: [GitHub CLI](https://cli.github.com), `pre-commit` (`pipx install pre-commit`),
   `gitleaks` e `trivy`.
2. Login no GitHub CLI: `gh auth login`.
3. Ambiente e primeiro commit (o hook `no-commit-to-branch` exige o `SKIP` só neste primeiro commit):

   ```bash
   make setup
   git add -A
   SKIP=no-commit-to-branch git commit -m "feat: api e painel de dados públicos do TSE"
   ```

4. Publicar e aplicar as regras:

   ```bash
   ./scripts/configurar-github.sh            # padrão: williamgsilva/tse-api
   ```

O script é idempotente; rode de novo sempre que quiser reaplicar as regras.

## O que o script configura

| Área | Configuração | Por quê |
| ---- | ------------ | ------- |
| Visibilidade | Repositório público, com descrição e tópicos | Projeto aberto |
| Merge | Só *squash merge*; título e corpo do commit = título e corpo do PR; branch apagada depois do merge | Histórico linear; CHANGELOG sem duplicatas |
| `main` (ruleset "main protegida") | Proibido push direto, force-push e apagar a branch; histórico linear | Toda mudança passa por PR |
| | PR com 1 aprovação, revisão do CODEOWNER, aprovação depois do último push, conversas resolvidas | Revisão de verdade antes do merge |
| | Checks obrigatórios e atualizados com a `main`: `Lint`, `Test`, `Build`, `Secrets`, `Vulnerabilities`, `Workflows` | Nada entra com a CI vermelha |
| | Administradores podem dispensar as regras **só ao mesclar PR** (nunca em push direto) | O mantenedor consegue mesclar os próprios PRs, já que o GitHub não deixa ninguém aprovar o próprio PR |
| Actions | Token padrão só de leitura; Actions podem abrir PR; workflows de PRs de forks precisam de aprovação para todo contribuidor externo | Release-please funciona; código de terceiros não roda na CI sem você ver antes |
| Segurança | Alertas e correções automáticas do Dependabot, varredura de segredos com bloqueio no push, reporte privado de vulnerabilidades | Camadas além do gitleaks e do trivy da CI |

## Ajustes manuais

| Quando | O que fazer |
| ------ | ----------- |
| O script avisar que não conseguiu aplicar algo | Ajustar em *Settings* no GitHub (o aviso diz onde) |
| A cada PR de release (release-please) | Clicar em **Approve and run workflows** antes do merge, se a CI estiver retida |
| Repositório for de **organização** | Criar o secret `GITLEAKS_LICENSE` (gratuita em gitleaks.io), exigido pelo job *Secrets* |
| Opcional | Plugins do Claude Code em [prompts/README.md](prompts/README.md#plugins-oficiais-recomendados) |

## Revisando contribuições externas

1. No primeiro PR de alguém, leia o diff **antes** de aprovar a execução dos workflows (*Approve and run*).
   Atenção especial a mudanças em `.github/`, `Makefile`, `Dockerfile`, `scripts/` e dependências.
2. Confira a evidência de verificação no PR e se o título segue Conventional Commits (vira o commit do squash).
3. Aprove pelo GitHub e use **Squash and merge**.

## Rotina

- A cada 1–3 meses: `pre-commit autoupdate` e revisão dos PRs do Dependabot (pip, npm, Docker e Actions).
- Ao atualizar o template de origem: [atualizar-do-template.md](atualizar-do-template.md).

## Automação de qualidade e segurança

| Item | O que faz | Quando roda |
| ---- | --------- | ----------- |
| [.pre-commit-config.yaml](../.pre-commit-config.yaml) | Espaços e finais de linha, YAML/JSON/TOML válidos, arquivos grandes, chaves privadas, **gitleaks**, **ruff**, **Conventional Commits**, markdownlint, shellcheck, bloqueio de commit na `main` | A cada commit e em `make lint` |
| [ci.yml](../.github/workflows/ci.yml) | Jobs *Lint*, *Test* e *Build* (Python e Node, com cache) | PR e push na `main` |
| [security.yml](../.github/workflows/security.yml) | gitleaks no histórico; trivy (vulnerabilidades, segredos, misconfig e licenças); actionlint; **CodeQL** (Python e TypeScript) | PR, push na `main` e toda segunda-feira |
| [release.yml](../.github/workflows/release.yml) | release-please: versão SemVer e CHANGELOG a partir dos commits; release com **SBOM assinado** (cosign) | Push na `main` |
| [scorecard.yml](../.github/workflows/scorecard.yml) | OpenSSF Scorecard | Push na `main` e semanal |
| [dependabot.yml](../.github/dependabot.yml) | Atualizações de pip, npm, Docker e Actions | Semanal |
| [CODEOWNERS](../.github/CODEOWNERS) | Revisão obrigatória do mantenedor | Com o ruleset ativo |
