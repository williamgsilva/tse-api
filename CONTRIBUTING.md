# Como contribuir

Contribuições são bem-vindas: correções, melhorias, novos dados do TSE, documentação e testes.
Todo trabalho entra pelo mesmo caminho: **uma branch nova e um pull request (PR)**. Ninguém, nem o
mantenedor, faz commit direto na `main`; ela é protegida e só recebe mudanças por PR revisado e com a CI verde.

Ao participar, você concorda com o [Código de Conduta](CODE_OF_CONDUCT.md).

## Antes de começar

- **Bug ou melhoria pequena:** abra uma [issue](https://github.com/williamgsilva/tse-api/issues/new/choose)
  ou vá direto para o PR.
- **Mudança grande** (novo módulo, nova fonte de dados, mudança no contrato da API): abra uma issue primeiro
  para combinar a abordagem. Isso evita retrabalho.
- **Vulnerabilidade:** não abra issue pública; siga o [SECURITY.md](SECURITY.md).

## Passo a passo

1. **Faça um fork** do repositório (botão *Fork* no GitHub) e clone o seu fork:

   ```bash
   git clone https://github.com/<seu-usuario>/tse-api.git
   cd tse-api
   git remote add upstream https://github.com/williamgsilva/tse-api.git
   make setup
   ```

2. **Crie uma branch nova** a partir da `main` atualizada, com o padrão `<tipo>/<descricao-curta>`
   (com o número da issue, se houver):

   ```bash
   git fetch upstream
   git switch -c feat/42-mapa-por-zona upstream/main
   ```

   Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `chore`.

3. **Faça as mudanças** seguindo os padrões do projeto ([docs/standards/](docs/standards/)) e o
   [AGENTS.md](AGENTS.md) (que vale também para quem programa com IA). Comportamento novo vem com teste.

4. **Escreva os commits** no padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/), em
   português: `feat: mapa por zona eleitoral`, `fix: fuso do oeste do Amazonas`. O hook do `make setup`
   confere a mensagem. Esse padrão alimenta a versão e o CHANGELOG automáticos.

5. **Confira localmente:**

   ```bash
   make check   # lint (ruff, mypy, import-linter, eslint, tsc, prettier), testes e segurança
   ```

6. **Envie a branch para o seu fork e abra o PR** contra a `main` deste repositório:

   ```bash
   git push -u origin feat/42-mapa-por-zona
   ```

   Preencha o modelo do PR: o que mudou, por quê e a **evidência de que funciona** (comando e saída,
   requisição e resposta, ou captura de tela).

## O que acontece depois do PR

1. **CI:** no primeiro PR de um novo contribuidor, o mantenedor aprova a execução dos workflows (proteção do
   GitHub contra abuso). Depois rodam os checks obrigatórios: `Lint`, `Test`, `Build`, `Secrets`,
   `Vulnerabilities` e `Workflows`.
2. **Revisão:** o mantenedor (ver [CODEOWNERS](.github/CODEOWNERS)) revisa. Pedidos de ajuste são normais;
   envie novos commits na mesma branch. Novos commits invalidam aprovações anteriores.
3. **Merge:** com a CI verde, a aprovação e as conversas resolvidas, o PR entra por *squash merge* (um commit
   por PR, com o título do PR). Por isso **o título do PR também segue Conventional Commits**.
4. A branch é apagada depois do merge.

Mantenha seu fork atualizado com `git fetch upstream && git rebase upstream/main` na sua branch.

## Definition of Done

Um PR está pronto para revisão quando:

- [ ] Resolve uma coisa só e é pequeno (idealmente menos de 400 linhas)
- [ ] Tem testes novos ou ajustados, e a cobertura não caiu
- [ ] Foi verificado em execução, com evidência no PR ([07-verificar](docs/prompts/07-verificar.md))
- [ ] `make check` passa
- [ ] Não traz segredos, dados pessoais nem arquivos grandes baixados do TSE (`data/` fica fora do git)
- [ ] A documentação foi atualizada quando necessário: README, ADR em
  [docs/architecture/adr/](docs/architecture/adr/), [glossário](docs/glossario.md), `.env.example`
- [ ] Respeita a arquitetura: dependências apontam para dentro e módulos só se falam pela API pública
  (o `import-linter` confere)

## Dados e fontes

- Use só fontes **públicas e oficiais** (TSE, IBGE). Não inclua dados pessoais de eleitores.
- Não versione arquivos baixados (`data/`). Para testes, use recortes pequenos em `tests/fixtures/`, sem
  alterar o conteúdo original (os fixtures são preservados byte a byte).
- Números estimados (como votos por candidato depois de um horário) precisam ser identificados como
  estimativa na API e no painel.

## Licença das contribuições

O projeto usa a [licença MIT](LICENSE). Ao enviar um PR, você concorda que sua contribuição seja
distribuída sob essa mesma licença.

## Para o mantenedor

A configuração do repositório (proteção da `main`, merge só por squash, aprovação de workflows de forks,
alertas de segurança) está em [docs/manutencao-do-repositorio.md](docs/manutencao-do-repositorio.md) e é
aplicada por `scripts/configurar-github.sh`.
