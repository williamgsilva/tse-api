# 07 — Verificar em execução

Testes e typecheck provam que a CI passa, não que a mudança funciona para quem usa.
**Verificar é executar o sistema, levar o fluxo até o código alterado e observar o resultado.**
Rode depois de `make check` e antes de abrir o PR.

```text
Verifique que a mudança desta branch funciona de verdade (git diff main...HEAD).

1. Leia o diff e a descrição da tarefa. Se os dois discordarem, isso já é um achado.
2. Identifique a superfície onde o usuário (pessoa ou sistema) encontra a mudança:
   - CLI: execute o comando e capture a saída
   - API/servidor: suba a aplicação e envie a requisição (curl/httpie), capture a resposta
   - Interface web: abra no navegador (ou Playwright) e capture a tela
   - Biblioteca: use pela API pública do pacote, não importando arquivos internos
   - Pipeline de CI: dispare o workflow e leia a execução
   Função interna não é superfície: siga até quem a chama e chegue a uma das opções acima.
3. Exercite o caminho feliz, pelo menos um caso de erro e um caso de borda.
4. Não conta como verificação: rodar testes de novo, importar a função e chamá-la num
   script, ou "ler o código e concluir que está certo".

Entregue: comandos executados, saída observada (resumida) e veredito por cenário
(funciona / não funciona / não foi possível verificar, e o motivo).
```

Cole a evidência (comandos + saída ou print) na seção **Verificação** do PR.
