# Observabilidade e performance

## Observabilidade — os três sinais

Padrão aberto: **[OpenTelemetry](https://opentelemetry.io)** (evita *lock-in* de fornecedor).

| Sinal     | O quê                                  | Stack OSS sugerida                      |
| --------- | -------------------------------------- | --------------------------------------- |
| Logs      | JSON estruturado com `trace_id`        | Loki / OpenSearch                       |
| Métricas  | RED (Rate, Errors, Duration) + USE     | Prometheus + Grafana                    |
| Traces    | Requisições ponta a ponta              | Tempo / Jaeger                          |

Opções gerenciadas econômicas: Grafana Cloud (free tier), Honeycomb, SigNoz Cloud.

### Mínimo obrigatório

- Logs estruturados com correlação (`trace_id`, `request_id`).
- Métricas RED por endpoint; métricas de negócio relevantes (ex.: pedidos criados).
- Health checks `live` e `ready`.
- **SLOs** definidos a partir dos NFRs (ex.: 99,5% das requisições < 300 ms) e alertas
  sobre *burn rate* do SLO — não sobre cada erro isolado.

## Performance

Regra de ouro: **meça antes de otimizar.** Otimização sem perfil é palpite.

1. Defina metas (NFRs) com números.
2. Meça (teste de carga com k6 + profiler da linguagem).
3. Ataque o maior gargalo; repita.

### Checklist comum (resolve a maioria dos casos)

- [ ] Sem N+1 queries; índices nas colunas de filtro/junção (analise com `EXPLAIN`)
- [ ] Paginação em todas as listas
- [ ] Pool de conexões dimensionado; timeouts em toda chamada externa
- [ ] Cache onde a leitura domina (HTTP cache headers, Redis/Valkey) com invalidação clara
- [ ] Trabalho pesado/lento em fila assíncrona (não no request)
- [ ] Compressão (gzip/brotli) e payloads enxutos
- [ ] Retries com *backoff* exponencial + jitter; *circuit breaker* para dependências instáveis
- [ ] Teste de carga no pipeline de release para endpoints críticos
