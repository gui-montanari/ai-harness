---
name: frontend-login
description: >
  Use when creating or restyling a sign-in, sign-up, password reset, or
  authentication form: layout, inputs, labels, errors, forgot-password,
  or when the user mentions login page, form-card, or /frontend-login.
---

# Login e formulários de acesso

Skill `auth` no servidor. Esta skill é **só a superfície**. `ui/` não faz `fetch`; a página chama `lib/api.ts`.

**REQUIRED SUB-SKILL:** `frontend-surfaces` (tokens) e `auth` (sessão interna ≠ pública).

## Layout

Duas colunas no `page-main` / `site-shell`:

```
[ ← voltar à home pública | idioma | tema ]
[ form-intro sticky ] [ form-card ]
  eyebrow               h2 Entrar
  h1 editorial          alerta role=alert
  lead                  email
                        senha
                        MFA (se a superfície exige)
                        esqueci a senha
                        CTA primário →
```

`form-layout`: `grid-template-columns: 0.85fr 1.15fr; gap: 2rem`. Abaixo de 900px: uma coluna; intro deixa de ser sticky.

Intro: eyebrow com traço, H1 `clamp(2rem, 4vw, 3.5rem)`, lead muted ~60ch.

Card: padding `clamp(1.5rem, 4vw, 2.5rem)`, border `--border`, radius 20px, `--surface`, sombra do token. Sem card-dentro-de-card.

## Campos

- Label acima, muted, ~0.76rem, peso 600. Uma linha, sem placeholder no lugar do label.
- Input 100%, **min-height 48px**, padding `.75rem .9rem`, radius 11px, fundo `--bg`, borda `--border`.
- Foco: `border-color: var(--action)` + anel `0 0 0 3px color-mix(in srgb, var(--action) 12%, transparent)`. Sem segundo retângulo (`outline: 0` no campo; o anel é o único).
- `autocomplete="username"` / `email` e `current-password` / `new-password`. `autocorrect="off"` na senha.
- Ordem dos campos **é** a jornada: identificador, senha, **depois** MFA. Código TOTP no meio (antes da senha) é achado.
- Erro do campo sob o input; erro de credencial no topo, `role="alert"`. Texto uniforme no miss (não “usuário não existe”).
- Link “Esqueci a senha” discreto, antes do submit.
- Submit: botão primário `--action`, seta `→` que desloca no hover. Largura do card.

Reset de senha e “conta criada” reutilizam o **mesmo** layout e os mesmos tokens. Não invente um segundo formulário.

## Comportamento

- CSRF se a sessão for cookie (`auth`).
- i18n PT/EN desde o primeiro commit. Tema herda do `html[data-theme]` — o chrome do login tem idioma e tema; o card não ganha um segundo toggle.
- Login é outra superfície. Sempre há um link **Voltar** (`backHome`) para a home pública (`VITE_PUBLIC_URL`). Sem isso a pessoa fica presa no backoffice.
- Cookie/audience da área interna **não** atravessa a home pública.
- Rate-limit e lockout são servidor; a UI só mostra a mensagem canônica.
- Após sucesso: navega para o shell autenticado (`frontend-shell`). Nunca deixa token em `localStorage` se o produto usa cookie httpOnly.

## Red flags

- Input de 36px “compacto”
- Placeholder no lugar de label
- Dois anéis de foco
- Login e home compartilhando cookie
- `fetch` dentro de `ui/`
- Mensagem “email não cadastrado”
- MFA antes da senha
- Login sem voltar para a home pública

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Duas colunas `0.85fr / 1.15fr`; &lt;900px uma coluna
- [ ] Label acima; input min-height 48; um anel de foco `--action`
- [ ] Campos: e-mail, senha, MFA (nesta ordem) quando a superfície pede o segundo fator
- [ ] Erro de credencial `role="alert"` uniforme; esqueci a senha antes do submit
- [ ] Seta `→` no CTA; i18n PT/EN; tema herdado do header
- [ ] Cookie interno não atravessa a home; `fetch` só em `lib/api.ts`
- [ ] Link voltar à home pública no chrome do login (`VITE_PUBLIC_URL`)
