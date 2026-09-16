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
exige esse contexto por nome; não contém um `integration_id` inventado. Quando
aplicar a regra, é possível vinculá-lo à integração GitHub Actions após confirmar
o ID da aplicação nos check runs reais do repositório. Esse vínculo adicional
precisa ser refletido no JSON se adotado.

Antes da ativação, publique o workflow e confira uma execução completa na branch
de preparação. Em um repositório vazio, a criação inicial de `main` precisa estar
resolvida antes de exigir o check nela. O arquivo usa `enforcement: active`, mas
essa propriedade só tem efeito após importação/aplicação aceita pelo servidor.

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
