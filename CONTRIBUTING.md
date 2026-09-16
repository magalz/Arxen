# Contribuir com o Arxen

Leia [AGENTS.md](AGENTS.md) antes de alterar o repositório e
[docs/testing.md](docs/testing.md) para o fluxo de testes. A E00.1 está integrada;
a entrega atual é a E00.2, descrita no
[plano da fundação](docs/e00-foundation-plan.md) e nos
[contratos centrais](docs/e00-2-contracts.md). E00.3 ainda não começou.

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

Assim que o Red for válido, congele os testes que o demonstraram:

```text
pnpm tdd:guard:record -- services/api/tests/test_exemplo.py
pnpm tdd:guard:verify
```

O agente implementador não modifica esses testes até obter Green. `pnpm check`
executa `tdd:guard:verify` automaticamente quando existe snapshot ativo em
`.artifacts/tdd-guard.json`. Se um teste tiver sido especificado incorretamente,
pare a implementação e trate a correção do teste como uma decisão separada: registre
o motivo, revise a mudança do teste, execute um novo Red e grave um novo snapshot.
Não enfraqueça assertion, remova caso, adicione skip ou limpe o guard para fazer a
implementação passar.

Abra um PR para `main`, descrevendo problema, resultado e evidência real de
Red/Green/Refactor ou de validação da configuração. Execute integração e E2E nas
camadas afetadas; o CI executa todas as camadas em cada PR. O ruleset ativo da
`main` exige `CI Gate` aprovado e conversas resolvidas antes do merge.

Antes de considerar uma entrega concluída, execute uma revisão técnica em um
**contexto novo**, separado de quem implementou. O revisor recebe o objetivo/spec,
o diff final e as evidências de teste e validação. Ele não deve depender da conversa
de implementação para justificar a aprovação. Para mudanças de banco, migrações ou
persistência, incluir revisão focada em PostgreSQL/esquema; para superfícies
sensíveis, acrescentar revisão de segurança. Achados bloqueantes devem ser
corrigidos e revalidados antes do fechamento da etapa.

Registre na PR a evidência desse review: identificação do contexto/revisor, commit
ou diff efetivamente revisado, escopo, resultado e resolução dos achados
bloqueantes. Se a implementação mudar materialmente depois do parecer, o trecho
alterado precisa de nova revisão em contexto novo antes do fechamento.

O autor solo precisa abrir PR, mas a configuração inicial exige **zero aprovações
humanas obrigatórias** no GitHub. Isso não dispensa o review técnico em contexto
novo descrito acima. Não configure hooks que impeçam commits de testes ainda em Red.
O PR destinado ao merge deve terminar aprovado pelos checks.

Preserve alterações alheias. Use somente fixtures sintéticas e provedores falsos
determinísticos; os testes não devem chamar APIs externas de modelos. Nunca
adicione acervo real, especificações privadas, dados pessoais, segredos, `.env` ou
saídas de execução ao repositório ou aos comentários do PR.

Fixe versões de novas dependências e atualize os lockfiles pelo pnpm/uv. Inclua
mudanças de configuração, instruções e evidências junto com a alteração que as
exige. Registre o que não foi executado e o motivo, sem declarar aprovação por
inferência.

Na seleção de ferramentas, a preferência do projeto é por alternativas open source
e sem custo de licença. Avalie maturidade, manutenção, compatibilidade, custo
operacional e quantidade de dependências; entre opções equivalentes, use a solução
mais simples. Dependência proprietária ou paga precisa de vantagem concreta que a
alternativa aberta não entregue ou de decisão explícita do projeto.

O plano operacional da fundação está em [docs/e00-foundation-plan.md](docs/e00-foundation-plan.md).
Os guardrails de engenharia estão em
[docs/engineering-guardrails.md](docs/engineering-guardrails.md).
