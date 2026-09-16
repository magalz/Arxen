# Desenvolvimento do Arxen

- Usar pnpm como ponto de entrada para instalar, preparar, executar e testar o
  projeto. Não usar npm/yarn. Python usa uv e a `.venv` local, via scripts pnpm.
- Aplicar TDD a todo comportamento: escrever o teste, observar a falha esperada,
  implementar o mínimo e refatorar. Registrar comandos e resultados. Falha de
  importação, dependência ou infraestrutura não demonstra a falha do comportamento.
  Configuração declarativa exige validação apropriada, não testes artificiais.
- Depois de observar um Red válido, o agente que implementa **não pode editar,
  apagar, renomear, pular ou enfraquecer esse teste para acomodar o código** antes
  do Green. Registrar o snapshot com `pnpm tdd:guard:record -- <teste...>` e manter
  `pnpm tdd:guard:verify` aprovado. Se o teste estiver errado ou a spec mudar,
  interromper a implementação: a alteração do teste exige justificativa explícita,
  revisão separada da correção do teste, novo Red válido e novo snapshot antes de
  retomar a implementação. Não usar `tdd:guard:clear` para contornar uma violação.
- Ler implementação e consumidores antes de editar; preservar alterações alheias.
- Testar unidade, integração e ponta a ponta nas camadas pertinentes. Corrigir
  bugs com testes de regressão. Não usar testes vazios, `.only`, skips injustificados
  ou flags que façam ausência de testes parecer sucesso.
- Usar exclusivamente fixtures sintéticas. Nunca versionar `references-01`,
  `pacote-teste-01`, documentos reais, segredos, `.env` ou saídas de execução.
- A stack de partida é React/TypeScript, FastAPI/Python e PostgreSQL/pgvector.
  A infraestrutura inicial não conclui a E00 nem autoriza uso com dados reais.
- Manter instruções, evidências de validação e estado da implementação atualizados.
- Revisar entregas em um contexto novo, separado do contexto que implementou a
  mudança. O revisor deve partir da spec/objetivo, diff e evidências finais, sem
  depender da conversa de implementação; corrigir achados bloqueantes antes de
  considerar a etapa concluída.
- Executar `pnpm check` antes de entregar alterações; executar integração e E2E
  quando pertinentes. Não alegar execução de verificações que não foram realizadas.
- Novas dependências devem ter versão fixada e lockfile atualizado. Não instalar
  dependências do projeto globalmente. Os checks de PR devem permanecer sem
  segredos de produção ou chamadas pagas a modelos.
- Ao escolher ferramentas ou dependências, preferir soluções open source, sem custo
  de licença, maduras, mantidas e compatíveis com a stack. Entre alternativas que
  atendem ao requisito, escolher a de menor complexidade operacional e menor número
  de dependências. Produto proprietário ou pago só entra quando houver benefício
  material não atendido pela alternativa aberta ou decisão explícita do projeto.
