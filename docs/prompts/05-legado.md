# 05 — Adequar um projeto existente ao template

## Passo 1 — Diagnóstico (somente leitura)

```text
Analise este repositório sem alterar nada e produza um diagnóstico comparando-o com
o padrão definido em AGENTS.md e docs/standards/ (do template).

Avalie e dê nota de 0 a 5 com evidências (arquivo:linha) para:
estrutura/arquitetura, qualidade de código, testes e cobertura, segurança
(segredos, deps vulneráveis, validação, autenticação), observabilidade, CI/CD,
documentação, gestão de dependências.

Liste os 10 maiores riscos ordenados por impacto × probabilidade.
```

## Passo 2 — Plano de adequação incremental

```text
Com base no diagnóstico, proponha um plano em etapas pequenas e independentes
(cada etapa = 1 PR revisável), nesta ordem:
1. Rede de segurança: CI, lint, scanners de segredo/vulnerabilidade, testes de caracterização
   nos fluxos críticos (sem mudar comportamento).
2. Correções de segurança críticas.
3. Reorganização estrutural gradual (strangler fig), módulo por módulo.
4. Melhorias de observabilidade e performance guiadas por medição.
Nada de reescrita total. Cada etapa deve manter o sistema funcionando.
```
