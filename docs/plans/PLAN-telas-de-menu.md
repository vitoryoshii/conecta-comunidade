# PLAN — Telas de menu e Mensagens premium

**Projeto:** Conecta Comunidade (acadêmico — UNIBTA)
**Data:** 2026-09-17
**Status:** Concluído (blocos 1–5)

## 1. Objetivo
Dar destino aos itens do menu do Perfil que hoje respondem "em breve" — Editar perfil,
Configurações, Ajuda e Favoritos — e elevar a lista de Mensagens ao padrão premium.
Favoritos e troca de senha exigem backend novo; o resto é UI sobre o que já existe.

## 2. Contexto atual
- `PATCH /usuarios/me` já aceita nome, estado/cidade, coordenadas e avatar. **Não** aceita
  telefone: `UsuarioAtualizar` não tem o campo, então editar telefone exige acrescentá-lo.
- Não há rota de troca de senha. `auth_service` já tem `verificar_senha` e `gerar_hash_senha`.
- `GET /auth/me` devolve o CPF já mascarado — a tela de edição não precisa mascarar nada.
- Não existe modelo de favoritos nem de preferências de notificação.
- `cartao_conversa` (em `components/comuns.py`) ainda é do desenho antigo: avatar por inicial,
  sem horário e sem o chip da solicitação no estilo novo. `ConversaLer` já traz
  `interlocutor_avatar`, `ultima_em` e `nao_lidas` — o dado existe, falta a tela usar.
- `conversas.py` não reserva espaço para o FAB: o último item fica atrás dele.
- `perfil.py` liga "Favoritos", "Configurações" e "Ajuda" a `em_breve(...)`.

## 3. Escopo

### Dentro do escopo
- Blocos 1–5 do pedido: Editar perfil, Configurações (com troca de senha), Ajuda, Favoritos
  (backend + tela + coração nos cartões) e a lista de Mensagens premium.
- Backend novo: `telefone` em `UsuarioAtualizar`, `PATCH /usuarios/me/senha`, modelo
  `Favorito` + `POST/DELETE/GET /favoritos` + migration `0005`.
- Ligar os itens do menu do Perfil às telas e registrar as rotas.

### Fora do escopo
- Favoritar **ofertas** — só solicitações nesta rodada (a segunda versão do pedido cita
  "solicitações/ofertas"; o detalhamento do Bloco 4 fala em solicitação, que é o que o
  cartão e a tela de detalhe suportam hoje).
- Envio real de notificações (push/e-mail): os toggles guardam a preferência, nada dispara.
- Recuperação de senha por e-mail (a rota atual só responde a mensagem padrão).
- Chat individual, já refeito.
- Editar e-mail, CPF ou data de nascimento — permanecem somente-leitura.

## 4. Arquivos afetados

| Arquivo | Ação | O que muda |
|---|---|---|
| `backend/models/favorito.py` | Criar | `usuario_id`, `solicitacao_id`, `criado_em`, único por par |
| `backend/models/__init__.py` | Editar | Reexporta `Favorito` |
| `backend/schemas/favorito.py` | Criar | `FavoritoCriar`, `FavoritoLer` |
| `backend/routers/favoritos.py` | Criar | `GET/POST /favoritos`, `DELETE /favoritos/{solicitacao_id}` |
| `backend/routers/usuarios.py` | Editar | `PATCH /usuarios/me/senha` (valida a senha atual) |
| `backend/schemas/usuario.py` | Editar | `telefone` em `UsuarioAtualizar`; `TrocarSenha`; toggles de notificação |
| `backend/models/usuario.py` | Editar | Três preferências de notificação (bool, default `True`) |
| `backend/routers/solicitacoes.py` | Editar | Marca `favoritada` nas listagens e no detalhe do usuário logado |
| `backend/schemas/solicitacao.py` | Editar | Campo derivado `favoritada: bool` |
| `alembic/versions/0005_favoritos_e_notificacoes.py` | Criar | Tabela `favorito` + colunas de preferência |
| `mobile/views/editar_perfil.py` | Criar | Formulário premium + avatar + somente-leitura |
| `mobile/views/configuracoes.py` | Criar | Conta, Notificações, Privacidade, Sobre |
| `mobile/views/alterar_senha.py` | Criar | Senha atual + nova + confirmação (feedback ao vivo reusado) |
| `mobile/views/ajuda.py` | Criar | FAQ expansível, fale conosco, links legais |
| `mobile/views/favoritos.py` | Criar | Lista no padrão dos cartões + vazio amigável |
| `mobile/views/conversas.py` | Editar | Cabeçalho, busca, itens premium, vazio, folga do FAB |
| `mobile/components/comuns.py` | Editar | `cartao_conversa` premium; coração em `cartao_solicitacao` |
| `mobile/views/perfil.py` | Editar | Menu apontando para as telas novas |
| `mobile/views/detalhe_solicitacao.py` | Editar | Coração na barra de ações |
| `mobile/main.py` | Editar | Registra as cinco rotas novas |
| `mobile/api_client.py` | Editar | `listar_favoritos`, `favoritar`, `desfavoritar`, `trocar_senha` |
| `tests/test_favoritos.py` | Criar | Favoritar, listar, desfavoritar, duplicidade, isolamento por usuário |
| `tests/test_auth.py` | Editar | Troca de senha: atual errada → 400; certa → nova senha entra |
| `tests/test_mobile_views.py` | Editar | Rotas novas, menu do Perfil, conversas premium, coração |

Dependências novas: nenhuma.

## 5. Passos de execução
1. **Backend** — modelo `Favorito`, preferências no `Usuario`, migration 0005, schemas,
   router de favoritos, `PATCH /usuarios/me/senha`, `telefone` no patch de perfil,
   `favoritada` nas solicitações. `pytest` com os testes novos de API.
2. **Bloco 1** — `editar_perfil.py` + rota + item do menu.
3. **Bloco 2** — `configuracoes.py` e `alterar_senha.py` + rotas.
4. **Bloco 3** — `ajuda.py` + rota.
5. **Bloco 4** — `favoritos.py`, coração no cartão e no detalhe, `api_client`.
6. **Bloco 5** — `conversas.py` e `cartao_conversa` premium.
7. `pytest` completo; conferência tela a tela com o app aberto do zero.

## 6. Riscos e pontos de atenção

| Risco | Impacto | Mitigação |
|---|---|---|
| `favoritada` exige saber quem está logado em rotas hoje anônimas | Médio | `UsuarioOpcional` já existe nas listagens; sem sessão, o campo vai `False` |
| Consulta de favoritos por cartão vira N+1 | Médio | Carregar os ids favoritados do usuário em um `set` por requisição |
| Troca de senha é rota sensível | Alto | Exige a senha atual, devolve 400 genérico, respeita o limite de 72 bytes do bcrypt |
| Toggles de notificação sem nada que os consuma | Baixo | Persistir de verdade e comentar que o disparo não existe — melhor que um TODO solto |
| Coração nos cartões muda um componente usado em 4 telas | Médio | Parâmetro opcional: sem callback de favoritar, o cartão fica como está |
| Migration em base com dados | Médio | Tabela nova + colunas com `server_default`; `downgrade` testado |

## 7. Validação
- [x] Cada tela abre pelo menu do Perfil e monta (`test_menu_do_perfil_abre_cada_tela`);
      todas voltam por `app.voltar`, que preserva a pilha do Perfil.
- [x] Editar perfil salva nome e telefone via PATCH; e-mail e CPF fora de campo editável, e o
      CPF exibido é o mascarado da API.
- [x] Alterar senha: 400 com a senha atual errada (a antiga continua valendo), 204 com a
      correta e login com a nova.
- [x] Favoritar pela Home coloca em Favoritos; desfavoritar esvazia com o recado; o cartão
      sem `ao_favoritar` continua idêntico ao que era.
- [x] Mensagens com avatar, horário relativo, não lidas em negrito, chip do pedido, busca e
      vazio amigável.
- [x] `pytest` verde — 153 testes.
- [ ] **Com você:** conferência visual com o app aberto do zero (sem hot reload).

## 8. Achado durante a execução
`backend.database.init_db()` roda `SQLModel.metadata.create_all` a cada start da API. Com a
API de pé, a tabela `favorito` nasceu pelo `create_all` **antes** da migration, e o
`alembic upgrade` quebrou com "table favorito already exists" — enquanto as colunas novas de
`usuario` (que `create_all` não acrescenta a tabela existente) continuavam faltando. Resolvido
apagando a tabela vazia e aplicando a 0005. Vale decidir, em algum momento, se `init_db`
continua criando esquema fora do Alembic: os dois juntos vão brigar de novo no próximo modelo.

> **Resolvido em 17/09/2026:** `init_db()` foi removido. O `create_all` não roda
> mais em lugar nenhum da aplicação (nem no startup da API, nem no seed) — o
> schema passou a vir só de `alembic upgrade head`. O seed agora checa o schema
> antes e falha com instrução em vez de erro cru. Ver `docs/decisoes.md`.
