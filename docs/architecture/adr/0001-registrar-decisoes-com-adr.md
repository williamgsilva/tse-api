# 0001 — Registrar decisões de arquitetura com ADR

- **Status:** Aceito
- **Data:** 2026-10-05

## Contexto

Decisões técnicas se perdem em conversas e PRs. Meses depois ninguém sabe *por que*
algo foi feito, e a decisão é refeita (ou revertida) sem considerar o contexto original.
Agentes de IA também precisam desse histórico para sugerir mudanças coerentes.

## Decisão

Registrar toda decisão arquiteturalmente significativa como um ADR
([Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions))
em `docs/architecture/adr/NNNN-titulo.md`, a partir de `0000-template.md`.

É significativa a decisão que: é cara de reverter, afeta vários módulos, escolhe
tecnologia/fornecedor, ou altera um requisito não funcional.

ADRs são imutáveis depois de aceitos: para mudar, crie um novo ADR que *substitui* o anterior.

## Consequências

- Histórico de decisões versionado junto do código e revisado em PR.
- Pequeno custo de escrita por decisão (~15 min).
