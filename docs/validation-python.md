# Validação da base Python

Registro de 16/09/2026, executado em Windows com PowerShell 5.1. O escopo é
infraestrutura: uma API de smoke, ferramentas Python e testes sintéticos. Não
representa conclusão da E00 nem implementação de casos ou autenticação.

O pacote `arxen_api` usa `services/api/src/arxen_api`, instalado em modo editável
na `.venv` da raiz. `.python-version` fixa Python 3.13.12; `pyproject.toml` exige
uv 0.12.10 e fixa o backend `uv_build` em 0.12.10. `uv.lock` resolve 34 pacotes.
As dependências diretas têm versões exatas no `pyproject.toml`; as transitivas
ficam resolvidas com hashes no lockfile.

`create_app()` cria a aplicação e `arxen_api.main:app` é o ponto de entrada ASGI.
`GET /healthz` responde HTTP 200, `Content-Type: application/json` e exatamente
`{"status":"ok","service":"arxen-api"}`. A resposta é de disponibilidade do
processo e não consulta o banco. Os padrões de documentação do FastAPI foram
mantidos; este smoke não introduz uma política de exposição para produção.

**Ciclo TDD observado.** Primeiro foram criados o contrato de teste e uma
aplicação FastAPI vazia, já importável e instalada. `pnpm test:api` terminou
com código 1 e duas falhas, para a fábrica e para o ponto de entrada ASGI:

```text
assert response.status_code == 200
E assert 404 == 200
2 failed
```

Após implementar somente a rota, o mesmo comando passou nos dois cenários.
Em seguida, os testes foram refatorados de `TestClient` para
`httpx.AsyncClient` com `ASGITransport` e o backend asyncio do AnyIO: isso
removeu avisos de depreciação emitidos pela versão instalada do `TestClient`.
A execução final teve dois testes aprovados, nenhum aviso e código 0.
Os testes verificam status, tipo de conteúdo e corpo JSON completo, sem
`DATABASE_URL` definido. O transporte ASGI roda no processo do teste;
essa evidência não substitui um teste HTTP com servidor externo.

**Interface dos scripts.** Executar os comandos na raiz do repositório.

| Comando pnpm                   | Comando executado                                                         |
| ------------------------------ | ------------------------------------------------------------------------- |
| `pnpm python:lock`             | `uv lock`                                                                 |
| `pnpm python:sync`             | `uv sync --locked --all-groups`                                           |
| `pnpm python:run <argumentos>` | `uv run --locked <argumentos>`                                            |
| `pnpm test:api`                | `uv run --locked pytest services/api/tests`                               |
| `pnpm test:integration`        | `uv run --locked pytest tests/integration --no-cov`                       |
| `pnpm lint:api`                | `uv run --locked ruff check .`                                            |
| `pnpm format:api:check`        | `uv run --locked ruff format --check .`                                   |
| `pnpm typecheck:api`           | `uv run --locked mypy services/api/src`                                   |
| `pnpm dev:api`                 | `uv run --locked uvicorn arxen_api.main:app --host 127.0.0.1 --port 8000` |

`pnpm python:lock` e `pnpm python:sync` foram executados com sucesso. O uv
criou a `.venv` local. A instalação informou fallback de hardlink para cópia,
mas concluiu sem erro. Ruff, verificação de formatação e mypy estrito passaram.

**Cobertura e separação das suítes.** A configuração da raiz usa
`testpaths = ["services/api/tests"]`, mede o pacote `arxen_api` com cobertura
de branches habilitada e exige cobertura global de pelo menos 85%.
A execução final cobriu as oito instruções existentes: 100%. Este skeleton
ainda possui zero ramos; o resultado não demonstra caminhos condicionais que
ainda não foram implementados. Não foram adicionados testes nem código de
negócio apenas para aumentar a métrica.

`tests/integration/pytest.ini` é selecionado ao chamar a suíte de integração.
Essa configuração tem JUnit próprio e `--no-cov`, pois os testes exercitam o
servidor PostgreSQL, sem executar o pacote da API. A integração não reduz o
limiar da suíte unitária nem sobrescreve seu relatório de cobertura.

| Saída               | Caminho                              |
| ------------------- | ------------------------------------ |
| JUnit da API        | `test-results/api/junit.xml`         |
| Cobertura XML       | `coverage/api/coverage.xml`          |
| Cobertura HTML      | `coverage/api/html/index.html`       |
| Dados de cobertura  | `.coverage.api`                      |
| JUnit da integração | `test-results/integration/junit.xml` |

Essas saídas são locais e estão cobertas pelo `.gitignore` da raiz.

**Integração real preparada.** Os seis cenários usam psycopg binary e um
PostgreSQL com pgvector disponível: quatro roundtrips de texto parametrizado
(simples, Unicode, aspas e texto parecido com SQL), um roundtrip vetorial com
distâncias euclidianas esperadas de 0 e 5 e um teste que confirma o
desaparecimento da tabela temporária após rollback.

Cada teste recebe uma conexão própria, com limite de conexão de cinco
segundos. A fixture abre uma transação explícita com `force_rollback=True`,
define timeout de comando e executa `CREATE EXTENSION IF NOT EXISTS vector`.
A criação da extensão, quando necessária, também é revertida ao final.
As tabelas são temporárias e todos os valores são sintéticos. O usuário do
banco precisa poder criar tabelas temporárias e, se a extensão ainda não
existir, ter permissão para criá-la. O pgvector precisa estar disponível no
servidor; a suíte não instala binários no servidor nem inicia Docker.

Para usar o banco descartável definido em `infra/compose.yaml`, depois que
ele estiver disponível:

```powershell
$env:TEST_DATABASE_URL = 'postgresql://arxen_test:arxen_test_password@127.0.0.1:5433/arxen_test'
pnpm test:integration
```

As credenciais acima são as sintéticas do Compose. Outra instância pode ser
usada configurando `TEST_DATABASE_URL` com sua conexão de teste.

**Pendência observada.** Na execução local, `TEST_DATABASE_URL` estava ausente.
`pnpm test:integration` coletou os seis cenários, terminou com código 1 e seis
erros de preparação, sem skips, produzindo o JUnit da integração. A mensagem
foi `TEST_DATABASE_URL is required for integration tests.` seguida da
orientação para configurar um banco descartável. Isso comprova o bloqueio
por configuração ausente; as assertions contra PostgreSQL/pgvector ainda
precisam ser executadas contra um banco ativo. Essa falha de infraestrutura
não foi tratada como evidência de TDD do comportamento da API.

O check completo do monorepositório, o teste de navegador e a execução da
integração no CI ficam na validação consolidada pelo agente principal.
