# Arquitetura: princípios, estilos e como escolher

Padrões de arquitetura existem em vários níveis, e **a maioria não depende da linguagem**:
o conceito é o mesmo, muda o idioma de implementação. Este guia complementa a decisão padrão
do template ([ADR 0002](../architecture/adr/0002-monolito-modular-hexagonal.md)) e a
[estrutura de pastas](estrutura-de-pastas.md).

## 1. Níveis de padrões

| Nível | Exemplos | Depende da linguagem? |
| ----- | -------- | --------------------- |
| Princípios | Coesão alta / acoplamento baixo, separação de responsabilidades, SOLID, regra de dependência, *information hiding*, KISS/YAGNI | Não |
| Estilos arquiteturais | Camadas, hexagonal / clean / onion, monólito modular, microsserviços, orientado a eventos, CQRS / Event Sourcing, serverless, pipes & filters, microkernel | Não |
| Padrões distribuídos | Outbox, Saga, Circuit breaker, Retry com backoff + jitter, Idempotência, API Gateway, Strangler Fig | Não |
| Padrões de design (GoF) | Strategy, Factory, Adapter, Observer, Decorator | Parcialmente: em linguagens funcionais vários viram "passar uma função" |
| Modelagem | DDD: bounded context, agregado, linguagem ubíqua ([glossário](../glossario.md)) | Não |
| Documentação | C4, ADR, arc42, atributos de qualidade (ISO/IEC 25010) | Não |

## 2. Catálogo de estilos e quando usar

| Estilo | Use quando | Evite quando | Custo principal |
| ------ | ---------- | ------------ | --------------- |
| **Monólito modular** (padrão) | Começo de produto; 1–3 times; domínio ainda mudando | Partes com escala ou ciclo de deploy muito diferentes | Disciplina nas fronteiras entre módulos |
| **Hexagonal / clean / onion** (dentro dos módulos) | Há regra de negócio real; precisa testar sem infraestrutura; vai trocar de banco ou fornecedor | CRUD simples sem regras (use camadas simples) | Mais arquivos e interfaces |
| **Camadas simples (MVC)** | CRUD, painéis administrativos, protótipos | Regras de negócio crescendo | Acoplamento ao framework/ORM com o tempo |
| **Microsserviços** | Times independentes, escala ou disponibilidade muito diferentes por parte, domínio estável | Time pequeno, domínio incerto, sem plataforma de observabilidade/deploy | Rede, consistência eventual, operação e custo |
| **Orientado a eventos** | Integrações assíncronas, picos de carga, vários consumidores do mesmo fato | Fluxos que exigem resposta síncrona e consistência forte | Rastreabilidade, ordenação, idempotência |
| **CQRS / Event Sourcing** | Leitura e escrita muito assimétricas; auditoria completa obrigatória | A maioria dos sistemas (complexidade alta) | Projeções, versionamento de eventos |
| **Serverless** | Carga intermitente, tarefas pequenas, custo por uso | Processamento longo, latência estável exigida, *lock-in* indesejado | Cold start, limites do provedor, testes locais |
| **Microkernel (plugins)** | Produto extensível por terceiros | Sem necessidade real de extensão | Contrato de plugin estável |

**Regra:** comece pelo mais simples que atende aos requisitos não funcionais e **registre a
escolha num ADR** (`/adr`). Evolua quando houver dor medida, não prevista. O monólito modular
permite extrair um módulo como serviço depois, sem reescrita
([Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html)).

## 3. O que pesa mais que a linguagem

1. **Domínio**: a complexidade das regras de negócio define quanto isolamento vale a pena.
2. **Requisitos não funcionais**: latência, escala, disponibilidade, auditoria
   ([overview](../architecture/overview.md) seção 3).
3. **Time**: tamanho e organização. A arquitetura tende a espelhar a comunicação do time
   (lei de Conway).
4. **Custo de operação**: cada serviço, fila e banco a mais precisa ser monitorado e mantido.

## 4. Mapeamento por linguagem (guia para as branches `lang/*`)

Os conceitos (módulos, portas, adaptadores, regra de dependência) são os mesmos; a forma muda:

| Linguagem | Portas (interfaces) | Injeção de dependência | Layout típico | Verificação de arquitetura |
| --------- | ------------------- | ---------------------- | ------------- | -------------------------- |
| Java / Kotlin | `interface` no domínio | Construtor; Spring/Micronaut se usar framework | `src/main/java/<pkg>/<modulo>/{domain,application,…}` + `src/test` | ArchUnit |
| C# / .NET | `interface` no domínio | Container nativo (`Microsoft.Extensions.DependencyInjection`) | Projetos por camada ou pastas por módulo numa *solution* | NetArchTest |
| Go | Interface **pequena, definida por quem consome**, não por quem implementa | Construtores explícitos no `main` (sem framework) | `cmd/<app>/`, `internal/<modulo>/` | go-arch-lint, `depguard` |
| Python | `typing.Protocol` ou ABC | Construtor / funções de fábrica no bootstrap | `src/<pacote>/<modulo>/…` + `tests/` | import-linter |
| TypeScript / Node | `interface`/`type` | Construtor; NestJS/tsyringe opcionais | `src/modules/<modulo>/…` | dependency-cruiser, eslint-plugin-boundaries |
| Rust | `trait` | Genéricos ou `Box<dyn Trait>` no bootstrap | Workspace com crates por módulo/camada | Fronteiras de crate (`pub(crate)`), cargo-modules |
| Elixir | Behaviours | Configuração / passagem de módulos | Contextos Phoenix por domínio | Boundary |
| Funcional (F#, Haskell, Clojure) | Funções/records de funções | Parâmetros e composição | *Functional core, imperative shell* (equivalente à hexagonal) | Fronteiras de módulo |

Outras diferenças que afetam o desenho:

- **Sistema de tipos:** linguagens com tipos estáticos fortes permitem tornar estados inválidos
  irrepresentáveis no tipo; nas dinâmicas, compense com validação na borda, type hints e testes.
- **Concorrência:** threads (Java), event loop (Node), goroutines (Go), atores/OTP (Elixir),
  async + ownership (Rust). Isso muda como você desenha timeouts, filas, estado compartilhado
  e *back-pressure*.
- **Frameworks com convenção forte** (Rails, Django, Laravel, Next.js, Spring Boot): mantenha o
  layout do framework e aplique as **fronteiras de módulo** e a **regra de dependência** dentro
  dele. Lutar contra o framework custa mais do que ganha.
