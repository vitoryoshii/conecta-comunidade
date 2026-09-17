# PLAN — Redesign premium das telas internas

**Projeto:** Conecta Comunidade (acadêmico — UNIBTA)
**Data:** 2026-09-16
**Status:** Concluído (blocos 0–6)

## 1. Objetivo
Elevar as telas internas ao padrão premium (sombra no lugar de traço, tom sobre tom por
categoria, hierarquia tipográfica) e reestruturar a navegação: 5 destinos uniformes com Mapa
na barra e o "+" promovido a FAB flutuante. Só UI — nenhuma regra de negócio muda.

## 2. Contexto atual
- `theme.py` já centraliza cores, ícones e `cartao()`, mas o cartão tem `Border.all(1, BORDA)`
  **e** sombra: é o traço cinza que o redesign quer tirar. Não há tokens de sombra nomeados.
- `components/comuns.py:navegacao_inferior` monta a barra à mão, com o "+" como item do meio
  (`ABAS`), borda de traço no topo e `publicar` como se fosse aba.
- `main.py` compõe `Column([área, barra])` — não há camada para um FAB flutuar sobre a área.
- `CORES_CATEGORIAS` é uma lista indexada por posição: a mesma categoria muda de cor conforme
  a ordem da API. As categorias não têm slug; o campo estável é `icone` (`water_drop`,
  `restaurant`, ...), que vem também nos cartões (`categoria_icone`).
- `Usuario.avatar_url`, `UsuarioAtualizar.avatar_url` e `api.atualizar_perfil` **já existem** —
  o avatar com foto é trabalho de UI, não de backend.
- Perfil: os três cards de impacto têm `width=122` fixa em `Row(wrap=True)` — é o que corta o
  terceiro em tela estreita.

## 3. Escopo

### Dentro do escopo
- Bloco 0: tokens premium em `theme.py` (sombras, raios, cores, `CATEGORIA_CORES`, tipografia).
- Bloco 1: nav bar de 5 destinos (com Mapa) + FAB como componentes reutilizáveis.
- Blocos 2–6: Home, Explorar, Mapa, Perfil e Detalhe da solicitação.
- Avatar com foto: exibição na Home e no Perfil, com troca por `ft.FilePicker`.
- Ajuste dos testes de tela que dependem da árvore de controles.

### Fora do escopo
- Telas de autenticação (splash, login, cadastro, recuperar senha) — já refeitas.
- Chat, Conversas, ONGs, Perfil de ONG, Publicar, Nova solicitação/oferta, Minhas
  solicitações, Quero ajudar: recebem só o reflexo dos tokens (sombra/cor), sem redesenho.
- Mecânica do mapa (pins por coordenada normalizada em `Stack`) — só o visual muda.
- Upload de imagem para servidor/CDN: a foto é copiada para uma pasta local do app.
- Qualquer mudança de endpoint, modelo ou regra de negócio.

## 4. Arquivos afetados

| Arquivo | Ação | O que muda |
|---|---|---|
| `mobile/theme.py` | Editar | `SOMBRA_CARD/FLUTUANTE/NAV`, raios, cores premium, `CATEGORIA_CORES`, `titulo_secao`, `cartao()` sem traço |
| `mobile/components/nav_bar.py` | Criar | Barra de 5 destinos (Início, Explorar, Mapa, Mensagens, Perfil) |
| `mobile/components/fab.py` | Criar | FAB com gradiente teal→verde profundo, canto inferior direito |
| `mobile/components/comuns.py` | Editar | `navegacao_inferior` sai; cartões ganham cor por categoria e chevron |
| `mobile/main.py` | Editar | `Stack` para o FAB flutuar sobre a área; `mapa` vira aba; `publicar` sai das abas |
| `mobile/views/home.py` | Editar | Header com avatar + sino, linha de local, banner, 2 ações, categorias, próximas |
| `mobile/views/explorar.py` | Editar | Busca, chips e contador premium; cards no padrão da Home; vazio amigável |
| `mobile/views/mapa.py` | Editar | Cabeçalho com chip de contagem, pins com sombra, painel e sheet premium |
| `mobile/views/perfil.py` | Editar | Header com foto, impacto responsivo (sem corte), menu em cards sem traço |
| `mobile/views/detalhe_solicitacao.py` | Editar | Topo com badges, blocos em cards, ações destacadas |
| `mobile/components/avatar.py` | Criar | Avatar com foto e fallback de inicial, em um lugar só |
| `tests/test_mobile_views.py` | Editar | Seletores que dependem da árvore (nav, FAB, cards) |

Dependências novas: nenhuma.

## 5. Passos de execução
1. **Bloco 0** — tokens em `theme.py`; `cartao()` perde a borda de traço. Rodar `pytest`.
2. **Bloco 1** — `nav_bar.py` + `fab.py`, `main.py` com a camada do FAB, `mapa` como aba.
3. **Bloco 2** — Home (header/avatar, banner, ações, categorias tom sobre tom, próximas).
4. **Bloco 3** — Explorar (busca, chips, contador, lista, vazio).
5. **Bloco 4** — Mapa (cabeçalho, pins, painel de filtros, bottom sheet).
6. **Bloco 5** — Perfil (header com foto, impacto responsivo, menu) + troca de foto.
7. **Bloco 6** — Detalhe da solicitação.
8. `pytest` completo e conferência visual de cada bloco no app aberto do zero.

## 6. Riscos e pontos de atenção

| Risco | Impacto | Mitigação |
|---|---|---|
| FAB cobrindo o último item das listas | Médio | Padding inferior de ~96px nas listas roláveis das telas com FAB |
| Trocar `CORES_CATEGORIAS` (por índice) por `CATEGORIA_CORES` (por ícone) | Médio | Manter fallback para categoria nova/desconhecida; cor deixa de depender da ordem |
| Testes presos à árvore de controles (`ft.FilledButton`, contagem de cards) | Médio | Ajustar junto de cada bloco, não no fim |
| `ft.Image` com caminho local pode não renderizar no modo web | Médio | Avatar sempre com `error_content` = inicial estilizada; foto é recurso de desktop |
| Redesenho amplo mexendo em tela que eu não testo visualmente | Médio | Conferência tela a tela no app servido em web; blocos pequenos e commit por bloco |
| Escopo grande em uma rodada só | Alto | Ordem fixa dos blocos; cada bloco fecha com `pytest` verde antes do seguinte |

## 7. Validação
- [x] Nav bar com 5 destinos e Mapa; FAB no canto inferior direito nos cinco destinos;
      publicar abre pelo FAB (`test_barra_tem_cinco_destinos_uniformes_com_o_mapa`,
      `test_fab_aparece_nos_destinos_e_some_nas_telas_empilhadas`, `test_fab_abre_a_tela_de_publicar`).
- [x] Nenhuma borda cinza de traço nas telas do escopo — varredura da árvore de controles
      de Home, Explorar, Perfil e Mapa em `test_telas_do_redesign_nao_tem_borda_cinza`.
- [x] Categorias tom sobre tom e estáveis: a cor vem do ícone, não da ordem da API
      (`test_cor_da_categoria_nao_depende_da_ordem_da_api`).
- [x] Perfil sem cortar o terceiro card de impacto — os três expandem
      (`test_impacto_do_perfil_divide_a_largura_em_tres`).
- [x] Avatar com foto na Home e no Perfil, com fallback de inicial e troca por FilePicker.
- [x] `pytest` verde ao fim de cada bloco — 107 testes.
- [ ] **Com você:** conferência visual na janela nativa, bloco a bloco, com o app aberto do
      zero. O modo web não serviu desta vez: a captura reescalava a cada redimensionamento.
