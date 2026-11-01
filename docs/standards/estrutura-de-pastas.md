# Estrutura de pastas

Princípio: **organizar por negócio (módulo) primeiro, por camada técnica depois.**
Quem abre `src/modules/` deve entender *o que o sistema faz*, não *qual framework usa*.

```text
src/
├── bootstrap/                 # composition root: lê config, instancia adaptadores, injeta dependências, sobe o servidor
├── shared/                    # shared kernel: só o que é realmente transversal e estável
│   ├── config/                #   carregamento/validação de configuração (env)
│   ├── observability/         #   logger, tracing, métricas
│   └── errors/                #   tipos de erro base
└── modules/
    └── <modulo>/              # ex.: users, billing, catalog
        ├── domain/            # entidades, value objects, regras, eventos, PORTAS (interfaces)
        ├── application/       # casos de uso (1 por arquivo), DTOs de entrada/saída
        ├── infrastructure/    # ADAPTADORES de saída: repositórios (BD), clientes HTTP, filas
        ├── interfaces/        # ADAPTADORES de entrada: controllers HTTP, CLI, consumers
        └── index / api        # API pública do módulo (único ponto que outros módulos importam)

tests/
├── unit/                      # domínio e casos de uso, sem I/O (rápidos, maioria)
├── integration/               # adaptadores contra dependências reais (Testcontainers)
└── e2e/                       # fluxos ponta a ponta pela interface pública
```

> Escolha do estilo e mapeamento por linguagem: [arquitetura.md](arquitetura.md).
>
> Algumas linguagens têm convenção própria (ex.: testes ao lado do código em Go/Rust,
> `src/main` + `src/test` em Java). A branch `lang/<stack>` adapta **o layout**, mas
> mantém **os mesmos conceitos e regras de dependência**.

## Regras de dependência

```text
interfaces ──► application ──► domain ◄── infrastructure
                                  ▲
                           (portas definidas aqui,
                         implementadas na infraestrutura)
```

| Camada           | Pode importar                       | Não pode importar                   |
| ---------------- | ----------------------------------- | ----------------------------------- |
| `domain`         | apenas `shared` (tipos básicos)     | framework, ORM, HTTP, SDKs, outras camadas |
| `application`    | `domain`, `shared`                  | `infrastructure`, `interfaces`      |
| `infrastructure` | `domain`, `application`, `shared`, libs externas | `interfaces`            |
| `interfaces`     | `application`, `shared`             | `infrastructure` diretamente        |
| `bootstrap`      | tudo (é onde as peças são ligadas)  | —                                   |

Entre módulos: importar **somente** a API pública do outro módulo. Proibido acessar
tabelas, repositórios ou entidades internas de outro módulo.

## Nomenclatura de arquivos

- Um conceito por arquivo; nome do arquivo = nome do conceito.
- Casos de uso com verbo: `create_order`, `CreateOrder`, `create-order` (siga a convenção da linguagem).
- Portas com nome de capacidade: `OrderRepository`, `PaymentGateway`, `Clock`.
- Adaptadores com a tecnologia no nome: `PostgresOrderRepository`, `StripePaymentGateway`.

## Quando NÃO usar toda essa estrutura

Scripts, CLIs pequenas ou protótipos descartáveis: comece com um único módulo e poucas
pastas. A estrutura completa vale a partir do momento em que há regra de negócio real.
