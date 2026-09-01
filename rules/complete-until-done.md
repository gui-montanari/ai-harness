---
description: Não encerrar o turno com trabalho aberto; provar que a solicitação ficou pronta.
alwaysApply: true
---

# Completar até o fim

Regra global. Vale em todo projeto.

Nunca encerre o turno com trabalho da solicitação ainda em aberto.
Não ofereça “continuar depois” o que ainda dá para fazer agora.
Não declare pronto por inferência, confiança ou screenshot de render.

Exceção única: o usuário pediu explicitamente um recorte, um plano, ou para parar.

## Antes de qualquer “pronto”

1. Releia o pedido original, ponto a ponto.
2. Confira a lista de tarefas: nada da solicitação pode ficar `pending` ou `in_progress`.
3. Prove que ficou correto e funciona de verdade nesta sessão.
4. Se algo estiver bloqueado, diga o bloqueio e o que falta — não transforme o restante em próximo passo opcional.

“Pronto” só vale quando todos os itens explícitos estão feitos, verificados e sem ponta solta: TODO, placeholder, teste pulado, documento divergente, subagente cujo resultado não foi incorporado.

## Conferência obrigatória

Toda atividade concluída precisa desta lista na resposta final, com `[x]` só no que foi de fato feito nesta sessão. Item não aplicável vira `[x]` com uma frase do porquê; item aplicável não feito impede declarar pronto.

- [ ] Pedido original relido; cada item explícito está feito
- [ ] Nenhum todo da solicitação ficou `pending` ou `in_progress`
- [ ] Testes, gates ou comando de verificação pertinentes rodaram nesta sessão; saída lida; exit 0
- [ ] Caminho feliz exercitado de ponta a ponta — não só compilou ou renderizou
- [ ] Estados de erro, vazio e borda verificados quando a mudança os toca
- [ ] Sem TODO, placeholder, teste pulado, documento divergente ou resultado de subagente não incorporado

## Teste como usuário (quando for possível)

Se a mudança for visível ou usável por uma pessoa — UI, fluxo no browser, formulário, navegação, tela, widget, página, estado da aplicação — o teste no browser da sessão é obrigatório, não opcional. Use as ferramentas de browser disponíveis (`chrome-devtools` ou `cursor-ide-browser`) e aja como o usuário: abrir, clicar, digitar, submeter, navegar.

- [ ] Fluxo exercitado no browser como um usuário faria, ponta a ponta
- [ ] Comportamento observado ficou green: o que deveria acontecer aconteceu
- [ ] Console sem erro bloqueante; rede das chamadas críticas no status esperado
- [ ] Rotas e páginas que compartilham o estado/componente continuam consistentes
- [ ] Desktop e mobile quando layout ou estilo mudou

Screenshot de render não conta. Confirme comportamento, não aparência.
Se o teste encontrar problema: corrija e reteste no browser antes de encerrar.
Se as ferramentas de browser não estiverem disponíveis, use o substituto mais próximo (testes, curl, script de render) e declare o que não pôde verificar.

Para mudança só de backend/CLI/docs sem superfície de usuário, o checkbox de browser é `[x]` com “não aplicável: …” e os testes/gates da seção anterior continuam obrigatórios.
