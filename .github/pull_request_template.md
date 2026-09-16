## Mudança

Problema, comportamento esperado e limite desta entrega.

## Evidência

Para comportamento, inclua comandos e trechos curtos dos resultados reais:

- **Red:** teste novo ou de regressão, assertion que falhou e motivo esperado.
- **Green:** mesmo teste aprovado após a implementação mínima.
- **Refactor:** ajuste realizado e verificações finais aprovadas.
- **TDD guard:** teste(s) congelado(s) após o Red e `tdd:guard:verify` aprovado.

Para configuração/documentação, indique "configuração" e a validação executada;
não fabrique uma etapa Red. Registre também verificações não executadas e o motivo.

## Revisão

- [ ] Usei somente dados sintéticos; não incluí acervo real, specs privadas ou segredos.
- [ ] Executei `pnpm check` e integração/E2E quando pertinentes; anexei os resultados.
- [ ] Não alterei teste Red para adaptá-lo à implementação; qualquer correção de teste foi tratada como novo ciclo explicitamente revisado.
- [ ] A documentação descreve o que foi demonstrado e as limitações restantes.

### Review em contexto novo

- **Contexto/revisor:**
- **Commit ou diff revisado:**
- **Escopo do review:**
- **Resultado:** aprovado / aprovado com observações / bloqueado
- **Achados bloqueantes e resolução:**

- [ ] O review foi feito em contexto separado daquele que implementou a mudança.
- [ ] O parecer cobre o commit/diff final ou uma nova revisão foi executada após mudanças materiais.
- [ ] Todos os achados bloqueantes foram resolvidos e revalidados.
