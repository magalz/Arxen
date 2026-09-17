# Validação da E00.3

Registro de 16/09/2026. Branch `feat/e00-3-synthetic-cases`, derivada de
`61924653f05f346ecf8978e99fd010e369e9b804`, merge da E00.2 pela PR #5.

## Escopo demonstrado

Configuração da identidade sintética, `GET /api/v1/me`, criação por
`POST /api/v1/cases` e consulta/reabertura por `GET /api/v1/cases/{case_id}`.
O vínculo de responsabilidade é persistido em PostgreSQL; outra identidade e
casos sem atribuição recebem o mesmo 404 de um caso inexistente. O servidor
confirma a criação somente após commit. E00.4 e E01 não foram iniciadas.

## Histórico do slice de identidade

Comandos focados, antes e depois de cada implementação:

```text
pnpm python:run pytest services/api/tests/test_synthetic_identity_settings.py --no-cov -q --tb=short
pnpm python:run pytest services/api/tests/test_synthetic_identity_http.py --no-cov -q --tb=short
```

O Red da configuração terminou com **17 failed, 3 passed**: o carregador retornava
`None` para ativação válida e não recusava ambiente/valores indevidos. O snapshot
precedeu a implementação. O mesmo arquivo terminou com **20 passed**.

O Red HTTP terminou com **7 failed, 2 passed**: a rota ainda retornava 404 e a
factory ignorava a configuração sintética. Após congelar o arquivo, foram
implementadas a ativação na factory, a conferência do token e a rota. A execução
conjunta dos dois arquivos terminou com **29 passed**.

Os checkpoints são `3b36c91` (configuração) e `b84aa52` (HTTP). Os oito testes
congelados da E00.2 continuam no manifesto; os dois novos foram acrescentados
após seus Reds. Não houve limpeza do guard ou alteração de teste congelado.

Foram observados dois avisos de depreciação no TestClient instalado, relativos
à integração com httpx e ao alias de BlockingPortal do anyio. Eles não foram
suprimidos nem motivaram atualização incidental de dependências nesta etapa.

## Recuperação da coordenação

Na sessão anterior, chamadas de coordenação retornaram `WORKER_IDENTITY_LOST`, sem
executar operação de agentes. `update_plan` também recusou a atualização por
ausência de identidade exata do chat; isso não impediu leitura, Git ou execução.

Foi tentada uma consulta separada pelo Codex CLI já instalado (0.154.0), com
`--sandbox read-only --ephemeral`, sem overrides de modelo ou esforço. O processo
encerrou com código 1 por limite de uso, sem gerar o arquivo de parecer. Não houve
aprovação de escopo, correção de teste ou review final por esse caminho.

Na retomada, a identificação da conversa foi recuperada e o coordenador confirmou
que não havia worker implementando a etapa. O agente principal conduziu o trabalho;
as consultas separadas foram executadas por workers identificados. A correção do
teste de migração foi revisada antes da edição, conforme o registro abaixo.

## Verificações históricas do slice parcial

Resultados observados em `f36ad08`, antes do fluxo persistente de casos:

| Verificação             | Resultado                                            |
| ----------------------- | ---------------------------------------------------- |
| `pnpm check`            | Exit 0; lint, formato, tipos, testes e build         |
| API dentro do check     | 45 passed; cobertura combinada de 97,44%             |
| Web dentro do check     | 1 passed; cobertura de 100%                          |
| `pnpm test:integration` | 87 passed; persistência Python com 100% de cobertura |
| `pnpm tdd:guard:verify` | 10 arquivos congelados intactos                      |
| `git diff --check`      | Exit 0                                               |

Os 87 testes de integração preservaram as garantias da E00.2; não demonstravam
o vínculo caso/identidade então pendente. O E2E local não foi repetido, pois o
percurso web e o contrato de `/healthz` permanecem iguais; Chromium continua
obrigatório no CI. Ambos os gates Python mantêm o limite de 85%.

SHA-256 dos dois arquivos novos, preservados desde seus Reds:

```text
d1eba624ef4846370ed0ecf5872f3e4ab5057ad4f8cbeba86ec8c127a7f2dcf1  services/api/tests/test_synthetic_identity_settings.py
655816c2d1a33300cb2f8f902fe8c10e6f9d254dc01acdc0cd2d625e94763a67  services/api/tests/test_synthetic_identity_http.py
```

O CI aprovado de `f36ad08` cobre somente esse slice parcial e não é usado como
evidência do commit que completa a E00.3.

## Retomada: revisão separada da regressão de migração

O workspace foi conferido em `f36ad08`, sem alterações alheias, com os dez
arquivos congelados intactos. A coordenação recuperou a identificação da conversa;
`worker-1` realizou uma consulta independente somente leitura da correção do teste
de migração, e `worker-2` revisou requisitos e riscos do recorte.

O `worker-1` aprovou a evolução de `test_core_contracts.py`: resolver o head único
dos scripts Alembic via configuração TOML, substituir a expectativa fixa de
versão e acrescentar assertions de existência e vazio da tabela de responsabilidade
após verificar os cinco contratos. As assertions anteriores, o comando real pnpm,
repetição, commit, releitura, rollback, pgvector e downgrade descartável permanecem.

Essa extensão permite observar Red no próprio arquivo por ausência do esquema de
vínculo, antes da comparação de revisão. O Red não será apresentado como prova de
isolamento HTTP ou como falha incidental de versão. O snapshot foi regravado
explicitamente após o novo Red, mantendo os demais arquivos do manifesto.

Antes de qualquer DDL novo, `test_synthetic_case_migration.py` observou **2 failed**
na assertion `to_regclass` (tabela de vínculo ausente), com PostgreSQL e migrações
anteriores funcionando. O guard foi ampliado de dez para onze arquivos. Esse
arquivo recebeu revisão separada para fixar a revisão específica nas chamadas
de migração, evitando repetir a fragilidade do teste legado de head.

O arquivo novo de contrato HTTP `test_synthetic_cases_http.py` observou
**27 failed, 2 passed**: as rotas de casos ainda retornavam 404 onde o contrato
exigia autenticação, validação ou erro de armazenamento; o OpenAPI de casos estava
ausente. Nenhum comportamento de casos foi implementado antes desses Reds.

O Red da correção do teste legado terminou com **1 failed, 2 passed**, por ausência
da tabela no catálogo; as verificações de rollback e downgrade continuaram verdes.
Na mesma execução, a integração HTTP observou **9 failed** por ausência de rotas
ou da tabela; a validação de privacidade HTTP observou **4 failed** por ausência
das rotas. Esses Reds não alegam injeção de cada falha no código ainda inexistente.

O `worker-1` também aprovou a correção separada do teste específico novo: trocar
somente suas quatro chamadas a `db:migrate` por upgrade explícito à revisão
`20260916_0003`, preservando cada assertion. O teste geral continua executando
`pnpm db:migrate` e conferindo o head versionado. Assim a regressão da revisão
específica não passa a falhar apenas porque uma etapa futura acrescentou migração.

Para repetir o Red sem falha de revisão ausente, o revisor aprovou um esqueleto
Alembic `0003` sem DDL, exclusivamente nos bancos descartáveis das fixtures.
Nenhum esqueleto foi aplicado ao banco-base. Os métodos de persistência novos
começaram como stubs importáveis com `NotImplementedError`, como na E00.2.
Novo Red e snapshot cumulativo precederam a implementação do DDL e das operações.

Com o esqueleto, os dois arquivos corrigidos repetiram o Red de catálogo:
`test_core_contracts.py::test_empty_database_migrates_and_reopens_all_contracts`
falhou ao procurar a tabela; os dois testes de migração específica falharam em
`assert_binding_schema`, por `to_regclass = None`. A execução conjunta com
`test_synthetic_case_ownership.py` terminou com **10 failed, 2 passed**, exit 1:
um Red do core, dois da migração específica e sete de persistência/constraints.
Os stubs foram alcançados; não houve falha de importação ou infraestrutura.

Hashes anteriores das duas exceções revisadas, preservados para auditoria do ciclo:

```text
9c63bdcffd4247883ef6bde4e66275287716d19025f2621ab62c709b7f8fff33  tests/integration/test_core_contracts.py
ff60136aaf09a48e4b409b1d7c8dcf6b6c59f3d2f6a39e9eb5977c2b99b7c5f7  tests/integration/test_synthetic_case_migration.py
```

O snapshot de implementação contém os dez caminhos herdados e os cinco arquivos novos,
com renovação explícita apenas das duas exceções acima. Nenhum manifesto foi limpo.

## Green, transações e reabertura

A correção revisada do teste legado está no commit `98f915a`; o checkpoint dos
testes de casos e stubs está em `05eca83`. Os quinze arquivos do guard foram
verificados antes de implementar o DDL e as operações. Nenhum deles foi alterado
durante o Green.

Comandos focados da retomada, sempre com `TEST_DATABASE_URL` sintética nas
execuções de integração:

```text
pnpm python:run pytest tests/integration/test_core_contracts.py tests/integration/test_synthetic_case_migration.py tests/integration/test_synthetic_case_ownership.py --no-cov -q --tb=short
pnpm python:run pytest services/api/tests/test_synthetic_cases_http.py services/api/tests/test_synthetic_request_privacy.py services/api/tests/test_synthetic_identity_http.py services/api/tests/test_synthetic_identity_settings.py --no-cov -q --tb=short
pnpm python:run pytest tests/integration/test_synthetic_cases_api.py --no-cov -q --tb=short
```

| Grupo                                         | Red observado                 | Green observado                                  |
| --------------------------------------------- | ----------------------------- | ------------------------------------------------ |
| Migração geral, específica e responsabilidade | 10 failed, 2 passed           | 12 passed                                        |
| Contratos HTTP de casos e privacidade         | 27 failed/2 passed e 4 failed | 33 passed, junto aos 29 da identidade: 62 passed |
| API com PostgreSQL real                       | 9 failed                      | 9 passed                                         |

O teste ASGI observa o instante `http.response.start` da resposta 201 e consulta
os dois registros por outra conexão. Duas injeções usam triggers reais: falha ao
inserir o vínculo e constraint trigger diferido até o commit. Ambas receberam
somente 503, sem emissão prévia de sucesso, e preservaram as contagens anteriores.
O segundo teste de transação da persistência também confirma rollback pelo chamador.

Duas instâncias com UUIDs e tokens distintos criam e consultam os próprios casos.
IDs alheios, inexistentes e sem atribuição recebem a mesma resposta 404. Recriar
a aplicação com o mesmo UUID e token rotacionado preserva o acesso, sem modificar
o caso ou acrescentar registros. As duas formas de URL admitidas pela configuração,
`postgresql://` e `postgresql+psycopg://`, foram exercitadas.

A migração `20260916_0003` preservou os cinco contratos criados em `0002`, sem
atribuição automática. Upgrade a partir de vazio, repetição e downgrade/re-upgrade
foram executados em bancos descartáveis. As fixtures e as regressões de isolamento
de URL/destino da E00.2 permaneceram intactas.

O risco de ecoar valores sensíveis em erros de validação foi identificado na consulta
read-only do `worker-2` e tratado antes do Green: a resposta 422 é genérica e os
testes enviam tokens indevidamente no corpo para verificar que não são devolvidos.
Não houve novo pacote, ORM, alteração de lockfile ou mudança dos gates de 85%.

## Snapshot após os Reds revisados

Os nove arquivos herdados que não precisaram de correção mantiveram seus hashes.
O snapshot completo permaneceu em `.artifacts/tdd-guard.json`, fora do Git. Hashes
da correção do core e dos cinco testes novos, congelados antes do Green:

```text
2e5d408abf9efb48d6ed8086f50784c705c45325cfc5c6356edcc0f0d050971b  tests/integration/test_core_contracts.py
b510f3880c1bed930e0a66c3509dde0851f4e79c37e9864bacab2d5c206e6b1d  tests/integration/test_synthetic_case_migration.py
aa492100db37e3f86911e2ccca80244ddd0429b836d0720d547208743aea5fd3  tests/integration/test_synthetic_case_ownership.py
f91c46d1ce5ad5bc401be46849d31f2967852a8c9f23d0f56b6e8c77bd7db7a0  tests/integration/test_synthetic_cases_api.py
9556b4adf0b69716d6147d5fdde6bc21093295c2abfbde1377ed48bb806b0873  services/api/tests/test_synthetic_cases_http.py
0700f43fa7dc7a046f2bd61ed97630240fc3d72594a52a07b6824f3a72dffc8c  services/api/tests/test_synthetic_request_privacy.py
```

## Verificação consolidada da entrega

Resultados locais do código completo, em Windows com PostgreSQL/pgvector real:

| Verificação                      | Resultado observado                                      |
| -------------------------------- | -------------------------------------------------------- |
| `pnpm check`                     | Exit 0: guard, lint, formato, tipos, unidades e build    |
| API no check                     | 78 passed; cobertura combinada de 89,42%                 |
| Web no check                     | 1 passed; cobertura de 100%                              |
| `pnpm test:integration`          | 105 passed; cobertura de 100% de `arxen_api.persistence` |
| `pnpm tdd:guard:verify` no check | 15 arquivos congelados intactos                          |

Os gates complementares continuam em 85%, com a mesma configuração da E00.2:
unidades medem a API, exceto apenas `persistence.py`; integração mede esse módulo
SQL contra o banco real. Nenhum código novo foi excluído. A cobertura unitária
de `synthetic_api.py` é 73,13%; seus caminhos de sucesso e leitura com escopo são
exercitados adicionalmente pelos nove testes de integração HTTP reais. O gate
unitário é agregado, como já estabelecido, e terminou em 89,42%.

As validações consolidadas mantiveram os dois avisos de depreciação do TestClient
descritos acima. O percurso web e `/healthz` não foram alterados; E2E local não foi
repetido. Chromium permanece obrigatório no CI, junto das qualidades Linux/Windows
e da integração. As últimas edições documentais recebem verificação de formato e
diff antes do commit; não alteram código nem testes congelados.

## Review e CI por commit

As consultas de `worker-1` e `worker-2` aprovaram correções de testes e decisões de
escopo, não o diff final. O parecer de encerramento deve ser emitido por um novo
contexto read-only, identificando o SHA e achados por severidade. A PR #6 registra
esse parecer e o CI do SHA final antes de ser liberada para revisão do responsável.
Nenhum resultado histórico substitui esses gates; o merge exige autorização própria.

## Correção do contrato de erros OpenAPI

O CI de `4aa1a6a88d5c77af56ac43898eb32afad26f2efe` passou na execução
`35165252595`, incluindo Linux/Windows, integração, Chromium e CI Gate. Um novo
worker read-only iniciou a revisão desse SHA. A conferência adicional do contrato
OpenAPI encontrou divergência entre a resposta genérica 422 e o esquema padrão
do FastAPI (`detail` como array), além de erros HTTP não declarados.

Foi acrescentado `test_synthetic_error_schema.py`, sem alterar os quinze testes
congelados. O comando abaixo terminou em **8 failed**, exit 1: seis respostas
ausentes do contrato e dois esquemas 422 com `array` em vez de `string`.

```text
pnpm python:run pytest services/api/tests/test_synthetic_error_schema.py --no-cov -q --tb=short
```

O guard foi verificado com quinze arquivos, ampliado explicitamente para dezesseis
e verificado novamente antes da implementação. Hash do novo Red:

```text
d770ed83edc2947bf6375ab36121f59582b127eca290a8e7c8dda709dc82e5e7  services/api/tests/test_synthetic_error_schema.py
```

O parecer e o CI de `4aa1a6a` não substituem review em contexto novo e CI do SHA
que corrigir esse contrato. O review também apontou texto desatualizado no README,
que ainda descrevia as rotas de casos como pendentes.
