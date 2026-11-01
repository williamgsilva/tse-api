---
name: adr
description: Registra uma decisão de arquitetura como ADR em docs/architecture/adr/ a partir do modelo 0000-template.md, comparando opções e trade-offs. Use quando uma decisão for cara de reverter, afetar vários módulos ou escolher tecnologia/fornecedor.
argument-hint: "<decisão a registrar>"
---

Decisão: $ARGUMENTS

1. Leia `docs/architecture/overview.md`, os ADRs existentes e `docs/architecture/adr/0000-template.md`.
2. Se a decisão ainda não foi tomada, siga `docs/prompts/02-arquitetura.md` para comparar opções.
3. Crie `docs/architecture/adr/NNNN-<titulo-em-kebab-case>.md` com o próximo número livre,
   status "Proposto" e a data de hoje.
4. Se o ADR substitui outro, atualize o status do antigo para "Substituído por NNNN".
5. Atualize a seção "Decisões" de `docs/architecture/overview.md` com o link.
