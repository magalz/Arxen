# Validação inicial da infraestrutura

Registro de 16/09/2026. [PR #1](https://github.com/magalz/Arxen/pull/1), branch
`chore/ci-tdd`, commit inicial `250d0760fbab0dbae199f0b5de6cfde1bfe41de7`.

## Execução local

No Windows, `pnpm check` terminou com código 0: ESLint, Ruff, Prettier,
TypeScript, mypy, um teste web, dois testes da API e build. `pnpm test:e2e`
terminou com código 0 e dois testes aprovados no Chromium, incluindo a API por
HTTP. Os ciclos Red/Green estão em [validation-web.md](validation-web.md) e
[validation-python.md](validation-python.md).

Docker não está instalado neste ambiente local. Por isso, não foi executado
`pnpm infra:up` nem demonstrado o funcionamento do Compose no Windows.
A integração foi executada no runner Linux, conforme os resultados abaixo.

## Execução da PR no GitHub

A [execução 35144457998](https://github.com/magalz/Arxen/actions/runs/35144457998)
foi disparada por `pull_request`. O checkout testou o merge sintético
`1750f76aaa92c9d1b1fd88d4a38c16d422c51f8a`, combinando o commit inicial da PR
com a base `3702ac2e2744e8d2902e45beb0b154959f3e51c9`.

| Check                               | Resultado observado                                                                                           |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Quality & unit (ubuntu-24.04)       | Aprovado: ferramentas, formato, tipos, unidades, cobertura e build. Actionlint e validação Compose aprovados. |
| Quality & unit (windows-2025)       | Status success reportado, mas evidência inválida: logs sem saída dos comandos pnpm e JUnit vazio.             |
| Integration (PostgreSQL + pgvector) | Aprovado: seis cenários contra o banco real, sem skips.                                                       |
| E2E (Chromium)                      | Aprovado: instalação do navegador, testes e upload do relatório.                                              |
| CI Gate                             | Status success reportado; insuficiente para concluir a validação, devido ao problema observado no Windows.    |

O log do job de integração `104956845765` registra `collected 6 items` e
`6 passed in 0.16s`. O container usado foi
`pgvector/pgvector:0.8.6-pg17-bookworm`. Os testes cobrem texto parametrizado,
Unicode, vetores e rollback com dados sintéticos.

Os uploads concluíram, mas o artefato Windows `10466339016` tinha apenas 168 bytes.
A inspeção do ZIP encontrou somente `test-results/web/junit.xml`, com zero bytes.
Essa execução não comprova testes nem cobertura no runner Windows, apesar do
status success. Os resultados locais Windows continuam válidos, pois os comandos
e seus relatórios foram observados. A retenção dos artefatos é de cinco dias.

## Correção da validação Windows

O setup foi alterado de `pnpm/action-setup` para a Action oficial `pnpm/setup`
v2.0.1, fixada no commit `4700d737c3d7a2e7199f3d42a920f0bf7f34e411`.
Ela instala diretamente o executável nativo do pnpm. A versão continua 12.3.4,
com Node preparado separadamente. O mecanismo interno da execução sem evidências
não foi isolado; a troca será avaliada pelos logs e artefatos da nova execução.

O setup exige uma saída de versão válida, e cada job de qualidade passa a exigir
JUnit web/API, LCOV web, cobertura XML da API e HTML do build não vazios antes de
concluir. Isso cobre o caso de regressão observado: um JUnit com zero bytes
reprova a verificação `test -s` mesmo quando um comando anterior retorna sucesso.
Os resultados da revalidação devem acompanhar o último commit na PR #1.

O push temporário na branch de preparação também foi usado durante o bootstrap.
Após a primeira validação, o gatilho dessa branch foi removido: novos commits na
PR disparam uma única execução por `pull_request`; pushes em `main`, disparo
manual e `merge_group` continuam configurados.

## Proteção e limites

O JSON em `.github/rulesets/main.json` exige PR, conversas resolvidas, base
atualizada e `CI Gate` do GitHub Actions (`integration_id: 15368`, observado
nos checks reais). Também bloqueia force push e exclusão, sem atores de bypass.
O fluxo solo começa com zero aprovações obrigatórias de outros revisores.

**O ruleset ainda não foi ativado.** A tentativa pela ferramenta de terminal
foi bloqueada antes de uma resposta do GitHub; a listagem posterior de rulesets
retornou `[]`. O [guia de proteção](../.github/rulesets/README.md) contém a
configuração e os comandos de aplicação e conferência.

Esta página preserva a evidência da execução inicial identificada acima.
Alterações posteriores devem ser avaliadas pelos checks do último commit da PR.
Cobertura de 100% sobre o código mínimo medido não representa funcionalidades
jurídicas implementadas. O limiar obrigatório configurado é 85%.
