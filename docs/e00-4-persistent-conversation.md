# E00.4 — conversa persistente

## Objetivo e recorte

Base: `81a26c8244dad0533a3f3b047eaf17d72e74d41c`, após integrar identidade/casos
e a configuração SonarCloud. Branch `feat/e00-4-persistent-conversation`.
Esta etapa expõe envio e histórico de mensagens para a identidade sintética dona
do caso. Uma confirmação HTTP deve sobreviver a nova conexão e recriação da API.

O escopo foi reconstruído das specs privadas 14–18 e do plano da fundação.
As specs permanecem fora do Git. Autenticação de produção, organização, RLS,
anexos, vinculação a tarefas, eventos operacionais, worker e resposta automática
continuam nas etapas próprias. Não há interface web de conversa neste recorte.

## Contrato definido antes dos testes

- `POST /api/v1/cases/{case_id}/messages`: objeto JSON obrigatório contendo somente
  `client_message_id` (UUID não nulo) e `content` (string estrita, de 1 a 16.000
  caracteres, com algum conteúdo não branco, sem NUL ou Unicode inválido).
  O texto válido é preservado exatamente, inclusive espaços e quebras de linha.
  Papel `user`, responsável, ID persistido, sequência e instante vêm do servidor.
- `Idempotency-Key`, quando informado, deve ser um UUID igual a `client_message_id`.
  Existe uma única identidade de envio, evitando dois sistemas concorrentes de
  deduplicação. Sem o header, o identificador obrigatório do corpo é a chave.
- Primeiro envio retorna 201; repetição com o mesmo conteúdo retorna 200 e a mesma
  mensagem. Mesmo identificador com outro conteúdo retorna 409. A comparação usa
  o texto imutável persistido, não uma cópia nem um hash sujeito a colisão.
  O escopo da chave é responsável/caso/operação; a tabela representa somente envio
  de mensagem e conserva o vínculo pelo tempo de vida do histórico sintético.
- `GET /api/v1/cases/{case_id}/messages`: retorna `items` ordenados por sequência
  crescente e `next_after_sequence`. Parâmetros: `after_sequence` entre zero e o
  máximo de bigint (padrão zero) e `limit` entre 1 e 100 (padrão 50).
  O próximo cursor é a sequência do último item entregue somente quando há mais
  itens; caso contrário é `null`. Repetir a consulta não grava ou altera registros.
  O cursor é um seletor, nunca autorização; novas mensagens podem aparecer na
  página seguinte. Não há promessa de snapshot imutável de toda a paginação.
- Credencial ausente/incorreta retorna 401; caso inexistente, alheio ou sem dono
  retorna o mesmo 404. Validação retorna 422 e armazenamento indisponível 503,
  com detalhes genéricos e `Cache-Control: no-store`. OpenAPI declara esses erros.

A autorização precede a consulta da chave de envio. Respostas 200/201 só são
emitidas após terminar o commit. Uma conexão perdida durante o commit pode deixar
o resultado indeterminado; reenviar a mesma chave/conteúdo permite reconciliar o
resultado sem uma repetição automática cega da escrita.

## Plano de mudança orientado pelo Memtrace

Antes de editar código existente, foi consultado o Memtrace local 1.2.5 em
`127.0.0.1:3030/mcp`, repositório indexado `app`. A consulta de preflight de
`create_synthetic_router` apontou impacto HIGH, 30 dependências e 17 fluxos,
incluindo a factory da aplicação, os testes de identidade, casos, erros e a
integração HTTP. `CoreRepository` e `Message` foram inspecionados no contexto do
grafo. Algumas buscas pontuais não resolveram símbolos, embora o preflight os
encontrasse; a leitura dos arquivos atuais complementou o índice.

Decisão: manter o contrato `Message`, as operações internas `add_message` e
`list_messages` e as rotas de casos; adicionar operações explicitamente autorizadas
ao repositório e um roteador de conversa separado, recebendo as dependências de
identidade e transação já existentes. As regressões apontadas pelo Memtrace serão
reexecutadas; ausência de aresta não é tratada como ausência de consumidor.

Uma nova migração após `20260916_0003` registra a chave de envio e a autoria
sintética em `synthetic_message_submissions`. FKs compostas vinculam o registro
ao responsável do caso e à mensagem do mesmo caso. Não são atribuídas chaves ou
autores sintéticos a mensagens antigas. A transação do chamador serializa os
envios pelo caso e engloba mensagem, contador e vínculo de idempotência.
Migrações anteriores e os dezesseis testes congelados permanecem preservados.

## Slices e aceite

1. Testes de migração e de persistência autorizada: esquema, replay, conflito,
   acesso, transação, rollback, ordem e concorrência real.
2. Testes HTTP: validação, autoria, contratos de erro, paginação, recriação e
   observação do commit antes dos headers de sucesso.
3. Implementação mínima após Red e snapshot; refatoração com testes congelados.
4. Verificação de cobertura, regressões, documentação e impacto final no Memtrace;
   commit/PR, review em contexto novo e CI do SHA final.

O CI herdado da base falhou no Quality Gate do Sonar por cobertura de código novo
58,4%, com exigência de 80%; todos os testes passaram. Migrações e o script do guard
aparecem sem cobertura importada, apesar de testes existentes. Essa lacuna de
instrumentação será tratada separadamente, preservando os gates de 85% e sem
excluir código para melhorar percentuais. Não se presume que o CI herdado passou.

## Estado

Planejamento registrado antes da implementação. Os Greens focados demonstraram
68 testes HTTP e 28 de integração de migração/persistência/conversa. Evidências,
limitações, review e CI são registrados em `validation-e00-4.md` e na PR.
A conclusão depende do review independente e dos checks do SHA final.

## Operação sintética

Use a configuração de identidade da E00.3 e aplique `pnpm db:migrate` ao banco
sintético antes de iniciar `pnpm dev:api`. Com o token Bearer da identidade dona
do caso, envie `{"client_message_id":"<UUID-não-nulo>","content":"Mensagem sintética"}`
para a rota POST. Preserve a chave até conhecer o resultado: caso a conexão caia,
reenvie exatamente a mesma chave e texto. Uma mensagem nova precisa de outra chave.

Consulte a rota GET com `limit` e, nas páginas seguintes, o `next_after_sequence`
retornado. Ao recarregar a interface futura, consultar o mesmo caso recupera o
histórico persistido. O limite atual é de 100 mensagens por página, não por caso.

A migração `0004` não altera mensagens antigas. Seu downgrade remove os vínculos
de idempotência/autoria sintética, conservando as mensagens e os demais contratos;
por isso serve apenas aos bancos descartáveis dos testes, não como recuperação
de produção. Transferência de responsabilidade e retenção/exclusão do histórico
exigirão decisões e migrações próprias nas etapas correspondentes.
