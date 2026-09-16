# Validação parcial da E00.3

Registro de 16/09/2026. Branch `feat/e00-3-synthetic-cases`, derivada de
`61924653f05f346ecf8978e99fd010e369e9b804`, merge da E00.2 pela PR #5.

## Escopo demonstrado

Configuração da identidade sintética e `GET /api/v1/me`, com opt-in explícito,
restrição a desenvolvimento/teste, token Bearer e identidade definida no servidor.
Ainda não há vínculo persistente entre caso e identidade, rotas HTTP de casos ou
nova migração. A E00.3 completa permanece em andamento.

## TDD

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

## Revisão independente pendente

As chamadas de coordenação de workers retornaram `WORKER_IDENTITY_LOST`, sem
executar operação de agentes. `update_plan` também recusou a atualização por
ausência de identidade exata do chat; isso não impediu leitura, Git ou execução.

Foi tentada uma consulta separada pelo Codex CLI já instalado (0.154.0), com
`--sandbox read-only --ephemeral`, sem overrides de modelo ou esforço. O processo
encerrou com código 1 por limite de uso, sem gerar o arquivo de parecer. Não houve
aprovação de escopo, correção de teste ou review final por esse caminho.

Antes de alterar a expectativa de revisão em `test_core_contracts.py`, deve ser
concluída a revisão separada descrita em [e00-3-synthetic-cases.md](e00-3-synthetic-cases.md).
Nenhuma migração nova foi aplicada e o teste original permanece intacto.

## Verificações consolidadas

Resultados locais observados:

| Verificação             | Resultado                                            |
| ----------------------- | ---------------------------------------------------- |
| `pnpm check`            | Exit 0; lint, formato, tipos, testes e build         |
| API dentro do check     | 45 passed; cobertura combinada de 97,44%             |
| Web dentro do check     | 1 passed; cobertura de 100%                          |
| `pnpm test:integration` | 87 passed; persistência Python com 100% de cobertura |
| `pnpm tdd:guard:verify` | 10 arquivos congelados intactos                      |
| `git diff --check`      | Exit 0                                               |

Os 87 testes de integração preservam as garantias da E00.2; eles não demonstram
o vínculo caso/identidade ainda pendente. O E2E local não foi repetido, pois o
percurso web e o contrato de `/healthz` permanecem iguais; Chromium continua
obrigatório no CI. Ambos os gates Python mantêm o limite de 85%.

SHA-256 dos dois arquivos novos, preservados desde seus Reds:

```text
d1eba624ef4846370ed0ecf5872f3e4ab5057ad4f8cbeba86ec8c127a7f2dcf1  services/api/tests/test_synthetic_identity_settings.py
655816c2d1a33300cb2f8f902fe8c10e6f9d254dc01acdc0cd2d625e94763a67  services/api/tests/test_synthetic_identity_http.py
```

O resultado do CI será vinculado ao SHA na PR deste slice. A PR permanece em
rascunho, pois a E00.3 e o review independente ainda não foram concluídos.
A E00.4 não começou.

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
isolamento HTTP ou como falha incidental de versão. O snapshot será regravado
explicitamente após o novo Red, mantendo os demais arquivos do manifesto.

Antes de qualquer DDL novo, `test_synthetic_case_migration.py` observou **2 failed**
na assertion `to_regclass` (tabela de vínculo ausente), com PostgreSQL e migrações
anteriores funcionando. O guard foi ampliado de dez para onze arquivos. Esse
arquivo ainda recebe revisão separada para fixar a revisão específica nas chamadas
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
Nenhum esqueleto é aplicado ao banco-base. Os métodos de persistência novos são
inicialmente stubs importáveis com `NotImplementedError`, como no ciclo da E00.2.
Novo Red e snapshot cumulativo precedem a implementação do DDL e das operações.

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

O próximo snapshot contém os dez caminhos herdados e os cinco arquivos novos,
com renovação explícita apenas das duas exceções acima. Nenhum manifesto foi limpo.
