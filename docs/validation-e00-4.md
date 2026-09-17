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
