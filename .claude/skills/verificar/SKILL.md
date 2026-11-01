---
name: verificar
description: Verifica se a mudança da branch funciona executando o sistema (CLI, API, interface, biblioteca ou CI) e observando o resultado, além de make check. Use antes de abrir PR.
argument-hint: "[o que verificar; padrão: mudanças da branch]"
disable-model-invocation: true
---

Pedido: $ARGUMENTS

Siga exatamente o prompt de `docs/prompts/07-verificar.md` (leia o arquivo agora).

- Rode `make check` primeiro; se falhar, pare e reporte.
- Não suba nada em produção, não aplique migração em banco real e não faça push.
- Entregue a evidência pronta para colar na seção "Verificação" do PR.
