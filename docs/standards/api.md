# APIs

## Contrato primeiro

- Descreva a API em **OpenAPI 3.1** (REST) / AsyncAPI (eventos) / `.proto` (gRPC) e versione junto do código.
- Gere documentação e, quando possível, clientes/validação a partir do contrato.

## REST — convenções

- Recursos no plural, substantivos: `GET /v1/orders/{id}`, `POST /v1/orders`.
- Verbos HTTP com semântica correta; `PUT` idempotente, `PATCH` parcial.
- JSON em `camelCase` (ou `snake_case` — escolha um por projeto e registre em ADR).
- Datas em ISO 8601 UTC (`2026-10-05T13:00:00Z`); dinheiro em inteiro de centavos ou decimal string + moeda.
- IDs opacos (UUIDv7/ULID), nunca sequenciais expostos.
- Paginação por cursor (`?limit=50&cursor=...`) para listas grandes.
- Versionamento no path (`/v1`). Mudança incompatível → nova versão + período de depreciação.
- **Idempotência** em operações de criação/pagamento via header `Idempotency-Key`.

## Status e erros

Erros no formato **Problem Details (RFC 9457)**:

```json
{
  "type": "https://api.exemplo.com/errors/insufficient-stock",
  "title": "Estoque insuficiente",
  "status": 422,
  "detail": "O item SKU-123 possui apenas 2 unidades.",
  "instance": "/v1/orders",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736"
}
```

| Código | Uso                                             |
| ------ | ----------------------------------------------- |
| 200/201/204 | sucesso / criado / sem conteúdo            |
| 400    | requisição malformada                           |
| 401    | não autenticado                                 |
| 403    | autenticado sem permissão                       |
| 404    | não encontrado (também para recurso de outro dono, evitando enumeração) |
| 409    | conflito de estado                              |
| 422    | regra de negócio violada / validação semântica  |
| 429    | rate limit (com `Retry-After`)                  |
| 5xx    | erro do servidor — sem detalhes internos        |

## Operação

- Rate limiting, timeouts e limites de payload em todas as rotas.
- Health checks: `/health/live` (processo vivo) e `/health/ready` (dependências OK).
- Propagar `traceparent` (W3C Trace Context) entre serviços.
