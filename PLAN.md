# PLAN — Cadastro: data de nascimento no desktop, confirmação de senha e documentos legais

> **Registro histórico.** Este plano foi concluído. A versão atual não mantém
> senhas no rascunho de navegação e usa ações explícitas para abrir Termos e
> Política, porque `TextSpan` dentro de `Checkbox` não recebe toques de forma
> confiável em todas as plataformas. Para o estado operacional atual, consulte
> `README.md`, `docs/homologacao-v1.0.0-rc.1.md` e os testes em `tests/`.

**Projeto:** Conecta Comunidade (acadêmico — UNIBTA)
**Data:** 2026-09-16
**Status:** Concluído

## 1. Objetivo
Destravar a escolha da data de nascimento no app desktop, acrescentar confirmação de senha
com feedback ao vivo e ligar o checkbox de consentimento aos documentos legais — que passam a
ser exibidos no app e o aceite passa a ser registrado no banco.

## 2. Contexto atual
- `mobile/views/cadastro.py:255` abre o `ft.DatePicker` pelo `on_click` de um `ft.Container`
  que envolve o `TextField`. O campo absorve o clique do mouse, então o handler do Container
  nunca dispara no desktop. `page.show_dialog()` **é** a API correta no Flet 0.86 (ela já
  monta o diálogo; `page.overlay` não é usado) e `ft.TextField` tem `on_click` próprio —
  é por aí que a correção passa.
- As views são reconstruídas a cada navegação (`App.renderizar`), logo abrir outra tela
  **apaga** o formulário. Preservar o cadastro exige guardar um rascunho no `AppState`.
- Os .md legais já existem em `mobile/assets/legal/`. Nada no app os lê.
- `POST /auth/register` valida CPF/telefone/nascimento, mas não conhece aceite de termos.

## 3. Escopo

### Dentro do escopo
- Data de nascimento clicável no desktop (`on_click` no próprio campo + ícone de calendário).
- Campo "Confirmar senha" com feedback verde/vermelho ao vivo e botão condicionado.
- Nova ordem dos campos, conforme pedido.
- Tela `documento_legal` (Markdown rolável) + links no texto do checkbox.
- Rascunho do cadastro no `AppState`, para voltar do documento sem perder nada.
- `aceite_termos` + `data_aceite` no modelo, migration, registro e 422 quando ausente.

### Fora do escopo
- Versionamento dos documentos (guardar *qual versão* foi aceita) e tela de revogação.
- Recibo/exportação dos dados do titular (LGPD art. 18) e política de retenção.
- Aceite de termos no login ou em cadastros já existentes (retroativo).
- Tradução do calendário para pt-BR (`locale_configuration` da página).

## 4. Arquivos afetados

| Arquivo | Ação | O que muda |
|---|---|---|
| `mobile/views/cadastro.py` | Editar | DatePicker, confirmar senha, ordem, links, rascunho, aceite no payload |
| `mobile/views/documento_legal.py` | Criar | Tela clara com voltar, título e `ft.Markdown` rolável |
| `mobile/legal_textos.py` | Criar | Lê os .md de `assets/legal` (com texto de fallback) — sem duplicar o conteúdo |
| `mobile/main.py` | Editar | Registra a rota `documento_legal` |
| `mobile/state.py` | Editar | `rascunho_cadastro: dict` + `limpar_rascunho()` |
| `mobile/theme.py` | Editar | `campo_claro` aceita `ao_clicar`/`somente_leitura`/`sufixo`; helper de status verde/vermelho |
| `backend/models/usuario.py` | Editar | `aceite_termos: bool` e `data_aceite: datetime \| None` |
| `backend/schemas/usuario.py` | Editar | `aceite_termos` em `UsuarioCriar`; aceite + data em `UsuarioPrivadoLer` |
| `backend/routers/auth.py` | Editar | 422 sem aceite; grava `data_aceite=agora` |
| `alembic/versions/0004_usuario_aceite_termos.py` | Criar | Duas colunas novas (revises `0003`) |
| `backend/services/seed_service.py` | Editar | Usuários de demonstração já com aceite registrado |
| `tests/test_auth.py`, `tests/test_dados_pessoais.py` | Editar | `aceite_termos` nos payloads; 422 sem aceite; data persistida |
| `tests/test_mobile_views.py` | Editar | Confirmação de senha, links dos documentos, rascunho preservado, rota nova |

Dependências novas: nenhuma.

## 5. Passos de execução
1. Backend: modelo + migration 0004 + schema + router (422 sem aceite, grava a data) + seed.
2. Ajustar os payloads dos testes existentes e somar os casos novos; `pytest` verde.
3. `legal_textos.py` e a tela `documento_legal`; registrar a rota em `main.py`.
4. `theme.campo_claro`: `ao_clicar`, `somente_leitura`, `sufixo` e helper de status.
5. Cadastro: corrigir o DatePicker (`on_click` no campo, `first_date=1900`, `last_date`=hoje−18).
6. Cadastro: confirmar senha com feedback ao vivo e regra de habilitação do botão.
7. Cadastro: nova ordem dos campos, links no consentimento e rascunho no `AppState`.
8. Validar no app rodando (uvicorn + flet): clicar no campo e escolher a data até o fim.
   Se o calendário não abrir, trocar por três seletores Dia/Mês/Ano (os dropdowns de
   estado/cidade já funcionam no desktop) e refazer a validação.
9. `pytest` completo + abrir o app do zero (sem hot reload).

## 6. Riscos e pontos de atenção

| Risco | Impacto | Mitigação |
|---|---|---|
| Migration em `conecta.db` com usuários já gravados | Médio | `server_default` nas duas colunas; `batch_alter_table` (SQLite) e `downgrade` testado |
| Aceite obrigatório quebra os testes/clientes atuais de `/auth/register` | Médio | Ajustar os payloads na mesma entrega; erro 422 com mensagem explícita |
| DatePicker do Flutter pode não abrir no Windows por outro motivo | Alto | Passo 8 valida no app real; fallback de dropdowns já autorizado |
| Rascunho do cadastro guarda senha em memória | Médio | Fica só no `AppState` da sessão, é apagado ao criar a conta e ao sair do fluxo |
| `ROTAS` nova entra no teste parametrizado de todas as telas | Baixo | A tela aceita rota sem parâmetro (abre os Termos por padrão) |

## 7. Validação
- [x] Clicar no campo abre o calendário e a data escolhida aparece como dd/mm/aaaa — conferido
      no app rodando (`flet run --web`, mesmo widget do desktop): campo → ano → dia → Confirmar
      → "12/09/1999" no campo. O `DatePicker` não abria por dois motivos, ambos corrigidos: o
      `on_click` estava no `Container` em volta (o `TextField` consome o clique) e o `value`
      padrão do seletor era a data de hoje, fora de [`first_date`, `last_date`].
- [x] Confirmação de senha: vermelho ao divergir, verde ao coincidir; botão só liga com tudo ok
      (coberto por `test_confirmacao_de_senha_avisa_ao_vivo` e `test_cadastro_exige_consentimento_lgpd`).
- [x] "Termos de Uso" e "Política de Privacidade" abrem os documentos; voltar preserva o
      formulário (`test_links_do_consentimento_abrem_os_documentos`,
      `test_voltar_do_documento_preserva_o_cadastro`).
- [x] Sem checkbox não envia; backend responde 422 sem aceite e grava `data_aceite`.
- [x] `pytest` verde: 99 testes, incluindo senha ≠ confirmação e registro sem aceite → 422.
- [x] App aberto do zero com o código novo (a execução em modo web foi uma partida limpa, sem
      hot reload); migration 0004 aplicada em `conecta.db` com ida e volta testada.

**Pendente com você:** conferir o calendário na janela nativa do Windows — a validação acima
foi feita no mesmo app servido no navegador, que usa o mesmo Flutter. O fallback de três
seletores (Dia/Mês/Ano) não foi necessário.
