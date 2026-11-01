# 04 — Code review

Dois prompts: **review geral** (bugs + qualidade) e **review de segurança**. Rode os dois
antes do review humano. São independentes: um procura bugs, o outro procura vulnerabilidades.

## Review geral (por ângulos)

```text
Revise as mudanças desta branch em relação à main (git diff main...HEAD, mais as mudanças
não commitadas em git diff HEAD). Use AGENTS.md e docs/standards/ como critério.

Analise cada ângulo (A a I) separadamente, sem misturar:

A. Linha a linha — para cada linha alterada pergunte: que entrada, estado, timing ou
   plataforma torna esta linha errada? (condição invertida, off-by-one, nulo, await
   esquecido, zero tratado como falso, variável errada por copiar/colar, erro engolido).
   Leia a função inteira em volta: bug em linha não alterada de função tocada também conta.
B. Comportamento removido — para cada linha apagada ou substituída, diga que garantia ela
   dava (validação, tratamento de erro, teste) e onde o código novo restabelece essa
   garantia. Se não restabelece, é um achado.
C. Chamadas cruzadas — para cada função alterada, encontre quem a chama e verifique se a
   mudança quebra algum chamador (nova pré-condição, retorno diferente, nova exceção).
D. Arquitetura — regra de dependência entre camadas e módulos (docs/standards/estrutura-de-pastas.md).
E. Testes — o comportamento alterado está coberto? Os testes falhariam se o código estivesse errado?
F. Reuso e simplificação — código que reimplementa algo existente (cite o helper),
   complexidade desnecessária, estado derivável, código morto.
G. Eficiência — trabalho repetido, I/O em loop, N+1, operações independentes em sequência.
H. Causa raiz — a correção ataca a causa ou só tapa o sintoma com um caso especial?
I. Falhas silenciosas — catch vazio ou genérico demais, erro convertido em null/lista
   vazia/valor padrão sem log, fallback que esconde a falha do usuário, log sem contexto ou
   com nível errado, stack trace perdido ao relançar, I/O de rede/arquivo/banco sem timeout,
   operação em várias etapas sem rollback, mock/fake usado fora dos testes.

Para cada achado:
- arquivo:linha
- severidade (alta / média / baixa)
- cenário de falha concreto: "com a entrada X no estado Y, acontece Z" (obrigatório)
- correção sugerida

Regras:
- Sem cenário de falha concreto, não é achado: descarte.
- Agrupe achados duplicados (mesma linha ou mesmo mecanismo).
- Não comente estilo que o formatter/linter já cobre.
- Ordene por severidade. Se um ângulo não tiver achados, diga isso em uma linha.
```

## Review de segurança

```text
Atue como engenheiro de segurança sênior. Revise somente as vulnerabilidades INTRODUZIDAS
pelas mudanças desta branch (git diff main...HEAD). Problemas antigos ficam fora.

Antes de julgar, pesquise no repositório quais proteções já existem (validação, ORM,
escape de templates, middleware de autenticação) para não reportar o que já está protegido.

Categorias:
- Injeção: SQL/NoSQL, comando de shell, template, XXE, path traversal, SSRF
- Autenticação e autorização: bypass, escalada de privilégio, IDOR, sessão, JWT
- Criptografia e segredos: chave/senha no código, algoritmo fraco, aleatoriedade insegura,
  validação de certificado desligada
- Execução de código: desserialização insegura, eval, XSS (refletido, armazenado, DOM)
- Exposição de dados: PII/segredos em log ou resposta, detalhes internos em erros

Regras:
- Reporte apenas o que tiver confiança > 80% de ser explorável, com o caminho de ataque
  (de onde vem a entrada controlada pelo atacante até o ponto vulnerável).
- Fora de escopo (tratados por outros processos): negação de serviço, rate limiting,
  segredos em disco já cobertos pelo gitleaks.
- Para cada achado: arquivo:linha, severidade, caminho de ataque, correção.
- Se não houver nada com confiança suficiente, diga "nenhuma vulnerabilidade encontrada".
```

> No Claude Code, os comandos nativos `/code-review` e `/security-review` aplicam o mesmo
> método. Estes prompts servem para qualquer ferramenta e documentam o critério do time.
