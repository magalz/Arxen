# SonarCloud: análise e cobertura do Arxen

O projeto `magalz_Arxen`, na organização `magalz`, recebe a análise do job
`SonarCloud` do workflow `CI`. A configuração versionada está em
`sonar-project.properties`.

## Por que usar o CI

A análise automática do SonarCloud não recebe os relatórios de cobertura gerados
pelos testes do GitHub Actions. Um resultado de 0% nessa modalidade não demonstra
ausência de testes, e um Quality Gate aprovado não comprova importação de cobertura.
O scanner do CI lê os arquivos produzidos pela própria execução dos testes.

Referência: [cobertura Python e análise pelo CI](https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/test-coverage/python-test-coverage/).

## Relatórios e escopo

| Relatório                           | Origem                              | Importação                          |
| ----------------------------------- | ----------------------------------- | ----------------------------------- |
| `coverage/api/coverage.xml`         | Unidades da API e scripts no Linux  | `sonar.python.coverage.reportPaths` |
| `coverage/integration/coverage.xml` | Persistência e migrações PostgreSQL | `sonar.python.coverage.reportPaths` |
| `coverage/web/lcov.info`            | Vitest no runner Linux              | `sonar.javascript.lcov.reportPaths` |

O job depende de qualidade/unidades e integração. Os dois downloads usam nomes
exatos de artefatos da mesma execução do workflow; não buscam relatórios de outra
branch, execução ou PR. O checkout mantém o histórico Git completo. A configuração
`relative_files` do coverage.py evita caminhos absolutos específicos do runner
ao transportar os relatórios para o job de análise.

Fontes analisadas: aplicação web, API, scripts operacionais, migrações,
infraestrutura e workflows. Testes da web, API, integração e E2E são classificados
como testes, sem duplicar sua classificação como código de aplicação. Saídas de
execução e dependências permanecem fora dessas raízes e ignoradas pelo Git.

Não há nova exclusão de cobertura para melhorar percentuais. O escopo da análise
estática é maior que o denominador das unidades da API. Scripts e migrações agora
recebem medição das execuções reais, inclusive em subprocessos. O bootstrap web
ainda pode aparecer sem cobertura importada. Isso deve ser tratado como lacuna de
instrumentação/cobertura, sem inventar medidas a partir de testes aprovados.
O percentual global do SonarCloud não precisa ser
igual ao percentual agregado de `pnpm test:api` ou de `pnpm test:web`.

Os dois gates Python de 85% e os limiares web de 85% permanecem inalterados.
`persistence.py` continua medido na integração real. Há verificações adicionais dos
escopos originais da API e da persistência para que as novas fontes não mascarem
seus resultados. O guard segue cumulativo; a mudança de instrumentação não altera
testes. Não somar percentuais de relatórios.

## Instrumentação após o merge da configuração

O CI de `main` em `81a26c8` importou os dois XML e o LCOV, mas o Quality Gate
reprovou: cobertura de código novo 58,4%, exigência de 80%. O relatório por arquivo
mostrou o script do guard e as migrações em 0%, apesar de suas execuções nos testes.
A E00.4 inclui essas fontes na coleta e habilita `patch = subprocess` no coverage.py
7.16.1 já instalado. Não há alteração de versões, testes ou exclusões de código.

O pytest-cov 7 delega a coleta de subprocessos a essa opção do coverage.py.
O suporte gera arquivos paralelos e o plugin combina os dados da execução antes
de produzir os relatórios. As verificações explícitas de 85% dos escopos originais
permanecem nos comandos pnpm, além do limiar dos relatórios ampliados.
Referências: [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html)
e [coverage.py](https://coverage.readthedocs.io/en/latest/config.html#run-patch).

## Credencial e ativação

Para ativar a análise no projeto existente:

1. Criar no SonarCloud uma credencial de análise com os menores privilégios
   disponíveis para este projeto e registrar sua expiração para rotação.
2. Salvar o valor como secret de Actions `SONAR_TOKEN` em `magalz/Arxen`.
   Não colocar o token em variáveis públicas, arquivos versionados ou logs.
3. Em **Administration > Analysis method** do projeto `magalz_Arxen`, desligar
   **Automatic analysis** antes da primeira execução autenticada do scanner.
4. Executar a PR e conferir os logs de importação dos dois XML e do LCOV, a
   revisão analisada, as medidas por arquivo e o Quality Gate no SonarCloud.
5. Após integrar, conferir também a análise de `main` disparada pelo push.

Referência: [action oficial do SonarQube](https://github.com/SonarSource/sonarqube-scan-action).

A action do scanner é fixada em `v8.2.1`, SHA
`22918119ff8e1ca75a623e15c8296b6ea4fbe28f`; o download de artefatos usa `v8.0.1`,
SHA `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c`. Os dois pins foram conferidos
contra as tags dos repositórios oficiais. Não há dependência nova na aplicação
nem alteração de lockfile.

## Gates e eventos

Em PRs do próprio repositório, push e disparos manuais, o job exige os três
relatórios não vazios e `SONAR_TOKEN`. Ausência de credencial falha explicitamente.
O scanner aguarda o Quality Gate por até 300 segundos. `CI Gate` exige também o
sucesso desse job, além de qualidade, integração e Chromium.

PRs de forks e do Dependabot não recebem essa credencial. Nesses eventos, e em
`merge_group`, somente o job Sonar é dispensado por condição explícita. O gate
confere que ele ficou `skipped`, enquanto qualidade, integração e Chromium
continuam obrigatórios. Para analisar uma contribuição externa, um mantenedor
deve revisar o código antes de levá-lo a uma branch controlada do repositório.
Não usar `pull_request_target` para executar código externo com segredos.

Em fila de merge, o Sonar permanece associado à PR original; a execução da fila
mantém os testes obrigatórios do commit de integração. A ausência de análise
Sonar nesses eventos está explícita e não deve ser descrita como aprovação Sonar.

## Validação da configuração

Esta alteração é declarativa. Não há alegação de novo ciclo Red/Green.
As verificações locais incluem `pnpm check`, `pnpm test:integration`, guard,
formato, validação do workflow e conferência dos caminhos presentes nos relatórios.
Os resultados de ativação remota, review independente e CI são registrados na PR
com o SHA correspondente; a presença destes arquivos não comprova a configuração
do secret ou a desativação da análise automática no serviço.

Validação local da configuração, a partir de `main` integrado pela PR #6:

| Verificação             | Resultado observado                               |
| ----------------------- | ------------------------------------------------- |
| `pnpm check`            | Exit 0; lint, formato, tipos, testes e build      |
| API                     | 86 passed; cobertura agregada 89,52%              |
| Web                     | 1 passed; cobertura 100%                          |
| `pnpm test:integration` | 105 passed; persistência 100%                     |
| `pnpm tdd:guard:verify` | 16 arquivos intactos                              |
| actionlint 1.7.12       | Exit 0; binário oficial com SHA-256 conferido     |
| XML Python e LCOV       | Caminhos relativos, todos resolvidos no workspace |

Foram conferidas cinco classes no XML de unidades, uma no XML de persistência e
uma fonte no LCOV. Os avisos de depreciação do TestClient continuam visíveis.
O percurso web não mudou; Chromium permanece obrigatório no CI. Estes resultados
não substituem a conferência da primeira análise autenticada no SonarCloud.
