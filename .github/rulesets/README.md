# Proteção de main

`main.json` é a configuração declarativa desejada. **Versionar esse arquivo não
ativa proteção no GitHub.** A aplicação e a leitura de confirmação precisam ser
realizadas por quem administra o repositório.

A regra exige PR para `refs/heads/main`, conversas resolvidas e o status
`CI Gate` aprovado com a base atualizada. Bloqueia exclusão e force push, e a lista
`bypass_actors` é vazia. A aprovação por outros revisores começa em **zero**, para
permitir o fluxo do dono solo. Não exige autoaprovação, revisão de CODEOWNERS ou
aprovação do último push por uma segunda pessoa.

O contexto requerido tem o nome exato `CI Gate`, definido no workflow `CI`. O JSON
vincula esse contexto ao GitHub Actions com `integration_id: 15368`, confirmado
nos check runs reais do commit `250d0760fbab0dbae199f0b5de6cfde1bfe41de7` em
16/09/2026. Assim, a regra preparada exige tanto o nome quanto a origem do check.

**Estado confirmado em 16/09/2026:** o ruleset foi aplicado ao repositório com ID
`23565202` e `enforcement: active`. A leitura posterior de
`GET /repos/magalz/Arxen/rules/branches/main` confirmou PR obrigatório, conversas
resolvidas, `CI Gate` estrito vinculado ao GitHub Actions, bloqueio de exclusão e
force push e ausência de bypass. A branch `main` passou a retornar
`protected: true`.

Os resultados e a correção identificada na execução inicial estão na
[validação do CI](../../docs/validation-ci.md). Antes de alterar este ruleset,
confira os checks e as evidências do último commit da PR, liste as regras atuais e
atualize o ruleset existente pelo ID em vez de criar uma duplicata.

Para um administrador, a
[API oficial de rulesets](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset)
aceita o JSON com permissão de administração de escrita. O comando de criação,
executado uma única vez após verificar as regras existentes, é:

```text
gh api --method POST repos/magalz/Arxen/rulesets --input .github/rulesets/main.json
```

Não repita a criação para recuperar uma resposta perdida: liste as regras e
consulte o ID existente. Uma atualização usa esse ID e o endpoint de atualização,
evitando rulesets duplicados. Consultas:

```text
gh api repos/magalz/Arxen/rulesets
gh api repos/magalz/Arxen/rules/branches/main
```

Registre o ID retornado, `enforcement`, alvo, regras, origem esperada do check e
ausência de bypass na confirmação do servidor. Se uma atualização futura falhar,
relate o erro específico e mantenha a regra existente; não crie uma exceção de
bypass para contornar o problema.

O workflow já atende ao evento `merge_group`, mas este ruleset não obriga nem
ativa uma fila de merge. Mudanças no nome do gate ou na política de proteção
precisam atualizar workflow, JSON e documentação juntos.
