# Dados e migrações de banco

Mudanças de banco são uma das maiores causas de incidente: são difíceis de reverter e afetam
todos os usuários ao mesmo tempo. Regras:

## Migrações

- **Versionadas no repositório** e aplicadas por ferramenta (Flyway, Liquibase, Alembic,
  Prisma Migrate, golang-migrate, EF Core…). Nunca alterar o banco manualmente em produção.
- **Uma migração = uma mudança pequena.** Migração aplicada nunca é editada; corrija com outra.
- **Toda migração tem plano de reversão** (script *down* ou passo de rollback documentado).
- **Teste a migração** contra uma cópia com volume realista antes de produção
  (tempo de execução e locks).
- Migração roda **antes** do deploy do código que depende dela, em passo separado do pipeline.

## Mudanças sem downtime: *expand → migrate → contract*

Nunca renomeie ou remova uma coluna em um único passo. Exemplo para renomear `name` → `full_name`:

1. **Expand:** adicionar `full_name` (nullable); código novo escreve nas duas colunas.
2. **Migrate:** copiar os dados antigos em lotes (sem transação gigante).
3. Código passa a ler de `full_name`.
4. **Contract:** depois de estável (e de um deploy sem rollback), remover `name`.

## Cuidados de performance

- Índices em tabelas grandes: crie de forma concorrente/online (ex.: `CREATE INDEX CONCURRENTLY`).
- Evite `ALTER TABLE` que reescreve a tabela inteira em horário de pico.
- Atualizações em massa: em lotes, com pausa, idempotentes (podem ser reexecutadas).
- Toda consulta nova em tabela grande: verifique o plano (`EXPLAIN`) e os índices.

## Dados

- Chaves primárias opacas (UUIDv7/ULID) para recursos expostos na API.
- Datas em UTC; dinheiro em inteiro (centavos) ou decimal exato — nunca float.
- *Soft delete* só quando houver requisito; considere LGPD (direito à exclusão).
- Dados pessoais: classificados, minimizados e com retenção definida
  ([seguranca.md](seguranca.md#5-dados)).

## Backups

- Backup automático, criptografado e **com restauração testada periodicamente**
  (backup que nunca foi restaurado não é backup).
- Defina RPO (quanto dado pode perder) e RTO (em quanto tempo volta) no
  [overview](../architecture/overview.md).
