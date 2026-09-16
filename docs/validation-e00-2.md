# Validação da E00.2

Branch `feat/e00-2-core-contracts`, iniciada a partir de `ff542c0` (PR #4).
Somente fixtures sintéticas foram usadas. O escopo e os limites estão em
[e00-2-contracts.md](e00-2-contracts.md).

## Correções de testes tratadas separadamente

### Regressão da migração inicial

O teste herdado executava `upgrade head` e exigia a revisão inicial. Com novas
migrações, essas duas condições deixam de representar o mesmo requisito. Antes
dos Reds de persistência, o worker de consulta de escopo (`worker-1`, contexto
próprio, somente leitura) aprovou a separação: a regressão da E00.1 migra
explicitamente para `20260916_0001`, mantendo suas assertions de extensão e revisão;
o novo teste de head demonstra os contratos da E00.2 a partir de banco vazio.

O reset que removia apenas a extensão e `alembic_version` também foi substituído
por banco temporário único criado pela fixture. Somente o banco criado por ela é
removido. O banco-base configurado não é resetado e a falta de permissão para criar
banco continua sendo erro explícito de infraestrutura.

### Formatação do teste temporal

O primeiro Red temporal terminou com `3 failed, 1 passed`: os instantes com offset
não eram normalizados e um instante sem fuso era aceito. O arquivo foi congelado.
Ruff também apontou uma assinatura de função com 90 caracteres. A implementação
foi interrompida para revisão separada da única correção proposta: quebrar essa
assinatura em linhas, mantendo parâmetros, cenários e assertions. O worker-1
aprovou explicitamente essa correção isolada antes de ela ser aplicada. O guard
não foi limpo; o novo Red repetiu `3 failed, 1 passed`, e o novo snapshot precedeu
a normalização. O Green do mesmo arquivo terminou com `4 passed`.

## Red e Green observados

Os contratos de persistência foram expostos primeiro como métodos importáveis que
levantavam `NotImplementedError`. Cada teste chegou a esse comportamento com
PostgreSQL disponível e a preparação Alembic válida. Esses Reds demonstram a
ausência da operação de persistência; não são alegados como experimentos de
remoção individual de cada constraint. Após implementar cada slice, os mesmos
testes verificaram seus efeitos e as rejeições por SQL direto.

Comando base dos ciclos Python:

```text
pnpm python:run pytest <arquivo-ou-arquivos> --no-cov -q
```

Nos testes PostgreSQL foi definida `TEST_DATABASE_URL` para o banco sintético local
do Compose. `--tb=short` ou `--tb=line` apenas limitou a apresentação dos tracebacks.

| Arquivo em `tests/integration/`                  | Red       | Green                          | Comportamento exercitado                                                                               |
| ------------------------------------------------ | --------- | ------------------------------ | ------------------------------------------------------------------------------------------------------ |
| `test_core_cases.py`                             | 6 failed  | 6 passed                       | ID do servidor, UTC, leitura, obrigatoriedade e rollback                                               |
| `test_core_messages.py`                          | 10 failed | 10 passed, junto aos 6 de Case | Histórico ordenado, origem, conteúdo e proteção contra sobrescrita                                     |
| `test_core_sources.py`                           | 15 failed | 15 passed                      | Localizador Unicode, trecho exato, mesmo caso e referência preservada                                  |
| `test_core_tasks.py`                             | 20 failed | 20 passed                      | Draft, 11 estados, objetivo, FK e múltiplas tarefas por caso                                           |
| `test_core_events.py` + `test_core_contracts.py` | 20 failed | 20 passed                      | Ordem, cursor, FK composta, JSON objeto, banco vazio, commit/reabertura e rollback dos cinco contratos |

A regressão da revisão inicial passou isoladamente (`1 passed`). Uma tentativa
anterior de conexão à porta 5433 falhou por timeout e não foi tratada como Red.
O `pnpm infra:up` iniciou o Compose do projeto; o container antigo em outra porta
foi preservado.

Os checkpoints de teste no Git são `6a10e47`, `c9272ab`, `22461b5`, `a42e797` e
`e94b186`. Eles preservam os stubs e os testes antes do Green da respectiva
persistência. O snapshot final é cumulativo: base temporal e seis arquivos de
integração. `pnpm tdd:guard:verify` confirmou os sete arquivos intactos após
implementar eventos. Nenhum snapshot foi limpo para contornar alteração.

## Migração e transações

A nova revisão é `20260916_0002_core_contracts.py`, com `down_revision` apontando
para `20260916_0001`. A migração da E00.1 não foi alterada. O teste final chama
`pnpm db:migrate` em banco sem tabelas públicas, confirma os cinco contratos,
repete a migração e reabre os registros por uma nova conexão. Outra conexão não
vê o caso antes do commit. Uma falha deliberada na transação não deixa nenhum dos
cinco registros visível.

O downgrade foi exercitado somente em banco temporário: retorna à revisão inicial,
preserva pgvector e permite aplicar o head novamente. Ele remove as tabelas e seus
dados; não é uma estratégia de rollback de dados de produção.

## Cobertura por camada

Na primeira execução de `pnpm test:api`, os 16 testes passaram, mas o gate de
cobertura falhou em 57,53%: o módulo SQL estava incluído no denominador unitário
sem ser executado nessa camada. A configuração foi dividida em dois gates
complementares de 85%, sem reduzir o limiar: API/contratos nas unidades e
`arxen_api.persistence` na integração real. Nenhum teste congelado foi alterado
nessa mudança declarativa. O CI exige os dois jobs e seus relatórios.

A configuração complementar foi conferida em consulta read-only pelo worker-1:
a omissão unitária corresponde exatamente ao módulo medido pelo gate de integração;
os relatórios e dados de cobertura são separados. Essa consulta não substitui o
fresh-context review do diff final.

Não houve dependência nova, adoção de ORM ou mudança de lockfile.

## Validação consolidada e revisão

Validação local em 16/09/2026:

| Verificação                     | Resultado observado                                     |
| ------------------------------- | ------------------------------------------------------- |
| `pnpm check`                    | Exit 0: guard, lint, formato, tipos, unidades e build   |
| `pnpm test:api` dentro do check | 16 passed; cobertura de 95,45% no escopo unitário       |
| `pnpm test:web` dentro do check | 1 passed; cobertura de 100%                             |
| `pnpm test:integration`         | 78 passed; cobertura de 100% de `arxen_api.persistence` |
| `pnpm tdd:guard:verify`         | 7 arquivos congelados intactos                          |
| `git diff --check`              | Exit 0                                                  |

O percurso web e os endpoints existentes não foram alterados, portanto o E2E local
não foi repetido nesta etapa. O CI mantém sua execução obrigatória de Chromium.
O resultado de CI e o parecer independente ficam registrados na PR, vinculados ao
commit efetivamente conferido; este registro local não substitui esses gates.

Hashes SHA-256 do snapshot final, mantidos desde os Reds correspondentes:

```text
2f063ec7ef861c257a41f442b949e170ab8134363ef74d71c5c11a25930a0f25  services/api/tests/test_contract_timestamps.py
227ccff73c2685997a8503ddce61c15c371697b6fa2e877e305263358afe3a37  tests/integration/test_core_cases.py
9c63bdcffd4247883ef6bde4e66275287716d19025f2621ab62c709b7f8fff33  tests/integration/test_core_contracts.py
95310de0fc8d7272b6f25b3a279c8f32d9b33e697e63c126eb86b07283da7144  tests/integration/test_core_events.py
09683f8220aa3cefebda2da35a391e2371ea66b5a0a837d2be7a58fed5e92e4b  tests/integration/test_core_messages.py
e12399f06d47a2646a3a19bcb767df0dc509caf7e59790af68e31bb242ac00d1  tests/integration/test_core_sources.py
b58e2c2f4bfc8bcde07ce63bf8da962a433b3049933699a76358c88c453a1b96  tests/integration/test_core_tasks.py
```

E00.3 ainda não começou. Autorização, identidade, fontes documentais, execução de
tarefas e entrega operacional de eventos continuam fora desta implementação.
