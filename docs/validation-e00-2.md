# Validação da E00.2

Branch `feat/e00-2-core-contracts`, iniciada a partir de `ff542c0` (PR #4).
Este registro será completado com os resultados observados da implementação.

## Correções de testes tratadas separadamente

### Regressão da migração inicial

O teste herdado executava `upgrade head` e exigia a revisão inicial. Com novas
migrações, essas duas condições deixam de representar o mesmo requisito. Antes
dos Reds de persistência, o worker de consulta de escopo (`worker-1`, contexto
próprio, somente leitura) aprovou a separação: a regressão da E00.1 migra
explicitamente para `20260916_0001`, mantendo suas assertions de extensão e revisão;
o novo teste de head demonstrará os contratos da E00.2 a partir de banco vazio.

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
não foi limpo; um novo Red e snapshot precedem a normalização.
