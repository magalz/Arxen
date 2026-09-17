# E00.3 — identidade sintética e casos

## Objetivo e recorte

A E00.2 foi aceita e integrada pela PR #5 em `6192465`. O objetivo desta etapa é
demonstrar uma identidade de desenvolvimento/teste criando, consultando e reabrindo
o mesmo caso persistido em PostgreSQL, inclusive após recriar a aplicação.

Estão implementados o opt-in de configuração, a identidade HTTP e o fluxo
persistente de criação, consulta e reabertura de casos. Os testes exercitam duas
identidades, novas conexões e aplicações recriadas contra PostgreSQL real. As
evidências locais estão em [validation-e00-3.md](validation-e00-3.md); review
independente e CI são registrados na PR #6, vinculados ao SHA revisado.

Referências normativas: specs privadas 14–18 e a subdivisão da E00 no
[plano da fundação](e00-foundation-plan.md). As specs permanecem fora do Git.

O recorte inicial da API é `GET /api/v1/me`, `POST /api/v1/cases` e
`GET /api/v1/cases/{case_id}`. Reabrir significa consultar novamente o mesmo ID;
não existe comando de desarquivamento nesta entrega. Listagem paginada, edição,
arquivamento, conversa e interface recebem suas próprias entregas.

## Invariantes e decisões

- O modo sintético exige ativação explícita e ambiente `development` ou `test`.
  Por padrão, somente as rotas já existentes são registradas. Ativá-lo em outro
  ambiente deve falhar na configuração.
- A identidade e o token de teste vêm da configuração do servidor. O cliente
  apresenta o token Bearer; campos ou headers de identidade não escolhem o dono.
  Esse mecanismo é um adaptador sintético, não a autenticação OIDC da E01.
- A relação entre caso e identidade sintética é persistida. Um caso de outra
  identidade ou sem atribuição recebe 404 pela API, mesmo conhecendo seu ID.
  Casos internos da E00.2 permanecem sem atribuição automática.
- IDs e instantes continuam gerados pelo banco. A resposta de criação só é
  entregue após o commit. Leituras não criam casos nem alteram seu conteúdo.
- A revisão Alembic `20260916_0003` estende o esquema. Migrações da E00.1/E00.2
  permanecem intactas. Organizações, memberships e RLS continuam fora deste
  adaptador; os controles de produção pertencem à E01.

## Slices TDD

1. Configuração: modo desligado, ativação válida, recusa de ambiente/configuração
   indevidos e proteção do token em representações de diagnóstico.
2. Identidade HTTP: token obrigatório, identidade do servidor, rotas desligadas
   por padrão e contrato OpenAPI.
3. Persistência: vínculo com a identidade, isolamento das leituras e upgrade
   sem atribuir casos preexistentes.
4. API de casos: criação validada, commit antes da resposta, consulta/reabertura
   por outra instância e rejeição de acesso cruzado.
5. Verificação consolidada, documentação, PR, CI Gate e fresh-context review.

Cada Red válido foi congelado antes da implementação. O guard da E00.2 foi
verificado após o merge; os hashes históricos permanecem em sua documentação.
Mudanças necessárias em expectativas de versão de migração exigem justificativa
e revisão separada, preservando os cenários de integridade anteriores.

## Persistência e transações

Na retomada, a branch e a PR #6 foram conferidas em `f36ad08`, com árvore limpa
e os dez arquivos do guard intactos. A identidade do coordenador foi recuperada;
não havia worker responsável pela implementação restante.

A tabela `synthetic_case_owners` pertence exclusivamente ao adaptador sintético.
`case_id` é PK e FK para `cases(id)`; `owner_user_id` é UUID obrigatório e não nulo.
A PK permite somente um responsável por caso. O usuário sintético vem da
configuração, sem criar cadastro de usuários ou memberships fictícios. A migração
não atribui casos antigos nem modifica os cinco contratos da E00.2.

`CoreRepository.create_owned_case` grava caso e vínculo em um único comando SQL
com CTE, mantendo a transação sob responsabilidade do chamador. A rota abre uma
conexão por operação e conclui seu commit antes de retornar 201. O teste observa
os dois registros por outra conexão no instante de envio dos headers HTTP.
`get_owned_case` filtra ID e responsável em um JOIN; não utiliza a leitura interna
irrestrita como alternativa. Leituras não criam vínculos ou alteram casos.

O upgrade foi testado a partir de banco vazio e da revisão `20260916_0002` com
dados dos cinco contratos. O downgrade de `0003` remove somente os vínculos
sintéticos, preservando os casos e pgvector; foi exercitado exclusivamente em
bancos descartáveis. Uma reaplicação não restaura vínculos removidos. Migrações
do banco local são executadas explicitamente por `pnpm db:migrate`.

## Contrato HTTP

O corpo de criação admite somente título, omitível com o provisório `Novo caso`.
A API retorna ID, título e instante persistidos. Formato do título e tratamento
de valores inválidos foram fixados nos testes: corpo JSON obrigatório, `{}` aceito,
string estrita com espaços externos removidos, entre 1 e 200 caracteres, sem NUL
ou Unicode inválido. `null`, outros tipos e campos extras recebem 422. Identidade
no corpo não é aceita; header ou query não alteram o responsável validado.

| Rota                          | Resultado                                                             |
| ----------------------------- | --------------------------------------------------------------------- |
| `GET /api/v1/me`              | 200 com `id` e `synthetic: true`; não abre conexão com o banco.       |
| `POST /api/v1/cases`          | 201 após commit, com `id`, `title`, `created_at` e header `Location`. |
| `GET /api/v1/cases/{case_id}` | 200 com o mesmo registro persistido; reabertura usa esta rota.        |

Credencial ausente ou incorreta recebe 401 com `WWW-Authenticate: Bearer`.
Recurso inexistente, alheio ou sem atribuição recebe o mesmo 404 `Case not found`.
Corpo inválido ou UUID de caminho malformado recebe 422 `Invalid request`, sem
reproduzir valores enviados pelo cliente. Falhas de PostgreSQL retornam 503
`Case storage unavailable`, sem incluir SQL, credenciais ou diagnóstico do driver.
Essas respostas e as respostas de sucesso usam `Cache-Control: no-store`.
O OpenAPI declara os erros pertinentes a cada rota com `detail` textual, incluindo
o 422 genérico, para manter o contrato publicado coerente com as respostas HTTP.

São requisitos desta etapa a atomicidade, releitura entre aplicações, escopo de
responsável e upgrade que preserve dados antigos. Revisões para edição, fase,
objetivo, listagem, idempotência de criações e autenticação de produção pertencem
aos próximos recortes. A escolha do provedor OIDC permanece aberta para E01.

## Regressões de migração e guard

Após revisão independente separada, `test_core_contracts.py` continua executando
`pnpm db:migrate` e compara o resultado ao head único dos scripts versionados.
As assertions anteriores foram preservadas, com verificação adicional de que o
novo esquema existe e não atribui os casos criados internamente. A regressão
específica de `0003` usa upgrade explícito dessa revisão, incluindo dados antigos,
downgrade e re-upgrade em banco descartável. Os dois testes observaram novo Red
de ausência do esquema antes do snapshot autorizado e do DDL correspondente.

O guard final é cumulativo e contém dezesseis arquivos. A justificativa, os pareceres,
as duas exceções revisadas e os hashes estão no registro de validação. Nenhum teste
foi enfraquecido ou retirado da suíte para acomodar a implementação.

## Limites

A E00.4 e a E01 não foram iniciadas. Não há sessão de produção, login OIDC, organizações,
convites, worker, SSE, upload ou chamadas de modelo. Não se trata de ambiente
para documentos reais. Nenhuma dependência nova ou ORM foi adotado.

Não há idempotência de criação: repetir um POST após perder a resposta pode criar
outro caso. As falhas confirmadas por constraints demonstram rollback integral;
perder a conexão durante o commit pode deixar o resultado indeterminado para o
cliente. A API não repete automaticamente a gravação nem promete rollback nesse
caso. O tratamento operacional e a idempotência pertencem a um recorte posterior.

## Executar o fluxo sintético

O servidor lê estas variáveis ao criar a aplicação:

| Variável                       | Valor/condição                                                  |
| ------------------------------ | --------------------------------------------------------------- |
| `ARXEN_SYNTHETIC_AUTH_ENABLED` | `true` para ativar; ausente ou `false` desativa                 |
| `ARXEN_ENV`                    | `development` ou `test` quando ativado                          |
| `ARXEN_SYNTHETIC_USER_ID`      | UUID não nulo definido pelo operador; preservar entre reinícios |
| `ARXEN_SYNTHETIC_TOKEN`        | Token local não vazio, sem espaços; sem valor padrão            |
| `DATABASE_URL`                 | URL PostgreSQL válida; `/me` e `/healthz` não abrem conexão     |

Com o PostgreSQL sintético configurado, aplique `pnpm db:migrate`. Inicie com
`pnpm dev:api`, ligado a `127.0.0.1` pelo script existente. Consulte
`GET /api/v1/me` com `Authorization: Bearer <token-local>`. A resposta contém
`id` e `synthetic: true`, com `Cache-Control: no-store`. Token ausente ou incorreto
retorna 401. O ID informado pelo cliente em `X-User-Id` não altera a identidade.

Envie `POST /api/v1/cases` com o mesmo Bearer e um objeto JSON, por exemplo
`{"title":"Caso sintético"}` ou `{}`. Guarde o ID retornado e consulte
`GET /api/v1/cases/{id}`. Recriar o servidor com o mesmo UUID e banco preserva
o acesso; o token pode ser trocado na configuração sem alterar os vínculos.
Para demonstrar a recusa de acesso cruzado, configure outra instância com outro
UUID e token. Nenhum header de identidade substitui essa configuração.

Com o modo desativado, as rotas não são registradas nem aparecem no OpenAPI. Um ambiente
indevido ou configuração inválida causa falha explícita ao criar a aplicação.
O token não aparece no `repr` da configuração nem nas respostas testadas. Não
versionar variáveis locais nem expor este adaptador como autenticação de produção.

O uso de `HTTPBearer` segue a [referência do FastAPI](https://fastapi.tiangolo.com/reference/security/).
As credenciais sintéticas são conferidas pelo adaptador do projeto.

## Entrega e revisão

A PR #6 reúne a identidade e o fluxo persistente de casos. Sua liberação para
revisão do responsável exige `pnpm check`, integração real, guard íntegro,
fresh-context review do diff final e CI Gate do mesmo SHA. As consultas de escopo
e correção de testes não substituem esse review. O merge depende de autorização
explícita do responsável pelo projeto.
