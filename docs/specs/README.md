# Especificações de features

Uma pasta por feature média/grande, criada com `/spec <feature>` ou com o prompt
[../prompts/09-spec.md](../prompts/09-spec.md):

```text
docs/specs/<feature>/
├── requirements.md   # histórias e critérios de aceite (QUANDO … ENTÃO o sistema DEVE …)
├── design.md         # arquitetura, dados, interfaces, erros e estratégia de testes
└── tasks.md          # checklist de tarefas pequenas, ligadas aos requisitos
```

As specs são versionadas e revisadas em PR como código. Mantenha-as atualizadas quando o
comportamento mudar.
