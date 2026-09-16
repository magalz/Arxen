# E00.3 — identidade sintética e casos

## Objetivo e recorte

A E00.2 foi aceita e integrada pela PR #5 em `6192465`. Esta etapa demonstra
uma identidade de desenvolvimento/teste criando, consultando e reabrindo o mesmo
caso persistido em PostgreSQL, inclusive após recriar a aplicação.

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
  identidade ou sem atribuição não é disponibilizado pela API, mesmo conhecendo
  seu ID. Os casos internos criados pela E00.2 não são atribuídos automaticamente.
- IDs e instantes continuam gerados pelo banco. A resposta de criação só é
  entregue após o commit. Leituras não criam casos nem alteram seu conteúdo.
- Uma nova revisão Alembic estende o esquema. Migrações aplicadas da E00.1/E00.2
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
