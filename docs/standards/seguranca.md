# Segurança

Referências: [OWASP Top 10](https://owasp.org/Top10/),
[OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) (alvo: nível 2),
[OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/), [SLSA](https://slsa.dev),
[OpenSSF](https://openssf.org). Princípio geral: **defesa em profundidade e menor privilégio.**

## 1. Segredos

- Nunca no código, no git, em logs ou em imagens Docker.
- Local: `.env` (ignorado pelo git). Produção: gerenciador de segredos
  (GitHub Actions Secrets/OIDC, AWS Secrets Manager, GCP Secret Manager, Vault/OpenBao, Infisical, SOPS).
- Detecção: `gitleaks` no pre-commit e na CI + *push protection* do GitHub.
- Vazou? **Revogue/rotacione imediatamente** — apagar do histórico não basta.
- **Agentes de IA:** o `.claude/settings.json` bloqueia a leitura de `.env*`/`secrets/` pelas
  ferramentas Read/Edit, e o hook `.claude/hooks/protect-secrets.sh` bloqueia comandos de shell
  que citam esses arquivos (as regras Read/Edit **não** se aplicam ao Bash). O sandbox do
  Claude Code (bubblewrap + socat no Linux) adiciona uma terceira camada. Ainda assim, o mais
  seguro é **não ter segredos de produção na máquina de desenvolvimento**.

## 2. Entrada e saída

- Validar **toda** entrada externa na borda (schema: tipo, tamanho, formato, faixa) — *allowlist*.
- SQL sempre parametrizado / via ORM. Nunca concatenar.
- Escapar saída conforme contexto (HTML, JS, URL, shell). Evite chamar shell com input do usuário.
- Upload: validar tipo real, tamanho, renomear, armazenar fora do webroot.
- Proteção contra SSRF ao buscar URLs informadas pelo usuário.

## 3. Autenticação e autorização

- Não implemente criptografia/autenticação do zero: use padrões (OIDC/OAuth 2.1) e provedores
  (Keycloak, Authentik, Zitadel — open source; ou Auth0/Cognito/Entra gerenciados).
- Senhas (se inevitável): Argon2id (ou bcrypt), nunca hash simples.
- MFA disponível; *rate limiting* e bloqueio progressivo em login.
- Autorização **no servidor**, em cada requisição, **negar por padrão**; checar posse do recurso (evita IDOR).
- Tokens curtos (access ≤ 15 min) + refresh rotativo; cookies `HttpOnly; Secure; SameSite`.

## 4. Transporte e headers

- TLS 1.2+ em tudo (inclusive interno). HSTS.
- Headers: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy`, `Permissions-Policy`, `frame-ancestors` via CSP.
- CORS restrito a origens conhecidas.

## 5. Dados

- Classifique dados (público / interno / confidencial / pessoal-sensível) — **LGPD**.
- Minimização: colete só o necessário; defina retenção e exclusão.
- Criptografia em repouso para dados sensíveis; backups testados e criptografados.
- Logs sem PII completa (mascarar: `***.***.123-**`).

## 6. Cadeia de suprimentos (supply chain)

- Lockfile obrigatório; versões fixadas; atualizações via Dependabot/Renovate.
- **Licenças:** o trivy (`make security` e CI) falha em licenças restritivas (ex.: GPL/AGPL)
  em dependências. Se o projeto aceitar alguma, registre a exceção num ADR.
- Scanner de vulnerabilidades em deps e imagens (`trivy`) na CI, com *gate* em HIGH/CRITICAL.
- Gerar **SBOM** (`trivy fs --format cyclonedx` ou `syft`) em cada release.
- Assinar imagens/artefatos ([cosign/Sigstore](https://www.sigstore.dev)) e gerar *provenance* (SLSA).
- GitHub Actions: `permissions` mínimas, `persist-credentials: false`, actions de fontes confiáveis
  **fixadas por SHA** (tags são mutáveis — ver o incidente `tj-actions/changed-files`, 2025), OIDC em vez de chaves de nuvem longas.

## 7. Containers

- Imagem base mínima (distroless / alpine / chainguard / wolfi), multi-stage build.
- Usuário **não-root**, filesystem read-only quando possível, sem segredos em `ENV`/camadas.
- Fixar versão da base; escanear imagem na CI.

## 8. Testes de segurança

| Tipo                  | Ferramenta (open source)                  | Quando       |
| --------------------- | ----------------------------------------- | ------------ |
| Segredos              | gitleaks                                  | commit + CI  |
| SCA (dependências)    | trivy / osv-scanner                       | CI + semanal |
| SAST                  | CodeQL (grátis p/ público), Semgrep CE    | CI           |
| IaC / misconfig       | trivy misconfig / checkov                 | CI           |
| DAST                  | OWASP ZAP (baseline scan)                 | staging      |

## 9. Resposta a incidentes

Processo em [SECURITY.md](../../SECURITY.md). Mantenha logs de auditoria
(quem, o quê, quando) para ações sensíveis.

## 10. Aplicações e agentes de IA

Referência: [OWASP Top 10 para aplicações LLM](https://genai.owasp.org/llm-top-10/).

**Ao construir features com LLM:**

- **Prompt injection** (direta e indireta): todo texto vindo de usuário, documento, página web
  ou ferramenta é **dado, não instrução**. Separe instruções de conteúdo e nunca dê ao modelo
  permissões que o usuário não teria.
- **Agência excessiva:** ferramentas do modelo com menor privilégio, escopo e limite de
  execuções; ações irreversíveis (pagamento, exclusão, e-mail) exigem confirmação humana.
- **Saída do modelo é entrada não confiável:** valide/escape antes de usar em SQL, shell, HTML
  ou chamadas de API.
- **Vazamento de dados:** não envie segredos ou PII desnecessária ao modelo; verifique a política
  de retenção do fornecedor; mascare dados sensíveis nos logs de prompts.
- **Custos e abuso:** rate limit e limite de tokens por usuário.

**Ao usar agentes de código neste repositório:**

- Servidores **MCP** só de fontes confiáveis, com o menor escopo possível; revise `.mcp.json` em PR
  como código (ele pode executar programas e acessar dados).
- Conteúdo de issues, PRs, páginas web e dependências pode conter instruções maliciosas:
  o agente deve tratá-lo como dado (regra no `AGENTS.md`).
- Loops autônomos só com limites ([10-loop-autonomo.md](../prompts/10-loop-autonomo.md)).
- Modelagem de ameaças para features sensíveis: [threat-model.md](../security/threat-model.md).
