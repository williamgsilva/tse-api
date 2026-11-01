#!/usr/bin/env bash
# PostToolUse (Write|Edit): formata o código depois que a IA edita arquivos.
# Fica inativo enquanto o alvo `make format` não estiver implementado (branch lang/<stack>).
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
grep -q 'call todo,formatter' Makefile 2>/dev/null && exit 0
# Só formata quando o arquivo editado é código (docs/config não disparam o formatter).
file=$(sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
case "$file" in
  *.md | *.json | *.yml | *.yaml | *.txt | */.claude/*) exit 0 ;;
esac
make -s format >/dev/null 2>&1 || echo "make format falhou; rode-o manualmente para ver o erro." >&2
exit 0
