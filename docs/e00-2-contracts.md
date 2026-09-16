# E00.2 — contratos centrais

## Escopo reconstruído

A E00.1 foi integrada em `main` pela PR #4 (`ff542c0`). Esta etapa estabelece
somente os contratos persistentes usados pelas próximas subetapas da fundação.
A referência normativa permanece nos documentos privados 14–18, fora do Git.

| Contrato | Obrigatório nesta etapa | Entrega posterior |
| --- | --- | --- |
| Case | ID opaco do servidor, título e instante de criação; gravação e leitura | Identidade sintética e fluxo de casos em E00.3; responsável autenticado, organização e RLS em E01 |
| Message | Caso explícito, autoria por papel, conteúdo preservado e sequência por caso | Recebimento HTTP, idempotência, sessões e conversa em E00.4 |
| Source | Identidade estável e referência verificável ao trecho de uma mensagem do mesmo caso | Documentos/versionamento documental, PDF, extração e pesquisa nas etapas correspondentes |
| Task | Caso, objetivo, estado inicial e domínio dos estados normativos | Transições com plano, autorização, orçamento e worker a partir de E00.5/E02 |
| Event | ID persistido, caso, tarefa opcional do mesmo caso, sequência, instante, ator, tipo e payload mínimo | SSE, outbox, retenção de cursor, eventos de recursos versionados e recuperação operacional |

Os IDs são UUIDs aleatórios gerados pelo PostgreSQL. Os instantes usam
`timestamptz` e os objetos Python devolvem UTC explícito. Não há autorização por ID:
a camada de persistência é interna e ainda não está ligada a rotas de domínio.
As próximas etapas deverão estabelecer o contexto autorizado antes de chamar essa
camada. Não serão criadas organizações ou identidades fictícias como placeholders.

## Decisões mínimas

- Usar `psycopg` com SQL explícito e dataclasses; nenhuma dependência nova ou ORM.
- Começar Source com o tipo mensagem: ID da mensagem, intervalo de caracteres e
  trecho. O intervalo é zero-based, com fim exclusivo, contado em pontos de código
  Unicode. Uma FK composta impede referência a mensagem de outro caso. O trecho
  precisa corresponder ao conteúdo persistido. Novos tipos terão migrações próprias.
- Preservar mensagens, fontes e eventos por inserção; alterações históricas não
  recebem uma operação de overwrite. Revisões completas permanecem futuras.
- Ordenar mensagens e eventos por sequência do caso, independentemente de
  timestamps iguais. A atribuição atômica da sequência é integridade local do
  contrato, sem introduzir fila, concessões ou coordenação operacional.
- Criar tarefas em `draft`. A lista de estados é validada na persistência, mas não
  existe comando de transição nem simulação de aprovações, orçamento ou execução.
- Eventos referenciam apenas caso e tarefa nesta etapa. Não criar ponteiros
  polimórficos sem FK para recursos ainda inexistentes. Revisão do recurso será
  adicionada quando houver a primeira mutação versionada.

Autoria por papel em mensagens e o campo ator em eventos são metadados internos;
não constituem identidade autenticada nem aprovação humana. O payload de evento
é um objeto JSON pequeno de atributos, não um recipiente para todo o caso.

## Slices TDD

1. Base temporal tipada, normalização UTC e rejeição de instante sem fuso.
2. Case: geração de ID e persistência real com campos obrigatórios.
3. Message: relação com caso, histórico ordenado e preservação de conteúdo.
4. Source: trecho verificável, referência estável e rejeição de cruzamento de caso.
5. Task: objetivo, criação em draft e estados válidos no PostgreSQL.
6. Event: associação, ordem por caso e leitura após sequência persistida.
7. Integração dos cinco contratos, rollback e leitura por uma nova conexão.

Cada slice observa Red comportamental, registra o snapshot antes da implementação
e verifica que os testes permanecem intactos. O teste legado de migração inicial
será preservado em banco isolado e separado do teste do novo head.

## Decisões abertas e limites

Continuam abertas para suas etapas: provedor de identidade, modelo, embeddings,
pesquisa, hospedagem, retenção e perfil de documentos. Não bloqueiam esta entrega.
OIDC, organizações, objetos, ingestão, ferramentas reais, APIs e telas funcionais,
RAG, revisão jurídica e concorrência operacional não pertencem à E00.2.

E00.3 ainda não começou. A conclusão da E00.2 depende das evidências locais,
review em contexto novo e CI Gate do commit final, registrados separadamente.
