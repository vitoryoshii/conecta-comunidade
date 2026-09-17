# Decisões técnicas

`// por que cada escolha` · Conecta Comunidade · por **VyteTech**

Registro curto das decisões de engenharia, o contexto de cada uma e o que foi
descartado no caminho.

---

## `01` Flet para a interface mobile

**Contexto.** O requisito era um app mobile com **stack 100% Python**.

**Decisão.** Flet, que renderiza Flutter e é dirigido por Python.

**Alternativas descartadas.**

- *Kivy* — desenha os próprios widgets; o resultado não tem cara de app nativo.
- *BeeWare/Toga* — mais próximo do nativo, porém com catálogo de componentes menor.
- *React Native / Flutter puro* — sairia da stack Python exigida.

**Consequência.** Ganhamos Material Design pronto e a mesma base rodando em
desktop, web e mobile. O custo é depender do ritmo de evolução do Flet — que é
rápido: a versão usada (**0.86**) trocou `ft.padding.all()` por `ft.Padding.all()`,
`ft.colors` por `ft.Colors` e removeu `page.views`. Por isso o app **não usa o
roteador por URL do Flet** (ver decisão `05`).

---

## `02` SQLModel como ORM

**Contexto.** Precisávamos de modelos de banco e de schemas de API.

**Decisão.** SQLModel, que é SQLAlchemy 2 + Pydantic v2 na mesma classe.

**Consequência.** Um único `Solicitacao` serve de tabela e de base de validação,
eliminando a duplicação clássica "model + schema idênticos". Onde a resposta
precisa de campos calculados (`distancia_km`, `tempo_publicacao`), mantivemos
schemas Pydantic separados em `backend/schemas/` — a API não devolve a tabela
crua, e sim uma projeção pensada para a tela.

---

## `03` Como o JWT é validado

**Fluxo.**

1. `POST /auth/login` confere a senha com `passlib.verify` (bcrypt).
2. `auth_service.criar_access_token` assina um JWT **HS256** com
   `sub = str(usuario_id)`, `iat` e `exp` (7 dias).
3. Cada requisição envia `Authorization: Bearer <token>`.
4. `deps.get_current_user` decodifica, valida assinatura e expiração, converte
   `sub` para `int` e carrega o usuário do banco.
5. Qualquer falha vira **401** com `WWW-Authenticate: Bearer`.

**Duas dependências, não uma.** `UsuarioAtual` exige token; `UsuarioOpcional`
aceita a ausência dele. É o que permite o **modo visitante**: listar pedidos sem
conta, mas sem poder publicar.

**Detalhe importante.** `sub` vai como **string**, conforme a RFC 7519 — algumas
bibliotecas rejeitam `sub` numérico.

**Senhas.** Nunca gravadas em texto puro. O bcrypt aplica salt automático e é
lento de propósito. O limite de 72 bytes do algoritmo é validado nos schemas
(`senha: str = Field(min_length=6, max_length=72)`), evitando erro no hash.

> **Armadilha de versão.** `passlib 1.7.4` é incompatível com `bcrypt >= 5.0`:
> a detecção de backend levanta `ValueError: password cannot be longer than 72
> bytes`. Por isso o `requirements.txt` **fixa `bcrypt==4.0.1`**.

---

## `04` Como a distância é calculada

**Decisão.** `geopy.distance.great_circle` (haversine) entre o par lat/long do
usuário e o de cada recurso, isolado em `services/geo_service.py`.

**Por que haversine e não `geodesic`.** `geodesic` (Vincenty/Karney) é mais
preciso, mas mais caro. Em escala urbana a diferença é de metros — irrelevante
para "a 1,2 km de você" — e a listagem calcula a distância para dezenas de itens
por requisição.

**Onde o cálculo acontece.** Em **Python, depois da consulta**: o SQLite não tem
função haversine nativa. O router busca os registros filtrados, enriquece cada
um e só então ordena.

**Limite conhecido.** Isso não escala para milhões de registros — seria preciso
paginar geograficamente ou migrar para PostgreSQL + PostGIS e empurrar o cálculo
para o SQL. Para o escopo do projeto (comunidades de bairro), é a escolha certa:
zero dependência extra e código testável de forma isolada.

**Contratos do serviço.**

- Coordenada `(0, 0)` é tratada como "sem localização" — está no meio do
  Atlântico e, na prática, sinaliza campo não preenchido.
- Sem coordenada válida, a função devolve `None`, e a interface mostra `--` em
  vez de um número enganoso.
- `chave_ordenacao_distancia` devolve `inf` para `None`, jogando registros sem
  localização para o fim de qualquer lista.

---

## `05` Navegação com pilha própria

**Contexto.** O Flet 0.86 removeu `page.views` e mudou o modelo de rotas.

**Decisão.** O app mantém a pilha de rotas em `AppState.pilha` e redesenha a
árvore a cada navegação. Cada tela é uma função `construir(app) -> ft.Control`.

**Consequências.**

- O comportamento não depende da API de roteamento do Flet, que ainda muda entre versões.
- O botão voltar funciona em qualquer profundidade.
- As cinco abas inferiores **reiniciam** a pilha; as demais telas empilham.
- Testável sem abrir janela: `tests/test_mobile_views.py` monta as 17 rotas em memória.

**Detalhe.** Os métodos de navegação declaram o nome da rota como
**posicional-only** (`def navegar(self, rota, /, **parametros)`). Sem isso, uma
tela com um parâmetro chamado `nome` — como o chat — colidiria com o argumento
do próprio método. O bug apareceu no teste de renderização antes de chegar ao app.

---

## `06` Tiles do OpenStreetMap em vez de `ft.Map` ou WebView

**Contexto.** O controle `ft.Map` não vem no pacote base do Flet 0.86 (está na
extensão `flet-map`, que exige build nativo), e `ft.WebView` **também não**: ele
virou o pacote separado `flet-webview`, cujo plugin Flutter não suporta Windows
desktop — justamente onde o app é desenvolvido e demonstrado. A primeira versão
desta tela desenhava um mapa esquemático (pins sobre uma grade vazia), que se
lia como wireframe.

**Decisão.** Baixar as imagens de tile do OpenStreetMap com o próprio
`ft.Image` e montá-las em um `ft.Stack`, posicionando os pins por cima com a
projeção **Web Mercator** de verdade (`mobile/mapa_tiles.py`). Para zoom e
arrasto, o botão "Abrir mapa interativo" gera uma página **Leaflet** com os
mesmos pontos e a abre no navegador (`mobile/mapa_leaflet.py`).

**Consequência.** O app mostra ruas de verdade em qualquer plataforma, sem
chave de API, sem dependência nova e sem toolchain nativa; os pins caem na
posição geográfica correta, e não apenas na posição relativa. Em troca, o mapa
embutido é estático (o zoom vem do enquadramento dos pontos) e depende de rede
— sem ela, o `error_content` de cada tile devolve a superfície verde-clara e os
pins continuam no lugar. O volume de tiles é pequeno e cabe na política de uso
do OSM; um app com muitos usuários precisaria de provedor de tiles próprio.

---

## `07` Contadores de impacto denormalizados

**Contexto.** A tela de perfil mostra três números em destaque.

**Decisão.** Guardar `solicitacoes_atendidas`, `doacoes_recebidas` e
`acoes_voluntario` como colunas em `usuario`, atualizadas nos eventos de negócio
(entrega realizada, oferta enviada, pedido concluído).

**Alternativa descartada.** Calcular por agregação a cada abertura do perfil.

**Consequência.** Leitura instantânea, sem `COUNT` em várias tabelas. O preço é
manter a consistência na escrita — por isso as atualizações ficam concentradas
em `routers/entregas.py` e `routers/ofertas.py`, e não espalhadas. `GET
/perfil/impacto` complementa esses contadores com três agregações calculadas na
hora (pedidos criados, ofertas enviadas, pessoas beneficiadas).

---

## `08` ONG como catálogo, não como usuário

**Contexto.** Uma instituição poderia ser modelada como um tipo de `Usuario`.

**Decisão.** `ONG` é uma tabela própria, sem login. Existe também o tipo de
usuário `ong`, para a **pessoa** que representa a instituição.

**Consequência.** A ficha institucional (avaliação, selo de verificação,
recursos disponíveis em JSON) fica limpa e o catálogo pode ser populado sem
criar credenciais. A contrapartida é que "Falar com a ONG" ainda não abre um
chat direto — evolução natural: vincular `ONG.responsavel_id → Usuario.id`.

---

## `09` Enriquecimento centralizado

**Decisão.** `services/apresentacao.py` concentra a montagem dos schemas de
leitura, carregando categorias e autores **em lote** (`carregar_mapa_usuarios`).

**Motivo.** Evita o problema N+1: uma listagem de 50 pedidos faria 100 queries
extras se cada item buscasse seu autor e sua categoria. E garante que Home,
Explorar, Mapa e detalhe mostrem exatamente os mesmos números.

---

## `10` Testes com SQLite em memória

**Decisão.** Cada teste recebe um banco `sqlite://` novo, com `StaticPool` para
manter a mesma conexão, e o `get_session` do FastAPI é sobrescrito por
`dependency_overrides`.

**Consequência.** Testes isolados, rápidos e sem tocar o `conecta.db` de
desenvolvimento. As telas Flet são testadas pelo mesmo caminho, trocando o
transporte HTTP do `ApiClient` pelo `TestClient` — sem rede e sem Uvicorn.

---

`Construído por` **VyteTech** — *Tecnologia para negócios.*
