# Deploy e rollback

## Princípios

- **Deploy automatizado** pelo pipeline; ninguém faz deploy da própria máquina.
- **Mesmo artefato** em todos os ambientes (build uma vez, promova staging → produção).
- **Configuração por ambiente** via variáveis/segredos, nunca no artefato.
- **Pequeno e frequente:** deploys pequenos têm risco pequeno e rollback fácil.
- **Feature nova arriscada atrás de feature flag** ([git.md](../standards/git.md#feature-flags)):
  separa *deploy* (código no ar) de *release* (usuário vê).

## Checklist antes do deploy

- [ ] CI verde (lint, testes, segurança) e PR aprovado
- [ ] Migrações compatíveis com a versão anterior do código ([expand → contract](../standards/dados-e-migracoes.md))
- [ ] Novas variáveis de ambiente e segredos já configurados no ambiente de destino
- [ ] Métricas e alertas para a mudança existem (como saberemos se quebrou?)
- [ ] Plano de rollback conhecido (abaixo) e testado em staging quando houver migração

## Estratégias

| Estratégia | Como funciona | Quando usar |
| ---------- | ------------- | ----------- |
| Rolling | Substitui instâncias aos poucos | Padrão para serviços sem estado |
| Blue/green | Sobe a versão nova ao lado e troca o tráfego de uma vez | Rollback instantâneo é crítico |
| Canary | Envia uma fração do tráfego para a versão nova e observa | Mudanças de alto risco com tráfego relevante |

## Depois do deploy (15–30 min)

- Acompanhe taxa de erro, latência (p95/p99) e métricas de negócio do fluxo alterado.
- Compare com o período anterior. Na dúvida, **faça rollback primeiro e investigue depois**.

## Rollback

1. Reverter para o artefato anterior pelo pipeline (redeploy da versão/tag anterior).
2. Se a feature está atrás de flag: **desligue a flag** (mais rápido que redeploy).
3. Migração de banco: só reverta se o script *down* foi testado; prefira corrigir para frente
   quando a migração seguiu *expand → contract*.
4. Registre o incidente e abra o [postmortem](postmortem.md) se houve impacto para usuários.
