# Testes

## Pirâmide (proporção aproximada)

```text
        /\        e2e          ~10%  fluxos críticos pela interface pública
       /  \       integração   ~20%  adaptadores com dependências reais (Testcontainers)
      /____\      unitários    ~70%  domínio e casos de uso, sem I/O, milissegundos
```

## Regras

- Toda mudança de comportamento vem com teste. Todo bug corrigido ganha um teste que o reproduz.
- Teste **comportamento**, não implementação (não testar métodos privados).
- Nome descreve o cenário: `should_reject_order_when_stock_is_insufficient`
  / `rejeita pedido quando estoque é insuficiente`.
- Estrutura **Arrange–Act–Assert** (ou Given–When–Then), uma razão para falhar por teste.
- Testes independentes, determinísticos e paralelizáveis: sem ordem, sem `sleep`,
  relógio e aleatoriedade injetados (porta `Clock`, seed fixa).
- **Mocks só nas fronteiras** (portas). Não mocke o que você não controla — use *fakes*
  em memória para repositórios no teste unitário e o serviço real (container) no de integração.
- Dados de teste via *builders/factories*, não fixtures gigantes compartilhadas.

## Cobertura

- Meta: **≥ 80% em `domain` e `application`**; a CI falha se a cobertura cair.
- Cobertura é indicador, não objetivo. Considere *mutation testing* (Stryker, mutmut, PIT)
  no domínio para medir a qualidade real dos testes.

## Outros tipos

| Tipo         | Para quê                                  | Ferramentas (OSS)               |
| ------------ | ----------------------------------------- | ------------------------------- |
| Contrato     | Garantir compatibilidade de APIs          | Pact, Schemathesis (OpenAPI)    |
| Carga        | Validar NFRs de performance               | k6, Gatling, Locust             |
| Propriedade  | Encontrar casos de borda                  | Hypothesis, fast-check, jqwik   |
| Arquitetura  | Garantir regras de dependência            | ArchUnit, import-linter, dependency-cruiser |
