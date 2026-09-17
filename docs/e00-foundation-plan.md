# Plano operacional da E00 — Fundação

Registro de decisão de 16/09/2026. Este documento transforma a etapa macro E00 da
spec privada do alpha em entregas pequenas e verificáveis dentro do repositório,
sem copiar o conteúdo privado da especificação ou do caso de referência.

Fonte normativa privada para retomada em outro contexto: `/arxen/specs`, documentos
`14-spec-alpha.md` a `18-plano-de-implementacao-e-aceite.md`, versão 0.1 consolidada
em 14/09/2026. Esses arquivos permanecem fora do Git e devem ser consultados apenas
quando necessário para validar decisões, invariantes ou critérios de aceite.

## Decisão

O roadmap macro do alpha permanece **E00–E08**, conforme a especificação de
implementação mantida fora do repositório. Não criar um segundo roadmap paralelo.
Para execução, a E00 é subdividida em E00.1–E00.7 para permitir PRs menores,
evidência TDD real e revisão técnica independente.

O critério macro de conclusão da E00 continua sendo um percurso sintético no qual
um usuário autenticado abre um caso e recebe uma resposta persistida. E01 em diante
mantém seu escopo próprio; a fundação não deve antecipar isolamento completo,
upload retomável, OpenHands, OCR final ou provedores reais apenas para encerrar E00.

## Subetapas da E00

| Subetapa                                    | Escopo                                                                                                                    | Evidência principal                                                                                                                  |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **E00.1 — Banco, migrações e configuração** | Migrações versionadas, configuração tipada e preparação reproduzível do PostgreSQL/pgvector.                              | Banco vazio recebe todas as migrações; esquema esperado fica disponível e a configuração inválida falha de forma explícita.          |
| **E00.2 — Contratos centrais**              | Contratos mínimos de caso, mensagem, fonte, tarefa e evento, com persistência compatível com as invariantes já aprovadas. | Testes demonstram criação e integridade dos contratos sem depender de provedores externos.                                           |
| **E00.3 — Identidade sintética e casos**    | Identidade apenas para desenvolvimento/teste e primeiro fluxo persistente de caso.                                        | Usuário sintético cria, consulta e reabre o mesmo caso. OIDC e isolamento completo permanecem em E01.                                |
| **E00.4 — Conversa persistente**            | Persistência de mensagem e histórico entre requisições/sessões.                                                           | Mensagem confirmada permanece disponível após nova leitura/reabertura.                                                               |
| **E00.5 — Worker falso e eventos**          | Tarefa, eventos e worker/provedor determinístico com sucesso e falhas controláveis.                                       | Entrada gera progresso e resposta reproduzível sem chamadas reais a modelo.                                                          |
| **E00.6 — Percurso web vertical**           | UI mínima ligando identidade sintética, caso, mensagem, tarefa e resposta.                                                | E2E: criar caso, enviar mensagem, receber resposta, recarregar e preservar histórico.                                                |
| **E00.7 — Anexo/fonte PDF sintético**       | Anexar uma fixture PDF sintética pelo percurso web, associá-la ao caso e permitir que o worker falso a referencie.        | E2E anexa o PDF sintético pela interface e demonstra progresso/resposta com fonte persistida, sem antecipar upload retomável da E01. |

Cada subetapa pode gerar mais de uma PR se o comportamento observável justificar a
separação. Não agrupar mudanças apenas para reduzir número de PRs.

## Objetivo atual: E00.4 — conversa persistente

A E00.1 foi integrada pela PR #4 em `ff542c0`; a E00.2 foi aceita e integrada
pela PR #5 em `6192465`, com review independente e CI aprovados. Seus contratos
e evidências permanecem em [e00-2-contracts.md](e00-2-contracts.md) e
[validation-e00-2.md](validation-e00-2.md).

A E00.3 foi integrada pela PR #6 em `2bad5a0`, com identidade sintética, casos e
responsabilidade persistida. A configuração Sonar foi integrada pela PR #7 em
`81a26c8`. Os contratos da etapa anterior estão em
[e00-3-synthetic-cases.md](e00-3-synthetic-cases.md).

A branch atual é `feat/e00-4-persistent-conversation`. O recorte está em
[e00-4-persistent-conversation.md](e00-4-persistent-conversation.md): envio autorizado,
histórico paginado, releitura após recriação da aplicação e idempotência de envios,
inclusive concorrentes. A revisão `20260916_0004` conserva os contratos anteriores.
E00.5 e E01 não foram iniciadas; não há worker ou resposta automática nesta entrega.

A conclusão exige `pnpm check`, integração real, guard íntegro, fresh-context
review do diff final e CI Gate verde. O merge de cada nova PR permanece uma
decisão explícita do responsável pelo projeto.

## Registro do escopo da E00.1

A branch de trabalho inicial foi `feat/e00-foundation`. Os critérios abaixo
registram a entrega que estabeleceu banco, migrações e configuração.

### Escopo obrigatório

1. Usar **Alembic 1.20.0** como ferramenta de migração, com SQLAlchemy 2.0.54
   somente como base técnica do migrador. Ambos são open source sob licença MIT.
   O domínio continua usando `psycopg`; a adoção do Alembic não implica adoção do
   ORM do SQLAlchemy.
2. Introduzir configuração tipada para os valores necessários à aplicação e às
   migrações, sem versionar `.env` ou segredos.
3. Criar migração inicial versionada para o menor esquema necessário à próxima
   etapa; não antecipar todo o modelo lógico do alpha.
4. Demonstrar criação do esquema a partir de um banco PostgreSQL/pgvector vazio.
5. Demonstrar falha explícita e útil quando configuração obrigatória estiver
   ausente ou inválida.
6. Manter o fluxo local compatível com Podman e o CI compatível com os runners do
   GitHub.
7. Atualizar instruções de execução e evidências reais da etapa.

### Fora do escopo da E00.1

- autenticação OIDC ou autorização/RLS completa;
- organizações, convites e isolamento entre casos;
- upload retomável ou armazenamento de objetos;
- OpenHands ou chamadas reais a modelos;
- OCR, pesquisa externa e entregáveis jurídicos;
- implementação antecipada de todas as tabelas descritas na spec.

## TDD e validação da E00.1

Comportamento novo segue Red → Green → Refactor. O teste Red deve falhar pela
ausência do comportamento pretendido, não por dependência, importação ou banco
indisponível. Configuração puramente declarativa recebe validação de sintaxe e da
ferramenta pertinente; não criar teste artificial que apenas repita o arquivo.

No fechamento da etapa, registrar no mínimo:

- comandos e resultado do Red/Green/Refactor dos comportamentos implementados;
- aplicação das migrações em banco vazio e verificação do esquema/resultados;
- `pnpm test:integration` quando a mudança tocar o banco real;
- `pnpm check` completo;
- E2E apenas se a mudança da E00.1 alterar o percurso já coberto pelo navegador;
- limitações e verificações não executadas, sem inferir aprovação.

## Review obrigatório em contexto novo

Nenhuma subetapa E00.x é considerada concluída apenas porque os testes e o CI estão
verdes. O fechamento exige **review em um contexto novo**, diferente daquele que
implementou a mudança. Essa regra existe para reduzir viés de continuidade e
pressupostos carregados da implementação.

O contexto novo recebe somente o necessário para avaliar a entrega:

1. objetivo e Definition of Done da subetapa;
2. instruções vigentes do repositório;
3. diff/commits finais;
4. testes e evidências observadas;
5. documentação técnica estritamente necessária.

Não fornecer como base a argumentação da sessão que implementou a solução. O
revisor deve reconstruir sua conclusão a partir dos artefatos finais.

O parecer precisa deixar evidência verificável no PR ou registro equivalente:
identificação do contexto/revisor, commit ou diff revisado, escopo, resultado,
achados bloqueantes e sua resolução. Um `CI Gate` verde ou a ausência de aprovação
humana obrigatória no GitHub não substitui esse registro.

Para E00.1, usar como referência o padrão de review do ECC: revisão geral de código
e mantenibilidade, revisão especializada de banco/migrações e revisão de segurança
quando a configuração introduzir fronteiras sensíveis. Ferramentas/agentes podem
variar por harness; o requisito é a independência do contexto e a cobertura das
perspectivas necessárias, não um nome específico de agente.

### Achados e fechamento

- Achados **bloqueantes** de correção, segurança, integridade de dados, migração,
  teste ou aderência à spec impedem o encerramento da etapa.
- Achados consultivos podem ser aceitos como dívida explícita somente quando não
  comprometem o critério de aceite atual e possuem justificativa registrada.
- Correções decorrentes do review recebem testes de regressão quando alteram
  comportamento e passam novamente pelas verificações pertinentes.
- Após as correções, o revisor em contexto novo confirma a resolução dos achados
  bloqueantes ou uma nova revisão independente é executada.
- Mudança material feita depois do parecer invalida a cobertura daquela parte do
  review e exige nova revisão em contexto novo sobre o estado final.

## Definition of Done da E00.1

E00.1 termina somente quando todos os itens abaixo forem verdadeiros:

- migrações e configuração necessárias estão implementadas e documentadas;
- banco vazio pode ser preparado de forma reproduzível;
- falhas de configuração relevantes são explícitas e testadas quando comportamentais;
- testes pertinentes e `pnpm check` estão aprovados;
- integração PostgreSQL/pgvector foi executada quando pertinente;
- dependências novas estão fixadas e lockfiles atualizados corretamente;
- nenhum segredo, dado real, spec privada ou saída de execução foi versionado;
- review técnico em **contexto novo** foi concluído;
- o parecer identifica o commit/diff final revisado e está registrado na PR ou
  evidência equivalente;
- todos os achados bloqueantes do review foram resolvidos e revalidados;
- documentação descreve o estado efetivamente demonstrado, sem antecipar E00.2/E01.

Somente após esse gate o objetivo ativo muda para E00.2.
