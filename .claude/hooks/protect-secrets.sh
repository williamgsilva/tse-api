#!/usr/bin/env bash
# PreToolUse (Bash): bloqueia comandos que acessam segredos.
# As regras Read()/Edit() do settings.json só valem para as ferramentas Read/Edit;
# sem este hook, `cat .env` pelo Bash leria o arquivo (comandos de leitura rodam sem pedir).
# Entrada: JSON do Claude Code no stdin. Saída 2 = bloqueia, com o motivo no stderr.
set -euo pipefail

input=$(cat)

# .env.example é documentação e pode ser lido.
sanitized=${input//.env.example/}

# Arquivos .env reais: .env, .env.local, .env.<ambiente>, .env.*.local
env_file='(^|[[:space:]/"'\''=:<])\.env(\.[[:alnum:]_.-]+)?([[:space:]"'\'';|&>)]|$)'
# Diretório secrets/ e chaves privadas
secret_path='(^|[[:space:]/"'\''=:<])secrets/|\.(pem|key|p12|pfx)([[:space:]"'\'';|&>)]|$)'

if grep -Eq "$env_file" <<<"$sanitized" || grep -Eq "$secret_path" <<<"$sanitized"; then
  echo "Bloqueado por .claude/hooks/protect-secrets.sh: o comando acessa .env, secrets/ ou chave privada. Use .env.example para ver as variáveis." >&2
  exit 2
fi
exit 0
