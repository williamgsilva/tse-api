# 0002 — Monólito modular com arquitetura hexagonal

- **Status:** Aceito (padrão do template — revise por projeto)
- **Data:** 2026-10-05

## Contexto

Alternativas e critérios de escolha: [docs/standards/arquitetura.md](../../standards/arquitetura.md).

Precisamos de uma estrutura que seja simples para começar, fácil de testar, que isole
regras de negócio de frameworks e infraestrutura, e que permita evoluir (inclusive
extrair serviços) sem reescrita.

## Opções consideradas

1. **Microsserviços desde o início** — escala e deploy independentes; porém alto custo
   operacional (rede, observabilidade distribuída, consistência eventual) sem benefício no início.
2. **Monólito em camadas tradicional (MVC)** — simples, mas tende a acoplar regras ao
   framework/ORM e vira "big ball of mud".
3. **Monólito modular + hexagonal (ports & adapters)** — um deploy, módulos com fronteiras
   claras, domínio independente de infraestrutura.

## Decisão

Opção 3.

- **Módulos por capacidade de negócio** (ex.: `billing`, `users`), cada um com API pública.
- Dentro de cada módulo, camadas hexagonais:
  - `domain` — entidades, value objects, regras, **portas** (interfaces). Sem I/O.
  - `application` — casos de uso; orquestram o domínio via portas.
  - `infrastructure` — **adaptadores** de saída (BD, filas, APIs externas).
  - `interfaces` — adaptadores de entrada (HTTP, CLI, consumers).
- Regra de dependência: `interfaces → application → domain ← infrastructure`.
- Módulos se comunicam por API pública ou eventos internos — nunca por tabelas uns dos outros.

## Consequências

- **Positivas:** domínio testável sem banco/framework; troca de tecnologia localizada;
  módulos podem virar serviços quando houver necessidade real.
- **Negativas:** mais arquivos/interfaces que um CRUD simples; exige disciplina
  (verificar com ferramenta de *architecture lint* da stack na branch `lang/*`).
- **A fazer:** configurar verificação automática de dependências entre camadas
  (ex.: import-linter, dependency-cruiser, ArchUnit, go-arch-lint).
