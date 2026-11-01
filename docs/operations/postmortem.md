# Postmortem (modelo, sem culpados)

> Copie para `docs/operations/postmortems/AAAA-MM-DD-<titulo>.md`.
> Foco em **sistemas e processos**, não em pessoas: "o deploy permitiu X", não "fulano fez X".

## Resumo

- **Data/hora (UTC):** início — detecção — mitigação — resolução
- **Duração do impacto:**
- **Severidade:** SEV1 (indisponível) · SEV2 (degradado para muitos) · SEV3 (degradado para poucos)
- **Impacto:** usuários afetados, funcionalidades, dados, custo

## Linha do tempo

| Horário (UTC) | Evento |
| ------------- | ------ |
| | Primeiro sinal / alerta |
| | Ação tomada |
| | Mitigado |

## Causa raiz

Use "5 porquês" até chegar a uma causa sistêmica (processo, teste ausente, alerta ausente),
não a "erro humano".

## O que funcionou / o que não funcionou

- Funcionou:
- Não funcionou:
- Tivemos sorte em:

## Ações

| Ação | Tipo (prevenir / detectar / mitigar) | Responsável | Issue | Prazo |
| ---- | ------------------------------------ | ----------- | ----- | ----- |
| | | | | |

Cada ação vira issue. Atualize o [runbook](runbook.md) e, se for decisão de arquitetura, um ADR.
