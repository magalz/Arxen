# Testes e evidências

Esta fundação verifica a execução de React/Vite/Vitest, FastAPI/pytest,
PostgreSQL/pgvector e Playwright. Um smoke aprovado demonstra somente o percurso
testado. Não conclui a E00 nem demonstra autenticação, isolamento entre clientes,
análise jurídica ou uso com dados reais.

## Ciclo TDD

1. **Red:** descreva uma regra ou regressão observável, escreva seu teste e execute-o
   antes da implementação. Confira a assertion, a saída e o código de retorno.
   Falha de importação, dependência ausente, banco indisponível ou erro de sintaxe
   não demonstra a ausência do comportamento.
2. **Green:** implemente o mínimo e execute o mesmo teste. Rode também os testes dos
   consumidores afetados. Não enfraqueça a assertion para acomodar a implementação.
3. **Refactor:** ajuste estrutura e duplicações, mantendo os testes aprovados.
   Registre os comandos finais, resultados e limites da validação.

Depois que o Red falhar pelo motivo comportamental esperado, o teste passa a ser a
referência fixa do ciclo. O agente implementador não pode alterar esse teste para
acomodar sua solução. Registre os arquivos com:

```text
pnpm tdd:guard:record -- caminho/do/teste.py caminho/outro.test.ts
```

O snapshot fica em `.artifacts/tdd-guard.json`, fora do Git. `pnpm check` executa
`pnpm tdd:guard:verify`; se qualquer teste registrado for alterado ou removido, a
verificação falha. Após o Green e as verificações finais, `pnpm tdd:guard:clear`
encerra o snapshot. O agente não pode limpar o guard para evitar uma falha.

Se o teste for realmente incorreto, interrompa o ciclo de implementação. Documente
o problema, revise a correção do teste separadamente, faça a alteração, observe um
novo Red válido e registre um novo snapshot antes de continuar. Mudança de spec
segue a mesma regra. Isso permite corrigir testes errados sem transformar o teste
em uma variável ajustável à implementação.

Inclua no PR os comandos exatos e trechos curtos dos resultados reais, com o teste
e a assertion que falhou em Red, o resultado em Green e a verificação após a
refatoração. A cronologia é evidência do trabalho e da revisão: **CI aprovado não
prova que o teste foi escrito antes do código**. Não invente logs nem alegue TDD
retroativo. Não há obrigação de bloquear commits Red por hooks locais.

Para uma alteração exclusivamente declarativa, registre a validação de formato,
sintaxe e ferramenta pertinente. Não crie um teste artificial que apenas repita
o conteúdo da configuração. Mudanças de comportamento em scripts também exigem
TDD; um script operacional complexo precisa de testes próprios.

## Preparação e comandos

Na raiz, com Node.js 26.8.1, pnpm 12.3.4 e uv 0.12.10 disponíveis:

```text
pnpm install --frozen-lockfile
pnpm python:sync
```

`python:sync` executa `uv sync --locked --all-groups` usando Python 3.13.12 e a
`.venv`. Um lockfile incompatível deve falhar, sem regeneração silenciosa no CI.
Para alterações intencionais de dependências Python, use `pnpm python:lock` e
revise o diff de `uv.lock` antes de sincronizar.

| Comando                                | Verificação                                                      |
| -------------------------------------- | ---------------------------------------------------------------- |
| `pnpm lint`                            | ESLint e Ruff.                                                   |
| `pnpm format:check`                    | Prettier e Ruff format, sem editar arquivos.                     |
| `pnpm typecheck`                       | TypeScript e mypy.                                               |
| `pnpm test:web`                        | Vitest em execução única, JUnit e cobertura.                     |
| `pnpm test:api`                        | pytest de unidade da API com cobertura.                          |
| `pnpm test:integration`                | pytest com PostgreSQL/pgvector reais; exige `TEST_DATABASE_URL`. |
| `pnpm test:e2e:install`                | Instala o Chromium usado pelo Playwright no ambiente local.      |
| `pnpm test:e2e:install:ci`             | Instala Chromium e dependências do sistema no CI Linux.          |
| `pnpm test:e2e`                        | Playwright Chromium com API e web iniciadas pela configuração.   |
| `pnpm tdd:guard:record -- <testes...>` | Congela hashes dos testes após um Red válido.                    |
| `pnpm tdd:guard:verify`                | Falha se um teste Red congelado foi alterado/removido.           |
| `pnpm tdd:guard:clear`                 | Encerra o snapshot após Green e verificações finais.             |
| `pnpm build`                           | Build da web com Vite.                                           |
| `pnpm check`                           | Lint, formato, tipos, unidades e build.                          |
| `pnpm check:all`                       | `check`, integração e E2E; requer banco e Chromium preparados.   |
| `pnpm infra:config`                    | Valida o Compose local pelo provedor configurado no Podman.      |
| `pnpm infra:up`                        | Sobe PostgreSQL/pgvector pelo Podman e aguarda o healthcheck.    |
| `pnpm infra:down`                      | Encerra o stack local preservando o volume nomeado.              |
| `pnpm db:migrate`                      | Aplica as migrações Alembic até `head`; exige `DATABASE_URL`.    |
| `pnpm db:current`                      | Mostra a revisão Alembic atual; exige `DATABASE_URL`.            |

Para focar o ciclo Red/Green da web, use `pnpm exec vitest run` com o caminho do
teste e, quando necessário, `-t` com seu nome. Para Python, use
`pnpm python:run pytest` com o caminho ou node ID do teste. `--no-cov` pode ser
usado nessa execução focada para separar a assertion dos limiares da suíte; a
verificação final usa os scripts completos, com a cobertura habilitada.

Desde a E00.2, há dois gates complementares de cobertura Python, ambos em 85%:
as unidades medem os módulos da API, exceto `arxen_api.persistence`; a integração
mede exatamente esse módulo SQL contra PostgreSQL real, com branches habilitados.
A exclusão unitária é específica a esse arquivo, não a uma pasta genérica. Novos
módulos continuam sujeitos ao gate unitário até uma decisão explícita de camada.
As configurações ficam em `pyproject.toml` e `tests/integration/coverage.ini`.
`pnpm check` verifica o primeiro gate; `pnpm test:integration` verifica o segundo.
O CI Gate exige ambos. Não substituir a integração por mocks para aumentar a
cobertura aparente. Os relatórios são separados em `coverage/api/` e
`coverage/integration/`, com arquivos de dados de cobertura distintos.

## Banco e E2E locais

Use o ambiente sintético descrito em [infra/README.md](../infra/README.md).
Com Podman e um provedor Compose disponíveis, no PowerShell:

```powershell
pnpm infra:up
$env:DATABASE_URL = 'postgresql://arxen_test:arxen_test_password@127.0.0.1:5433/arxen_test'
pnpm db:migrate
$env:TEST_DATABASE_URL = 'postgresql://arxen_test:arxen_test_password@127.0.0.1:5433/arxen_test'
pnpm test:integration
pnpm test:e2e:install
pnpm test:e2e
pnpm infra:down
```

Em Bash, use `export TEST_DATABASE_URL='postgresql://arxen_test:arxen_test_password@127.0.0.1:5433/arxen_test'`
no lugar da atribuição PowerShell. O teste de integração deve falhar quando a
conexão necessária não estiver configurada ou não funcionar; não transformar
ausência de banco em skip ou sucesso.

Os testes de migração e contratos criam bancos temporários com nomes únicos a
partir da conexão de teste, usando `template0`. O usuário sintético precisa de
`CREATEDB` e da permissão necessária para habilitar pgvector. A fixture remove
somente o banco que criou, após fechar as conexões. Ela não reseta o banco-base
configurado e não faz fallback para ele se faltar permissão. A revisão inicial
tem sua própria regressão; o teste de head chama `pnpm db:migrate` em banco vazio,
grava os cinco contratos, reabre por nova conexão e testa downgrade em banco
descartável. Rodar qualquer desses testes isoladamente independe da ordem da suíte.

Para essas fixtures, a URL de teste não pode conter query parameters ou fragmentos,
inclusive parâmetros aparentemente inofensivos como `sslmode`. A validação recusa
essas formas antes de abrir conexão ou emitir DDL: parâmetros como `dbname`
poderiam sobrepor o nome temporário ao serem interpretados por outro driver.
Após criar o banco, a fixture consulta `current_database()` pela URL derivada e
somente entrega o destino à migração se o nome corresponder ao banco criado.
Uma divergência interrompe o fluxo e remove apenas o temporário da própria fixture.
Essa restrição pertence à infraestrutura sintética de testes; não altera o
contrato geral de `DATABASE_URL` da aplicação.

As migrações usam Alembic 1.20.0 com SQLAlchemy 2.0.54 no grupo Python
`migration`. O acesso de domínio permanece em `psycopg`; SQLAlchemy está presente
para o mecanismo de migração, não como decisão de ORM para a aplicação.

No Windows validado em 16/09/2026, `podman compose` delegou ao Docker Compose
v5.5.1 e aceitou `--wait`. O runtime dos contêineres continuou sendo Podman. O CI
Linux mantém sua validação declarativa com `docker compose` no runner do GitHub.

Playwright inicia `pnpm dev:api` em `127.0.0.1:8000/healthz` e o build/preview da
web em `127.0.0.1:4173`. As duas portas precisam estar livres; os testes não
reutilizam servidores já abertos. A configuração encerra os subprocessos que
iniciou. O smoke E2E atual não depende do banco. Traces, vídeos e capturas são
mantidos quando há falha, junto do relatório e JUnit.

## Dados e qualidade dos testes

Use somente dados fabricados, inclusive nomes, textos, documentos e vetores. Não
copie o acervo ou as specs privadas para fixtures, logs ou artefatos. Modelos e
pesquisa externa devem usar substitutos determinísticos com falhas controláveis;
nenhum teste de PR deve exigir chave de modelo ou chamada paga. Um mock valida o
contrato exercitado, não a capacidade de um fornecedor.

Verifique efeitos observáveis, invariantes e falhas relevantes. Teste SQL e
operações de pgvector contra o banco real na integração. As credenciais locais
administrativas servem somente ao smoke isolado: elas não demonstram autorização
de aplicação ou RLS, que precisarão de papéis e testes próprios quando implementados.

Mantenha os limiares de cobertura nas configurações e analise o relatório; não
reduza limiares para ocultar falhas. Não use testes vazios, `.only`, skips sem
justificativa, `passWithNoTests` ou opções equivalentes para produzir aprovação.

## Contrato do CI

O workflow `.github/workflows/ci.yml`, nome **CI**, executa em PRs para `main`,
pushes em `main`, disparo manual e `merge_group: checks_requested`.
Não há filtros por caminho. Os checks são:

| Check                                 | Execução                                                                |
| ------------------------------------- | ----------------------------------------------------------------------- |
| `Quality & unit (ubuntu-24.04)`       | Qualidade, unidades com cobertura e build em Linux.                     |
| `Quality & unit (windows-2025)`       | Mesmos scripts, a partir de Windows PowerShell.                         |
| `Integration (PostgreSQL + pgvector)` | Linux, serviço PostgreSQL 17/pgvector 0.8.6 com healthcheck.            |
| `E2E (Chromium)`                      | Linux, navegador real e subprocessos da API/web.                        |
| `CI Gate`                             | Agrega os três jobs, incluindo as duas entradas da matriz de qualidade. |

`CI Gate` usa `always()` e só aprova se **quality**, **integration** e **e2e**
retornarem exatamente `success`. Falha, cancelamento ou skip não satisfazem essa
condição. Não remover dependências do gate para acomodar falhas. A matriz usa
`fail-fast: false`, permitindo observar o resultado das duas plataformas.

Antes do upload, cada job de qualidade exige arquivos não vazios de JUnit web/API,
LCOV web, cobertura XML da API e HTML do build. Um comando que termine sem erro,
mas não gere suas evidências, deve reprovar o job. O setup também confere que
`pnpm --version` retorna a versão fixada.

O job de integração exige JUnit e cobertura XML não vazios, além do gate de 85%
da persistência. Os relatórios XML/HTML de integração acompanham seu artefato.

O token do workflow tem somente `contents: read`; o checkout não persiste suas
credenciais. Novos commits cancelam a execução anterior do mesmo PR. Cada job tem
timeout. Não há `continue-on-error`, segredos de produção ou publicação automática.

O job de qualidade Linux também valida o workflow com **actionlint 1.7.12** e
executa `pnpm exec docker compose -f infra/compose.yaml config --quiet`. O binário
de actionlint vem da [release oficial](https://github.com/rhysd/actionlint/releases/tag/v1.7.12),
com SHA-256 conferido antes de executar. O comando equivalente, quando actionlint
está no PATH local, é `pnpm exec actionlint .github/workflows/ci.yml`.

Os uploads executam com `always()`, inclusive após falhas. Os artefatos
`unit-ubuntu-24.04`, `unit-windows-2025`, `integration-results` e
`playwright-chromium` têm retenção de **cinco dias**. Uma falha de preparação pode
impedir a geração de arquivos; nesse caso o upload avisa, e a falha do job continua
visível. Cobertura e resultados ficam em `coverage/`, `test-results/` e
`playwright-report/`, ignorados pelo Git.

A aplicação da proteção de `main` é uma ação separada, descrita em
[.github/rulesets/README.md](../.github/rulesets/README.md). O arquivo JSON, por si
só, não ativa regras no GitHub.

## Actions e atualização de dependências

As Actions são fixadas por SHA de commit. Os SHAs abaixo foram obtidos dos
repositórios oficiais com `git ls-remote --tags`; para tags anotadas foi usado o
commit indicado por `^{}`, não o objeto da tag.

| Action                                                                | Tag conferida | Commit                                     |
| --------------------------------------------------------------------- | ------------- | ------------------------------------------ |
| [actions/checkout](https://github.com/actions/checkout)               | v6.1.0        | `d23441a48e516b6c34aea4fa41551a30e30af803` |
| [actions/setup-node](https://github.com/actions/setup-node)           | v6.5.0        | `249970729cb0ef3589644e2896645e5dc5ba9c38` |
| [pnpm/setup](https://github.com/pnpm/setup)                           | v2.0.1        | `4700d737c3d7a2e7199f3d42a920f0bf7f34e411` |
| [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv)           | v8.3.2        | `11f9893b081a58869d3b5fccaea48c9e9e46f990` |
| [actions/upload-artifact](https://github.com/actions/upload-artifact) | v7.0.1        | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |

O setup de Node precede o pnpm. A Action oficial `pnpm/setup` v2 instala o
executável nativo de pnpm v11 ou superior; `install: false` mantém a instalação
congelada das dependências no passo explícito do workflow.
uv e Python são preparados antes de `pnpm python:sync`. Atualize pins em PR e
execute novamente os checks. Um exemplo de reconferência de tag anotada:

```text
git ls-remote --tags https://github.com/pnpm/setup.git refs/tags/v2.0.1 refs/tags/v2.0.1^{}
```

`.github/dependabot.yml` habilita atualizações semanais de GitHub Actions, sem
automergir. Na consulta de **16/09/2026**, a
[matriz oficial do Dependabot](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories)
listava pnpm v7–v10 sob o ecossistema `npm`, e uv v0.11 sob `uv`. Isso não confirma
compatibilidade com os pins deste projeto, **pnpm 12.3.4 e uv 0.12.10**. Portanto,
atualizações automáticas dessas duas ferramentas/ecossistemas não estão habilitadas.

Até confirmar suporte, revise dependências JS/Python manualmente em PRs, preserve
os pins e regenere os lockfiles pelas ferramentas fixadas. Para habilitar depois,
registre a fonte que confirma as versões e valide um PR que atualize os lockfiles
sem migração indevida, com instalação congelada e `CI Gate` aprovado. Não configure
`pip` como substituto de `uv` nem um ecossistema fictício `pnpm`.
