# PostgreSQL/pgvector para desenvolvimento

`compose.yaml` oferece um banco sintético local para validar a integração das
ferramentas. A imagem `pgvector/pgvector:0.8.6-pg17-bookworm` consta nas
[tags oficiais do pgvector](https://github.com/pgvector/pgvector#docker).
A mesma tag é usada pelo serviço do CI. A tag fixa a linha PostgreSQL 17 e a
versão pgvector 0.8.6; não fixa um digest imutável da imagem.

Com Docker e Compose disponíveis, execute pela raiz do projeto:

```text
pnpm exec docker compose -f infra/compose.yaml config --quiet
pnpm infra:up
pnpm exec docker compose -f infra/compose.yaml ps
```

O serviço `postgres` publica somente `127.0.0.1:5433`. O healthcheck usa
`pg_isready`, e `infra:up` aguarda a condição saudável com `--wait`.

| Parâmetro local    | Valor sintético                                                         |
| ------------------ | ----------------------------------------------------------------------- |
| Banco              | `arxen_test`                                                            |
| Usuário            | `arxen_test`                                                            |
| Senha              | `arxen_test_password`                                                   |
| Porta do host      | `5433`                                                                  |
| Porta no contêiner | `5432`                                                                  |
| Volume Compose     | `pgdata`, sob o projeto `arxen-dev`                                     |
| URL                | `postgresql://arxen_test:arxen_test_password@127.0.0.1:5433/arxen_test` |

A senha é pública e exclusiva deste banco descartável, que deve conter somente
fixtures sintéticas. Não reutilize esse Compose, usuário ou senha em produção.
PostgreSQL deve estar saudável antes dos testes, e a suíte de integração habilita
e exercita a extensão `vector`; disponibilidade da porta sozinha não demonstra isso.

No PowerShell, defina a conexão e execute:

```powershell
$env:TEST_DATABASE_URL = 'postgresql://arxen_test:arxen_test_password@127.0.0.1:5433/arxen_test'
pnpm test:integration
pnpm infra:down
```

`infra:down` remove os contêineres e a rede, preservando o volume nomeado. Mudanças
nas variáveis iniciais de usuário, banco ou senha não recriam automaticamente um
cluster já persistido. Preserve esse detalhe ao diagnosticar autenticação local.

O CI usa banco e contêiner novos por job, porta `5432` no runner e credenciais
sintéticas iguais. O smoke E2E atual inicia API/web pelo Playwright e não precisa
do Compose. Nenhum desses smokes valida backup, autorização ou isolamento de
produção.
