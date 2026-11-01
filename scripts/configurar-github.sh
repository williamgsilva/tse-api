#!/usr/bin/env bash
# Publica o projeto no GitHub como repositório PÚBLICO e aplica as regras de contribuição:
#   - main protegida: só entra por PR (squash), com CI verde, revisão do CODEOWNER e conversas resolvidas;
#     ninguém faz push direto, nem o dono (o dono pode mesclar os próprios PRs sem aprovação de terceiros);
#   - workflows de PRs vindos de forks só rodam depois de aprovados pelo mantenedor;
#   - alertas de dependências, correções automáticas, varredura de segredos e reporte privado de falhas.
# Idempotente: pode ser executado de novo para reaplicar as configurações.
#
# Uso:  gh auth login   (uma vez)
#       ./scripts/configurar-github.sh [dono/repositorio]
set -euo pipefail

cd "$(dirname "$0")/.."

REPO="${1:-williamgsilva/tse-api}"
DESCRIPTION="API e painel web com os dados públicos das eleições do TSE: mapa, resultados e boletim de urna de cada seção."
# Nomes dos jobs da CI exigidos para o merge (ci.yml e security.yml).
REQUIRED_CHECKS=(Lint Test Build Secrets Vulnerabilities Workflows)

step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[33mAVISO:\033[0m %s\n' "$1" >&2; }

command -v gh >/dev/null || { echo "Instale o GitHub CLI: https://cli.github.com" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Faça login antes: gh auth login" >&2; exit 1; }
git rev-parse --verify HEAD >/dev/null 2>&1 || {
  echo "Ainda não há commits. Faça o primeiro (ver docs/manutencao-do-repositorio.md)." >&2
  exit 1
}

step "Repositório público $REPO"
if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "Já existe."
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$REPO.git"
  git push -u origin main
else
  gh repo create "$REPO" --public --description "$DESCRIPTION" --source . --remote origin --push
fi

step "Configurações gerais (só squash merge, apagar branch após merge)"
gh api -X PATCH "repos/$REPO" --silent \
  -f description="$DESCRIPTION" \
  -F has_issues=true -F has_wiki=false -F has_projects=false \
  -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false \
  -F delete_branch_on_merge=true -F allow_update_branch=true \
  -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY
gh api -X PUT "repos/$REPO/topics" --silent \
  -f 'names[]=eleicoes' -f 'names[]=tse' -f 'names[]=dados-abertos' -f 'names[]=boletim-de-urna' \
  -f 'names[]=fastapi' -f 'names[]=react' -f 'names[]=brasil'

step "Segurança (alertas, correções automáticas, segredos, reporte privado)"
gh api -X PUT "repos/$REPO/vulnerability-alerts" --silent || warn "não foi possível ativar os alertas do Dependabot"
gh api -X PUT "repos/$REPO/automated-security-fixes" --silent || warn "não foi possível ativar as correções automáticas"
gh api -X PUT "repos/$REPO/private-vulnerability-reporting" --silent || warn "não foi possível ativar o reporte privado"
gh api -X PATCH "repos/$REPO" --silent --input - <<'JSON' || warn "não foi possível ativar a varredura de segredos"
{"security_and_analysis": {"secret_scanning": {"status": "enabled"},
                           "secret_scanning_push_protection": {"status": "enabled"}}}
JSON

step "GitHub Actions (token só leitura; release-please pode abrir PR; forks precisam de aprovação)"
gh api -X PUT "repos/$REPO/actions/permissions/workflow" --silent \
  -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true
gh api -X PUT "repos/$REPO/actions/permissions/fork-pr-contributor-approval" --silent \
  -f approval_policy=all_external_contributors ||
  warn "ajuste à mão: Settings → Actions → General → 'Require approval for all external contributors'"

step "Regras da branch main (ruleset)"
checks=$(printf '{"context":"%s"},' "${REQUIRED_CHECKS[@]}")
ruleset=$(
  cat <<JSON
{
  "name": "main protegida",
  "target": "branch",
  "enforcement": "active",
  "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
  "bypass_actors": [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "pull_request"}],
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "required_linear_history"},
    {"type": "pull_request", "parameters": {
      "required_approving_review_count": 1,
      "dismiss_stale_reviews_on_push": true,
      "require_code_owner_review": true,
      "require_last_push_approval": true,
      "required_review_thread_resolution": true,
      "allowed_merge_methods": ["squash"]
    }},
    {"type": "required_status_checks", "parameters": {
      "strict_required_status_checks_policy": true,
      "required_status_checks": [${checks%,}]
    }}
  ]
}
JSON
)
existing=$(gh api "repos/$REPO/rulesets" --jq '.[] | select(.name == "main protegida") | .id' | head -n 1)
if [[ -n "$existing" ]]; then
  echo "$ruleset" | gh api -X PUT "repos/$REPO/rulesets/$existing" --silent --input -
  echo "Ruleset atualizado (id $existing)."
else
  echo "$ruleset" | gh api -X POST "repos/$REPO/rulesets" --silent --input -
  echo "Ruleset criado."
fi

cat <<EOF

Pronto: https://github.com/$REPO

Fluxo a partir de agora (inclusive para você):
  git switch -c feat/minha-melhoria
  ... commits ...
  git push -u origin feat/minha-melhoria
  gh pr create --fill

Os checks ${REQUIRED_CHECKS[*]} passam a ser exigidos depois da primeira execução da CI.
EOF
