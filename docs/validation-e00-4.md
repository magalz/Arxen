# Validação da E00.4

Base `81a26c8244dad0533a3f3b047eaf17d72e74d41c`, branch
`feat/e00-4-persistent-conversation`. Somente dados sintéticos.
Contrato e plano em [e00-4-persistent-conversation.md](e00-4-persistent-conversation.md).

## Planejamento e coordenação

Memtrace local consultado antes de alterar código existente: inventário do repo
`app`, contexto de `CoreRepository`/`Message`, impacto e preflight do roteador.
O preflight apontou 30 dependências/17 fluxos, incluindo testes herdados; a mudança
foi delimitada a novas operações e um roteador de conversa separado. O índice
apresentou resoluções diferentes conforme o filtro; os arquivos atuais foram
conferidos antes de editar. Saídas do índice permanecem em `.artifacts`, fora do Git.

`agents` e `update_plan` recusaram a coordenação por ausência de identidade exata,
inclusive na retentativa. Isso não impediu leitura, Git, edição e testes. Nenhuma
tarefa foi presumida delegada. Uma revisão formal separada foi obtida em novo
contexto do navegador; o review final da entrega continua obrigatório.

## Reds observados antes da implementação

Comandos focados usam `pnpm python:run pytest <arquivos> --no-cov -q`.
O PostgreSQL local sintético estava disponível. A migração `0004` começou como
esqueleto sem DDL, usado somente nos bancos descartáveis das fixtures. Os métodos
novos começaram como stubs importáveis; o roteador novo não registrava endpoints.

| Seleção                                                                | Red observado       | Causa                                                                       |
| ---------------------------------------------------------------------- | ------------------- | --------------------------------------------------------------------------- |
| `test_message_submission_migration.py` + `test_message_submissions.py` | 16 failed           | Catálogo sem tabela de envios e stubs de envio/histórico alcançados         |
| `test_conversation_http.py` + `test_conversation_routes.py`            | 66 failed, 2 passed | Rotas e OpenAPI de conversa ausentes, inclusive na fronteira de repositório |
| `test_conversation_api.py`                                             | 12 failed           | Rotas ausentes e catálogo sem tabela para injeção das falhas reais          |

O guard foi ampliado cumulativamente de 16 para 18 e depois 20 arquivos.
Não houve alteração dos testes herdados. Os Reds não alegam que cada constraint
foi removida individualmente; isso será exercitado no Green contra PostgreSQL real.

## Correção formal de teste revisada separadamente

O primeiro comando de lint apontou duas strings SQL longas no novo teste de
migração. O batch também executou pytest, que demonstrou Red comportamental; por
isso o arquivo foi congelado antes de qualquer correção de formatação.

Revisor em contexto novo `6aab45c2-62fc-83e9-849c-7e0cac1de269`, somente leitura,
aprovou exclusivamente quebrar os dois literais SQL em literais adjacentes Python.
Parecer: APPROVE; BLOCKER/HIGH/MEDIUM/LOW zero para esse diff. A comparação verificou
strings de 81 e 86 bytes idênticas, espaços e placeholders preservados, dois
elementos na mesma ordem. Nenhuma assertion, cenário ou argumento muda.
O parecer não aprova implementação, Green nem entrega final.

Hash anterior do arquivo `tests/integration/test_message_submission_migration.py`:
`a4291427c335b292f6b6d4c6b3f3e3b4053b18ee91565642ffdb3b168f072d08`.
O manifesto anterior foi preservado localmente. Após aplicar apenas essas duas
quebras, a mesma seleção deve repetir o Red e receber snapshot cumulativo, sem
alterar os hashes dos outros arquivos, antes do DDL e da persistência.

A repetição terminou novamente com **16 failed**, pelas mesmas causas de catálogo
e stubs, com Ruff aprovado. Os hashes dos outros dezenove arquivos foram conferidos
antes da renovação. O snapshot cumulativo passou a **21 arquivos**, acrescentando
a integração HTTP, e foi verificado antes da implementação.

## Green observado

Checkpoint Red `8859f82`: testes, stubs e migração sem DDL. Os blobs desse commit
foram conferidos antes de relatar a cronologia. Nenhum teste foi editado no Green.

| Seleção focada                           | Resultado            |
| ---------------------------------------- | -------------------- |
| HTTP/roteador de conversa                | 68 passed            |
| Migração, persistência e integração HTTP | 28 passed            |
| Guard após implementação                 | 21 arquivos intactos |

Foram demonstrados os dois formatos de URL PostgreSQL, duas identidades, reabertura
com token rotacionado, conflito/replay, paginação incluindo mensagens internas,
concorrência entre conexões e entre aplicações. Um observador ASGI confere os
registros por outra conexão antes dos headers. Triggers reais provocam falhas na
inserção e no commit; mensagem, contador e chave são revertidos, e a mesma chave
pode ser reenviada após remover a falha. As fixtures de isolamento não mudaram.

## Coleta de cobertura

O Memtrace também recebeu a lista dos quatro arquivos de configuração afetados;
não mapeou símbolos nesses arquivos e indicou relinking em andamento. As fontes
e consumidores dos scripts foram conferidos diretamente. A configuração acrescenta
scripts/migrações e o suporte a subprocessos já presente no coverage.py instalado.
As duas medições originais continuam com verificações explícitas de 85%, além dos
gates dos relatórios ampliados. Essa alteração é declarativa, sem alegação de TDD
retroativo para os scripts e migrações existentes.

## Verificação consolidada

O Green da implementação está em `836d0f0`. O `pnpm check` final terminou com
exit 0: guard, lint, formato, tipos, unidades e build. A suíte da API aprovou
154 testes: cobertura de 91,47% na API e 89,57% incluindo scripts. A web aprovou
um teste com 100%. A integração aprovou 133 testes, com 100% na persistência e
96,81% incluindo migrações. Os gates originais de 85% foram conferidos separadamente.

A coleta ampliada mediu o guard (85,27%), migrações `0002` a `0004` (100%),
migração inicial (90%) e ambiente Alembic (77,27%). Oito classes no XML unitário,
seis na integração e uma fonte no LCOV tiveram caminhos relativos resolvidos.
Nenhum percentual foi inferido a partir de testes aprovados.

Uma execução anterior de `pnpm check` perdeu a continuação do terminal antes de
entregar resultado final; ela não foi declarada aprovada. A conferência final,
após a atualização documental e da coleta, concluiu com exit 0 e registro local.
Os dois avisos de depreciação do TestClient continuam visíveis. O percurso web não
mudou; E2E local não foi repetido pelo implementador, e Chromium permanece obrigatório
no CI. Nenhuma dependência, lockfile ou fixture de isolamento foi alterada.

A conferência posterior do Memtrace encontrou o roteador de identidade com
45 dependências e risco HIGH, incluindo testes novos e herdados. `CoreRepository`
retornou sete dependências e risco MEDIUM. Os arquivos indicados foram exercitados
nas suítes completas. Contagens refletem o índice naquele instante, sem provar
inexistência de outros consumidores. As consultas e seus resultados foram preservados
localmente, fora do Git.

Hashes SHA-256 dos cinco testes novos, preservados desde o snapshot anterior ao Green:

```text
6fb2769ba94841c3cebb573341e81aabb15241e3531d8e59901d1580afe7498f  services/api/tests/test_conversation_http.py
1d8fd0189c0e4be5f56089e90438f8250b8488eaaca6240883cdf6996f1a9d30  services/api/tests/test_conversation_routes.py
1cef4f813895878bd674e0e9a150b6ce2d98f3ebee49de66132f9adfd503c0dc  tests/integration/test_conversation_api.py
e1f5a588a39abf42918fc39052d91d070cecfee5c24f29837868f3bffc165e23  tests/integration/test_message_submission_migration.py
883bc207dc7e725f370dbbfce35a575adbd6f47f907b8a9fe20a99fa6c5e1177  tests/integration/test_message_submissions.py
```

O guard final contém 21 arquivos intactos. O review independente e o CI são
vinculados ao SHA na PR. A revisão formal de formatação não substitui o parecer
integral. Mudança material posterior exige nova revisão. E00.5 e E01 não começaram.

## Correção declarativa dos caminhos de cobertura

No primeiro CI da PR #8, SHA `8cca7d1`, qualidade Linux/Windows, integração e
Chromium passaram. O Sonar leu os XML, mas ignorou sete arquivos da API e a
persistência: as raízes mistas do XML fizeram o parser procurar os caminhos completos
sob `scripts` e `migrations`. A cobertura de código novo apareceu como 12,5%, e o
gate reprovou corretamente. Esse CI não é apresentado como entrega aprovada.

A configuração agora distingue `source_pkgs` de `source_dirs`. O coverage.py
7.16.1 mantém as mesmas fontes medidas e gera nomes relativos completos a partir
da raiz do repositório. Na prova com os dados já coletados, cada linha, branch e
contador de execução permaneceu idêntico nos oito arquivos unitários e seis de
integração. Não há edição dos XML após sua geração nem alteração de denominadores.
As fontes e os dois gates anteriores de 85% permanecem iguais.

O Memtrace recebeu novamente os dois arquivos de configuração antes desse ajuste.
O ajuste foi isolado em worktree próprio para preservar o checkpoint em revisão
e a atualização documental concorrente no workspace principal. A leitura local de
arquivos confirmou o escopo; o índice de configuração não contém símbolos de código.
Os resultados após a correção e o review do SHA final ficam registrados na PR.

Após a correção declarativa, `pnpm check` e `pnpm test:integration` foram repetidos
no worktree isolado e terminaram com exit 0. Permaneceram 154 testes de API, um
web e 133 de integração, com os mesmos percentuais e 21 hashes intactos. A coleta
nova confirmou raízes únicas e nomes completos relativos ao repositório; o código
da aplicação e os testes não mudaram em relação a `8cca7d1`.
