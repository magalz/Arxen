# Guardrails de engenharia

Decisões operacionais do Arxen para seleção de ferramentas, TDD e revisão. Este
documento complementa `AGENTS.md` e `CONTRIBUTING.md` e deve ser reutilizado em
novos contextos de desenvolvimento.

## Seleção de ferramentas e dependências

A ordem de preferência é:

1. atender integralmente ao requisito e aos critérios de segurança;
2. preferir software open source e sem custo de licença;
3. verificar maturidade, manutenção ativa e compatibilidade com a stack;
4. minimizar dependências, serviços adicionais e complexidade operacional;
5. fixar versões e preservar instalação reproduzível;
6. adotar opção proprietária ou paga somente quando houver benefício material que
   a alternativa aberta não ofereça ou uma decisão explícita do projeto.

Preço zero não compensa uma ferramenta abandonada ou inadequada. Da mesma forma,
popularidade isolada não justifica adicionar uma camada que o produto não precisa.

Na E00.1 essa regra levou à escolha de Alembic para migrações: ferramenta MIT,
madura e alinhada ao ecossistema Python/PostgreSQL. SQLAlchemy está presente apenas
como dependência técnica do migrador; o domínio continua em `psycopg`.

## Teste Red é contrato durante a implementação

Um Red só é válido quando o teste chega ao comportamento pretendido e falha pelo
motivo esperado. Import ausente, erro de sintaxe, dependência faltando ou
infraestrutura indisponível não contam.

Depois de um Red válido, o agente que implementa fica impedido por regra de projeto
de editar os testes que demonstraram esse Red para adaptar o critério à solução. Isso
inclui reduzir assertions, remover cenários, adicionar skip, trocar valores esperados
para os produzidos pelo código ou reescrever o teste de modo a esconder a falha.

O soft guard local registra SHA-256 desses arquivos:

```text
pnpm tdd:guard:record -- services/api/tests/test_regra.py
pnpm tdd:guard:verify
```

O estado fica em `.artifacts/tdd-guard.json`, já ignorado pelo Git. O `pnpm check`
verifica automaticamente um snapshot ativo. O mecanismo não impede tecnicamente a
edição do arquivo; ele torna a alteração detectável e faz a verificação local falhar.
Por isso é um **soft guardrail**, complementado pelas instruções obrigatórias aos
agentes e pelo review da PR.

### Quando um teste Red realmente precisa mudar

O agente implementador deve parar. A correção do teste é tratada como uma decisão
separada e precisa de:

1. motivo documentado — erro no teste ou mudança aprovada de spec;
2. revisão da correção do teste separada da tentativa de fazer o código passar;
3. novo Red comportamental observado;
4. novo `tdd:guard:record` antes de retomar a implementação.

`pnpm tdd:guard:clear` é usado depois do Green e das verificações finais. Ele não é
um mecanismo de bypass.

## Independência de review

O review final continua sendo executado em contexto novo, separado da implementação.
Além de correção, segurança e aderência à spec, o revisor verifica se os testes que
definiram o comportamento foram preservados durante o ciclo. Mudança material após
o parecer exige nova revisão do estado final.
