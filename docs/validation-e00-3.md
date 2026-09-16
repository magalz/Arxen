# Validação parcial da E00.3

Registro de 16/09/2026. Branch `feat/e00-3-synthetic-cases`, derivada de
`61924653f05f346ecf8978e99fd010e369e9b804`, merge da E00.2 pela PR #5.

## Escopo demonstrado

Configuração da identidade sintética e `GET /api/v1/me`, com opt-in explícito,
restrição a desenvolvimento/teste, token Bearer e identidade definida no servidor.
Ainda não há vínculo persistente entre caso e identidade, rotas HTTP de casos ou
nova migração. A E00.3 completa permanece em andamento.

## TDD

Comandos focados, antes e depois de cada implementação:

```text
pnpm python:run pytest services/api/tests/test_synthetic_identity_settings.py --no-cov -q --tb=short
pnpm python:run pytest services/api/tests/test_synthetic_identity_http.py --no-cov -q --tb=short
```

O Red da configuração terminou com **17 failed, 3 passed**: o carregador retornava
`None` para ativação válida e não recusava ambiente/valores indevidos. O snapshot
precedeu a implementação. O mesmo arquivo terminou com **20 passed**.

O Red HTTP terminou com **7 failed, 2 passed**: a rota ainda retornava 404 e a
factory ignorava a configuração sintética. Após congelar o arquivo, foram
implementadas a ativação na factory, a conferência do token e a rota. A execução
conjunta dos dois arquivos terminou com **29 passed**.

Os checkpoints são `3b36c91` (configuração) e `b84aa52` (HTTP). Os oito testes
congelados da E00.2 continuam no manifesto; os dois novos foram acrescentados
após seus Reds. Não houve limpeza do guard ou alteração de teste congelado.

Foram observados dois avisos de depreciação no TestClient instalado, relativos
à integração com httpx e ao alias de BlockingPortal do anyio. Eles não foram
suprimidos nem motivaram atualização incidental de dependências nesta etapa.

## Revisão independente pendente

As chamadas de coordenação de workers retornaram `WORKER_IDENTITY_LOST`, sem
executar operação de agentes. `update_plan` também recusou a atualização por
ausência de identidade exata do chat; isso não impediu leitura, Git ou execução.

Foi tentada uma consulta separada pelo Codex CLI já instalado (0.154.0), com
`--sandbox read-only --ephemeral`, sem overrides de modelo ou esforço. O processo
encerrou com código 1 por limite de uso, sem gerar o arquivo de parecer. Não houve
aprovação de escopo, correção de teste ou review final por esse caminho.

Antes de alterar a expectativa de revisão em `test_core_contracts.py`, deve ser
concluída a revisão separada descrita em [e00-3-synthetic-cases.md](e00-3-synthetic-cases.md).
Nenhuma migração nova foi aplicada e o teste original permanece intacto.

## Verificações consolidadas

Resultados locais observados:

| Verificação             | Resultado                                            |
| ----------------------- | ---------------------------------------------------- |
| `pnpm check`            | Exit 0; lint, formato, tipos, testes e build         |
| API dentro do check     | 45 passed; cobertura combinada de 97,44%             |
| Web dentro do check     | 1 passed; cobertura de 100%                          |
| `pnpm test:integration` | 87 passed; persistência Python com 100% de cobertura |
| `pnpm tdd:guard:verify` | 10 arquivos congelados intactos                      |
| `git diff --check`      | Exit 0                                               |

Os 87 testes de integração preservam as garantias da E00.2; eles não demonstram
o vínculo caso/identidade ainda pendente. O E2E local não foi repetido, pois o
percurso web e o contrato de `/healthz` permanecem iguais; Chromium continua
obrigatório no CI. Ambos os gates Python mantêm o limite de 85%.

SHA-256 dos dois arquivos novos, preservados desde seus Reds:

```text
d1eba624ef4846370ed0ecf5872f3e4ab5057ad4f8cbeba86ec8c127a7f2dcf1  services/api/tests/test_synthetic_identity_settings.py
655816c2d1a33300cb2f8f902fe8c10e6f9d254dc01acdc0cd2d625e94763a67  services/api/tests/test_synthetic_identity_http.py
```

O resultado do CI será vinculado ao SHA na PR deste slice. A PR permanece em
rascunho, pois a E00.3 e o review independente ainda não foram concluídos.
A E00.4 não começou.
