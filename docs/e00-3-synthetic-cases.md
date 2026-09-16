# E00.3 — identidade sintética e casos

## Objetivo e recorte

A E00.2 foi aceita e integrada pela PR #5 em `6192465`. O objetivo desta etapa é
demonstrar uma identidade de desenvolvimento/teste criando, consultando e reabrindo
o mesmo caso persistido em PostgreSQL, inclusive após recriar a aplicação.

**Estado atual: implementação parcial, aguardando revisão independente.** Estão
implementados o opt-in de configuração e `GET /api/v1/me`. Criação/consulta de
casos com identidade e a nova migração ainda não foram implementadas. O objetivo
completo da E00.3 não está demonstrado por este primeiro slice.

Referências normativas: specs privadas 14–18 e a subdivisão da E00 no
[plano da fundação](e00-foundation-plan.md). As specs permanecem fora do Git.

O recorte inicial da API é `GET /api/v1/me`, `POST /api/v1/cases` e
`GET /api/v1/cases/{case_id}`. Reabrir significa consultar novamente o mesmo ID;
não existe comando de desarquivamento nesta entrega. Listagem paginada, edição,
arquivamento, conversa e interface recebem suas próprias entregas.

## Invariantes e decisões para a etapa completa

- O modo sintético exige ativação explícita e ambiente `development` ou `test`.
  Por padrão, somente as rotas já existentes são registradas. Ativá-lo em outro
  ambiente deve falhar na configuração.
- A identidade e o token de teste vêm da configuração do servidor. O cliente
  apresenta o token Bearer; campos ou headers de identidade não escolhem o dono.
  Esse mecanismo é um adaptador sintético, não a autenticação OIDC da E01.
- A relação entre caso e identidade sintética deverá ser persistida. Um caso de
  outra identidade ou sem atribuição deverá ser inacessível pela API, mesmo
  conhecendo seu ID. Casos internos da E00.2 não deverão ser atribuídos
  automaticamente.
- IDs e instantes continuam gerados pelo banco. A resposta de criação só é
  entregue após o commit. Leituras não criam casos nem alteram seu conteúdo.
- Uma nova revisão Alembic deverá estender o esquema. Migrações da E00.1/E00.2
  permanecem intactas. Não serão criadas organizações, memberships ou RLS nesta
  etapa; esses controles continuam obrigatórios antes de uso real na E01.

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

Cada Red válido será congelado antes da implementação. O guard da E00.2 foi
verificado após o merge; os hashes históricos permanecem em sua documentação.
Mudanças necessárias em expectativas de versão de migração exigem justificativa
e revisão separada, preservando os cenários de integridade anteriores.

## Limites

A E00.4 ainda não começou. Não há sessão de produção, login OIDC, organizações,
convites, worker, SSE, upload ou chamadas de modelo. Não se trata de ambiente
para documentos reais. Novas dependências não estão previstas.

## Executar o slice de identidade

O servidor lê estas variáveis ao criar a aplicação:

| Variável                       | Valor/condição                                                  |
| ------------------------------ | --------------------------------------------------------------- |
| `ARXEN_SYNTHETIC_AUTH_ENABLED` | `true` para ativar; ausente ou `false` desativa                 |
| `ARXEN_ENV`                    | `development` ou `test` quando ativado                          |
| `ARXEN_SYNTHETIC_USER_ID`      | UUID não nulo definido pelo operador; preservar entre reinícios |
| `ARXEN_SYNTHETIC_TOKEN`        | Token local não vazio, sem espaços; sem valor padrão            |
| `DATABASE_URL`                 | URL PostgreSQL válida; `/me` e `/healthz` não abrem conexão     |

Inicie com `pnpm dev:api`, ligado a `127.0.0.1` pelo script existente. Consulte
`GET /api/v1/me` com `Authorization: Bearer <token-local>`. A resposta contém
`id` e `synthetic: true`, com `Cache-Control: no-store`. Token ausente ou incorreto
retorna 401. O ID informado pelo cliente em `X-User-Id` não altera a identidade.

Com o modo desativado, a rota não é registrada nem aparece no OpenAPI. Um ambiente
indevido ou configuração inválida causa falha explícita ao criar a aplicação.
O token não aparece no `repr` da configuração nem nas respostas testadas. Não
versionar variáveis locais nem expor este adaptador como autenticação de produção.

O uso de `HTTPBearer` segue a [referência do FastAPI](https://fastapi.tiangolo.com/reference/security/).
As credenciais sintéticas são conferidas pelo adaptador do projeto.

## Próximo slice e bloqueio atual

`test_core_contracts.py` verifica `pnpm db:migrate` e espera a revisão da E00.2.
Antes da nova revisão, é necessária a revisão separada da evolução dessa
expectativa, mantendo os testes de criação, commit, reabertura e rollback. O
arquivo continua congelado e inalterado.

A coordenação de workers recusou chamadas por `WORKER_IDENTITY_LOST`. Uma tentativa
de consulta em contexto novo pelo Codex CLI instalado, com sandbox read-only,
encerrou por limite de uso sem produzir parecer. Nenhuma dessas tentativas conta
como revisão. A PR deste slice permanece em rascunho até concluir as etapas e os
reviews pertinentes. Evidências em [validation-e00-3.md](validation-e00-3.md).
