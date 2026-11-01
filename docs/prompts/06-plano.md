# 06 — Plano "decisão completa"

Use antes de qualquer tarefa não trivial. O objetivo é um plano que outra pessoa (ou outro
agente) consiga executar **sem precisar tomar nenhuma decisão**.

```text
Tarefa: <descrição ou issue #N>

Fase de PLANEJAMENTO — somente leitura:
- Pode: ler e buscar arquivos, rodar testes e comandos que não alteram arquivos versionados.
- Não pode: editar arquivos, rodar formatter que reescreve, aplicar migrações, commitar.
Mesmo que eu peça para executar nesta fase, trate como pedido para planejar a execução.

1. Explore o código relevante antes de supor qualquer coisa. Procure funções e padrões
   existentes que possam ser reutilizados.
2. Se houver ambiguidade de requisito ou decisão de negócio, me pergunte (no máximo 3
   perguntas por vez, cada uma com sua recomendação).
3. Entregue o plano neste formato:

## Objetivo
O problema e o resultado esperado, em 2–3 frases.

## Decisões
Cada decisão tomada e o motivo (bibliotecas, formato de dados, nomes, tratamento de erro).
Nada fica "a definir".

## Mudanças
Por módulo e camada (domain/application/infrastructure/interfaces): arquivos a criar ou
alterar e o que muda em cada um. Cite as funções existentes que serão reutilizadas.

## Testes
Casos de teste (unitário, integração, e2e) que provam os critérios de aceite.

## Riscos
Segurança, performance, migração de dados, compatibilidade de API, rollback.

## Verificação
Como provar que funciona rodando o sistema (ver 07-verificar.md), além de `make check`.
```

> No Claude Code, o *plan mode* (Shift+Tab) aplica a restrição de somente leitura de forma
> automática.
