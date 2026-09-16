# Evidência da preparação web

Execução em 16/09/2026, no Windows, com Node.js 26.8.1 e pnpm 12.3.4.

O comportamento mínimo desta etapa é identificar a aplicação e seu estado de
desenvolvimento. Não implementa funções jurídicas ou a jornada da E00.

## Red

Com `App` retornando `null`, o comando abaixo executou um teste e falhou:

```text
pnpm exec vitest run apps/web/src/App.test.tsx
```

A assertion não encontrou o heading acessível de nível 1 com nome `Arxen`:
`TestingLibraryElementError: Unable to find an accessible element with the role "heading" and name "Arxen"`.
O runner carregou e executou o teste; a falha foi a ausência do comportamento.

## Green

Foi adicionada somente a estrutura `main`, o heading `Arxen` e o texto
`Ambiente de desenvolvimento`. `pnpm test:web` passou com **1 teste** e cobertura
de **100%** das linhas, statements, funções e branches de `App.tsx`.
O bootstrap `main.tsx` é exercitado pelo smoke de navegador, não pelo teste unitário.

Não houve refatoração necessária nesta implementação mínima. A verificação
completa da infraestrutura deve acompanhar a PR e seu commit final.

## Compatibilidade das ferramentas

A instalação inicial identificou conflito entre TypeScript 7.0.2 e o intervalo
suportado pelo typescript-eslint 8.70.0. A dependência foi fixada em TypeScript
5.9.3 e o lockfile foi regenerado. `pnpm peers check` confirmou ausência de
conflitos após o ajuste.

As métricas desta página se limitam ao skeleton testado. Elas não representam
cobertura de funcionalidades que ainda não existem.
