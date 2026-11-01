# Runbook — TSE API

Guia para quem está de plantão resolver problemas **sem precisar conhecer o código**.
Mantenha curto, testado e atualizado após cada incidente.

## Visão rápida

| Item | Valor |
| ---- | ----- |
| Serviço / URL | |
| Dashboards | |
| Logs | |
| Alertas (onde chegam) | |
| Dono / contato de escalonamento | |
| Dependências críticas | Banco, filas, serviços externos… |
| SLO | ex.: 99,5% das requisições < 300 ms |

## Health checks

- `GET /health/live` — processo vivo. Se falha: reiniciar a instância.
- `GET /health/ready` — dependências OK. Se falha: verificar qual dependência (ver logs).

## Procedimentos

Copie o bloco abaixo para cada alerta conhecido.

### Alerta: <nome do alerta>

- **Significa:** o que está acontecendo para o usuário.
- **Impacto:** quem é afetado e quão grave.
- **Diagnóstico:** onde olhar (dashboard, consulta de log, comando).
- **Mitigação:** passos numerados para estabilizar (rollback, desligar flag, escalar recurso).
- **Escalonar quando:** condição para chamar o próximo nível.

## Operações comuns

- Deploy e rollback: [deploy-e-rollback.md](deploy-e-rollback.md)
- Restaurar backup: <passo a passo testado>
- Rotacionar um segredo: <passo a passo>

## Depois do incidente

Abra um [postmortem](postmortem.md) e atualize este runbook com o que faltou.
