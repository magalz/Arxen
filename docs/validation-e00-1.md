# Validação da E00.1 — banco, migrações e configuração

Registro de 16/09/2026 para a branch `feat/e00-foundation`.

## Decisão técnica

O migrador selecionado é **Alembic 1.20.0**, com **SQLAlchemy 2.0.54** como
dependência técnica direta do ambiente de migração. A escolha não introduz custo de
licença e não muda a decisão atual de acesso ao banco pelo `psycopg` no domínio.
Ela segue a política do projeto de preferir ferramentas open source, sem custo de
licença, maduras e com menor complexidade operacional entre alternativas adequadas.

A configuração mínima usa `DATABASE_URL`, carregada por uma `dataclass` imutável e
validada sem biblioteca adicional de settings. São aceitas URLs PostgreSQL com
host e nome de banco; para Alembic, `postgresql://` é convertido para o driver
`postgresql+psycopg://`.

## Evidência TDD — configuração

Red focado:

```text
pnpm python:run pytest services/api/tests/test_settings.py --no-cov -q
FFFF
4 failed
```

Os quatro testes falharam por `NotImplementedError` no contrato já importável de
configuração. Depois da implementação mínima, o mesmo comando terminou com:

```text
....
4 passed in 0.16s
```

Os cenários cobrem ausência de `DATABASE_URL`, esquema não PostgreSQL, ausência do
nome do banco e normalização para o driver psycopg usado pelo SQLAlchemy.

## Evidência TDD — migração inicial

O ambiente Alembic e uma revisão inicial vazia foram preparados antes do teste de
comportamento. Contra PostgreSQL real, o Red foi:

```text
pnpm python:run pytest tests/integration/test_migrations.py --no-cov -q
FAILED test_upgrade_head_prepares_empty_database
assert extension is not None
```

Alembic havia chegado ao `head`, porém `pg_extension` ainda não continha `vector`.
Após a implementação mínima de `CREATE EXTENSION IF NOT EXISTS vector`, o mesmo
teste terminou com `1 passed`.

A revisão `20260916_0001` habilita somente pgvector. Nenhuma tabela de caso,
mensagem, fonte, tarefa ou evento foi antecipada; essas estruturas pertencem à
E00.2.

## Evidência TDD — soft guard dos testes Red

O guard foi desenvolvido com dois arquivos de teste: unidade e CLI. Uma primeira
tentativa de Red falhou por importação da raiz do repositório e não foi aceita como
evidência comportamental. Depois que o contrato ficou importável, houve Red válido;
na verificação de qualidade posterior foram detectados problemas mecânicos de lint
nos próprios testes.

Como o guard ainda estava sendo criado, essa correção foi tratada como exceção de
bootstrap: os arquivos originais foram preservados em `.artifacts/`, o snapshot foi
encerrado explicitamente, somente importação/formatação foi corrigida e as
assertions/valores esperados foram mantidos. Em seguida, a implementação do guard
foi temporariamente neutralizada e um **novo Red válido** foi observado:

```text
pnpm python:run pytest services/api/tests/test_tdd_guard.py services/api/tests/test_tdd_guard_cli.py --no-cov -q
FFFFFF
6 failed
```

Os hashes SHA-256 nesse Red final foram:

```text
CBB920ACD79598DDC1ADD51FB3BEDF183A06AFA96106FF2FC629D65AC673C9F7 services/api/tests/test_tdd_guard.py
7C91C998253FAC331429770F3A868D8E952128E97B37D1195352568D19BAAF12 services/api/tests/test_tdd_guard_cli.py
```

A implementação Green previamente salva foi restaurada sem editar os testes e o
mesmo comando terminou com `6 passed`. Depois disso o próprio guard registrou esses
dois arquivos e confirmou `Verified 2 recorded Red test(s) unchanged.`. O
`pnpm check` passa a executar essa verificação automaticamente enquanto houver um
snapshot ativo.

## Validação consolidada

Com o banco sintético local saudável via Podman:

```text
pnpm test:integration
7 passed

pnpm db:current
20260916_0001 (head)

pnpm check
exit 0
```

O `pnpm check` final começou verificando o snapshot ativo do TDD guard, depois
executou lint, formato, tipos, unidades e build. A API coletou 12 testes, todos
aprovados, e terminou com cobertura total de 90,48%, acima do mínimo de 85%; a web
manteve um teste e 100% sobre o código medido.

Sem `DATABASE_URL`, `pnpm db:current` termina com código 1 e a mensagem final:

```text
arxen_api.settings.ConfigurationError: DATABASE_URL is required
```

O smoke E2E não foi repetido nesta etapa porque E00.1 não altera o percurso web ou
o comportamento do Playwright. A integração real foi executada porque a mudança
altera diretamente preparação e versão do PostgreSQL.

## Limites

Esta etapa não implementa autenticação, RLS, organizações, casos, objetos privados,
upload retomável, OpenHands, OCR ou tabelas do domínio. O banco local continua sendo
um ambiente sintético e descartável; a validação não autoriza dados reais.

E00.1 só pode ser encerrada após review técnico em contexto novo, conforme
`docs/e00-foundation-plan.md`.
