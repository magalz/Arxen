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

**Estado confirmado em 16/09/2026:** configuração pronta, proteção ainda não
ativada. A tentativa de criação pela ferramenta de terminal foi bloqueada antes
de retornar uma resposta do GitHub, com a mensagem de que não foi possível
determinar o status de segurança da solicitação. A consulta posterior a
`GET /repos/magalz/Arxen/rulesets` retornou `[]`. Isso não demonstra falta de
permissão da conta ou limitação do plano; a ativação administrativa segue pendente.

Antes da ativação, publique o workflow e confira uma execução completa na branch
de preparação. Em um repositório vazio, a criação inicial de `main` precisa estar
resolvida antes de exigir o check nela. O arquivo usa `enforcement: active`, mas
essa propriedade só tem efeito após importação/aplicação aceita pelo servidor.
Os resultados e a correção identificada na execução inicial estão na
[validação do CI](../../docs/validation-ci.md). Confira também os checks e as
evidências do último commit da PR antes da ativação.

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
ausência de bypass na confirmação do servidor. Até essa confirmação, descreva a
proteção como **configurada no arquivo, aplicação não demonstrada**. Se a conta ou
credencial não permitir a aplicação, relate o erro específico e mantenha o arquivo
pronto; não crie uma exceção de bypass ou declare a proteção ativa.

O workflow já atende ao evento `merge_group`, mas este ruleset não obriga nem
ativa uma fila de merge. Mudanças no nome do gate ou na política de proteção
precisam atualizar workflow, JSON e documentação juntos.
