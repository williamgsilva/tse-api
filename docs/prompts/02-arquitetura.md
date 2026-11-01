# 02 — Decisão de arquitetura / tecnologia

```text
Leia docs/architecture/overview.md e os ADRs existentes em docs/architecture/adr/.

Preciso decidir: <decisão, ex.: linguagem e framework do backend | banco de dados | autenticação | hospedagem>.

Contexto adicional:
- Experiência do time: <ex.: forte em X, básico em Y>
- Orçamento mensal de infraestrutura: <valor>
- Preferência: open source; serviço pago apenas se reduzir custo/risco operacional.

Faça:
1. Liste 3 opções viáveis e compare em tabela: adequação aos requisitos não funcionais,
   maturidade/comunidade, licença, segurança (histórico de CVEs, suporte), custo total,
   curva de aprendizado, lock-in.
2. Recomende uma opção e explique os trade-offs, incluindo quando ela deixaria de ser a melhor escolha.
3. Cite fontes oficiais (documentação, páginas de release) para as afirmações importantes.
4. Escreva o ADR em docs/architecture/adr/NNNN-<titulo>.md seguindo 0000-template.md,
   com status "Proposto".

Não implemente nada ainda.
```
