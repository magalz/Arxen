# Desenvolvimento do Arxen

- Usar pnpm como ponto de entrada para instalar, preparar, executar e testar o
  projeto. Não usar npm/yarn. Python usa uv e a `.venv` local, via scripts pnpm.
- Aplicar TDD a todo comportamento: escrever o teste, observar a falha esperada,
  implementar o mínimo e refatorar. Registrar comandos e resultados. Falha de
  importação, dependência ou infraestrutura não demonstra a falha do comportamento.
  Configuração declarativa exige validação apropriada, não testes artificiais.
- Ler implementação e consumidores antes de editar; preservar alterações alheias.
- Testar unidade, integração e ponta a ponta nas camadas pertinentes. Corrigir
  bugs com testes de regressão. Não usar testes vazios, `.only`, skips injustificados
  ou flags que façam ausência de testes parecer sucesso.
- Usar exclusivamente fixtures sintéticas. Nunca versionar `references-01`,
  `pacote-teste-01`, documentos reais, segredos, `.env` ou saídas de execução.
- A stack de partida é React/TypeScript, FastAPI/Python e PostgreSQL/pgvector.
  A infraestrutura inicial não conclui a E00 nem autoriza uso com dados reais.
- Manter instruções, evidências de validação e estado da implementação atualizados.
- Executar `pnpm check` antes de entregar alterações; executar integração e E2E
  quando pertinentes. Não alegar execução de verificações que não foram realizadas.
- Novas dependências devem ter versão fixada e lockfile atualizado. Não instalar
  dependências do projeto globalmente. Os checks de PR devem permanecer sem
  segredos de produção ou chamadas pagas a modelos.
