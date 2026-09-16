# Arxen

Assistente jurídico para advogados no Brasil.

Este repositório contém a infraestrutura inicial de desenvolvimento: web mínima
em React/TypeScript, API FastAPI, testes de unidade, integração PostgreSQL/pgvector
e smoke de navegador. A E00.1 adiciona configuração tipada e migrações Alembic;
as demais subetapas da fundação funcional e as funcionalidades jurídicas seguem
como próximas entregas.

Todo comportamento será desenvolvido com TDD: teste significativo, falha esperada,
implementação mínima e refatoração com os testes passando.

## Preparação

Use Node.js **26.8.1**, pnpm **12.3.4**, uv **0.12.10** e Python **3.13.12**.
Na raiz do repositório:

```text
pnpm bootstrap
pnpm check
pnpm test:e2e:install
pnpm test:e2e
```

`bootstrap` instala as dependências fixadas nos lockfiles. Python permanece na
`.venv` local, gerida por uv. Todos os comandos do projeto partem do pnpm.

Para desenvolver, execute `pnpm dev:web` e `pnpm dev:api` em terminais separados.
A web abre em `http://127.0.0.1:5173` e a API responde em
`http://127.0.0.1:8000/healthz`. O smoke de navegador usa as portas 4173 e 8000
e exige que estejam livres.

## Testes e contribuições

`pnpm check` verifica lint, formatação, tipos, unidades com cobertura mínima de 85%
e build. `pnpm test:web:watch` mantém o ciclo de feedback da web aberto.
`pnpm test:integration` exige um banco de teste PostgreSQL com pgvector e
`TEST_DATABASE_URL`; consulte [infra/README.md](infra/README.md) para o Compose local.

O CI de PRs executa qualidade e unidades em Linux/Windows, integração real e
Playwright/Chromium. O check **CI Gate** só aprova quando todos esses jobs passam.
A definição da proteção de `main` está em
[.github/rulesets](.github/rulesets/README.md); sua aplicação no GitHub é uma
configuração separada do arquivo versionado.

Leia [CONTRIBUTING.md](CONTRIBUTING.md), [AGENTS.md](AGENTS.md) e
[docs/testing.md](docs/testing.md) antes de implementar. Registre na PR os
resultados reais de Red/Green/Refactor ou da validação declarativa pertinente.
Use exclusivamente fixtures sintéticas. Dados de casos, documentos privados,
segredos e saídas de execução não pertencem ao repositório.

Os critérios de seleção de ferramentas, congelamento dos testes após Red válido e
review em contexto novo estão em
[docs/engineering-guardrails.md](docs/engineering-guardrails.md).

O objetivo de desenvolvimento atual e a decomposição da fundação E00 estão em
[docs/e00-foundation-plan.md](docs/e00-foundation-plan.md).

A [validação inicial](docs/validation-ci.md) registra os resultados locais e do
GitHub Actions, o follow-up local com Podman e a ativação da proteção de `main`.
