# 03 — Implementar uma feature

Use **depois** de ter um plano aprovado: [06-plano.md](06-plano.md) (`/planejar`) para tarefas
pequenas ou as tarefas de uma spec [09-spec.md](09-spec.md) (`/spec`) para features maiores.

## Implementação

```text
Plano aprovado. Implemente em pequenos passos:
1. Testes do domínio (falhando) → domínio → testes passando.
2. Caso de uso + testes com fakes das portas.
3. Adaptadores + testes de integração.
4. Interface de entrada + teste e2e do fluxo.
Ao final rode `make check` e corrija tudo. Atualize docs/OpenAPI/glossário se aplicável
(o CHANGELOG é gerado pelo release-please a partir dos commits).
Resuma o que mudou e sugira a mensagem de commit (Conventional Commits).
```
