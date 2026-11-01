# 08 — Modo estudo (aprender fazendo)

Para quando o objetivo é **aprender**, não só entregar. A IA cuida do código repetitivo e
deixa as decisões importantes para você.

## Opção 1 — Nativo do Claude Code

`/config` → *Output style*:

- **Learning**: o Claude marca um `TODO(human)` no código e pede para você escrever as
  partes de decisão (tratamento de erro, estrutura de dados, regra de negócio), explicando o
  contexto e os trade-offs. Depois revisa o que você escreveu.
- **Explanatory**: o Claude faz o trabalho e explica as escolhas ao longo do caminho.

## Opção 2 — Prompt (qualquer ferramenta)

```text
Quero aprender enquanto desenvolvemos <tarefa>. Regras desta sessão:

1. Antes de começar, pergunte o que já sei sobre o assunto (uma pergunta só).
2. Você escreve o código repetitivo (estrutura, configuração, boilerplate).
3. Nas decisões de design (regra de negócio, tratamento de erro, estrutura de dados,
   algoritmo), NÃO escreva por mim: marque o ponto com TODO(human) e me explique o contexto,
   o que preciso fazer e os trade-offs a considerar. Espere eu implementar.
4. Revise o que eu escrevi: aponte erros com gentileza e explique o porquê.
5. Faça uma pergunta por vez. Quando eu travar, dê uma dica antes de dar a resposta.
6. Ao final de cada etapa, me peça para explicar com minhas palavras o que fizemos.
7. Relacione o que fizemos com docs/standards/ e indique uma referência para aprofundar.
```
