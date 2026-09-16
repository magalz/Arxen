# Contribuir com o Arxen

Leia [AGENTS.md](AGENTS.md) antes de alterar o repositório e
[docs/testing.md](docs/testing.md) para o fluxo de testes. A entrega atual prepara
as ferramentas e seus smokes. Ela não implementa casos, autenticação ou o alpha.

Use Node.js **26.8.1**, pnpm **12.3.4**, uv **0.12.10** e Python **3.13.12**.
pnpm é a entrada para o trabalho no projeto; uv mantém Python e dependências na
`.venv` local. Não instale dependências do projeto globalmente.

Com as ferramentas disponíveis no terminal, execute na raiz:

```text
pnpm install --frozen-lockfile
pnpm python:sync
pnpm check
```

Antes de implementar comportamento, escreva o teste e observe a assertion que
falha pelo motivo esperado. Implemente o mínimo, execute o mesmo teste e refatore
com a suíte aprovada. Para corrigir um bug, comece pelo teste de regressão.
Configurações declarativas e documentação recebem validação apropriada.

Abra um PR para `main`, descrevendo problema, resultado e evidência real de
Red/Green/Refactor ou de validação da configuração. Execute integração e E2E nas
camadas afetadas; o CI executa todas as camadas em cada PR. O merge depende de
`CI Gate` e das conversas resolvidas quando o ruleset estiver aplicado.

O autor solo precisa abrir PR, mas a configuração inicial exige **zero aprovações**
de outros revisores. Não configure hooks que impeçam commits de testes ainda em
Red. O PR destinado ao merge deve terminar aprovado pelos checks.

Preserve alterações alheias. Use somente fixtures sintéticas e provedores falsos
determinísticos; os testes não devem chamar APIs externas de modelos. Nunca
adicione acervo real, especificações privadas, dados pessoais, segredos, `.env` ou
saídas de execução ao repositório ou aos comentários do PR.

Fixe versões de novas dependências e atualize os lockfiles pelo pnpm/uv. Inclua
mudanças de configuração, instruções e evidências junto com a alteração que as
exige. Registre o que não foi executado e o motivo, sem declarar aprovação por
inferência.
