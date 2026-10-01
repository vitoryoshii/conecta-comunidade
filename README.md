<div align="center">

<img src="docs/assets/vytetech-symbol.svg" alt="VyteTech" width="76" />

### <span style="color:#22486C">Vyte</span><span style="color:#21BCCE">Tech</span>

# Conecta Comunidade

**Quem precisa de ajuda e quem pode ajudar, a poucos quilômetros de distância.**

![status](https://img.shields.io/badge/%E2%97%8F%20sistema%20no%20ar-3DDC97?style=flat-square&labelColor=0C1A22)
&nbsp;
![python](https://img.shields.io/badge/python-3.12%2B-21BCCE?style=flat-square&labelColor=0C1A22)
![fastapi](https://img.shields.io/badge/fastapi-0.141-21BCCE?style=flat-square&labelColor=0C1A22)
![flet](https://img.shields.io/badge/flet-0.86-21BCCE?style=flat-square&labelColor=0C1A22)
![sqlmodel](https://img.shields.io/badge/sqlmodel-0.0.42-21BCCE?style=flat-square&labelColor=0C1A22)
![jwt](https://img.shields.io/badge/auth-JWT-21BCCE?style=flat-square&labelColor=0C1A22)
![tests](https://img.shields.io/badge/pytest-61%20testes-3DDC97?style=flat-square&labelColor=0C1A22)
![license](https://img.shields.io/badge/license-MIT-4A6076?style=flat-square&labelColor=0C1A22)

</div>

---

## `// sobre`

Depois de um alagamento, de uma frente fria ou de uma conta que não fechou,
falta sempre a mesma coisa: **saber quem, ali perto, tem o que está faltando.**
A ajuda existe — o que não existe é o encontro.

O **Conecta Comunidade** é um aplicativo mobile que resolve exatamente esse
encontro. Quem precisa publica um pedido georreferenciado; quem pode ajudar vê
os pedidos **ordenados por distância real**, se propõe, conversa pelo chat e
agenda a entrega. Pedidos marcados como emergência furam a fila em todas as
telas.

**Para quem é:**

| Perfil | O que faz no app |
| --- | --- |
| `solicitante` | Publica pedidos, acompanha status, combina a entrega |
| `doador` | Encontra pedidos próximos, oferece itens, agenda entregas |
| `voluntario` | Oferece transporte e pontos de retirada |
| `ong` | Catálogo de instituições com selo de verificação e avaliação |

Projeto acadêmico construído com **stack 100% Python** — do banco à interface.

---

## `// telas`

> Substitua os placeholders pelas capturas em `docs/assets/`
> (instruções em [`docs/assets/README.md`](docs/assets/README.md)).

| | | |
| :-: | :-: | :-: |
| ![Splash](docs/assets/tela-splash.png) | ![Home](docs/assets/tela-home.png) | ![Explorar](docs/assets/tela-explorar.png) |
| **Splash / Onboarding** | **Home** | **Explorar** |
| ![Detalhe](docs/assets/tela-detalhe.png) | ![Chat](docs/assets/tela-chat.png) | ![Mapa](docs/assets/tela-mapa.png) |
| **Detalhe do pedido** | **Chat + entrega** | **Mapa com filtros** |
| ![ONGs](docs/assets/tela-ongs.png) | ![Perfil](docs/assets/tela-perfil.png) | ![Demo](docs/assets/demo.gif) |
| **ONGs e instituições** | **Meu impacto** | **Fluxo completo** |

São **13 telas** implementadas: Splash, Cadastro, Login, Home, Explorar,
Detalhe da solicitação, Quero ajudar, Chat, Mapa, ONGs, Perfil da ONG, Minhas
solicitações e Meu perfil — mais os formulários de publicação, com navegação
inferior de cinco abas.

---

## `// stack`

Cada escolha e por que ela está aqui. O detalhamento está em
[`docs/decisoes.md`](docs/decisoes.md).

| `camada` | `tecnologia` | por que |
| --- | --- | --- |
| Mobile/UI | `flet` | Flutter renderizado por Python — visual nativo sem sair da stack |
| API | `fastapi` | Tipagem, validação e **Swagger gerado automaticamente** |
| ORM | `sqlmodel` | SQLAlchemy 2 + Pydantic v2 na mesma classe: um modelo, não dois |
| Banco | `sqlite` / `postgresql` | Zero configuração no dev; troca por variável de ambiente |
| Auth | `python-jose` + `passlib[bcrypt]` | JWT HS256 e hash com salt automático |
| Validação | `pydantic v2` | Contratos explícitos de entrada e saída |
| Migrations | `alembic` | Histórico versionado do schema |
| Geo | `geopy` | Haversine sem depender de banco geoespacial |
| Servidor | `uvicorn` | ASGI rápido, com `--reload` no desenvolvimento |
| Testes | `pytest` + `httpx` | Banco em memória, sem tocar o `conecta.db` |

---

## `// funcionalidades`

- **Distância real** — haversine (`geopy`) entre o usuário e cada pedido, oferta ou ONG, exibida em km/m.
- **Modo emergência** — fixa o pedido no topo de todas as listas e destaca o pin no mapa.
- **Filtros** — categoria, urgência, status, tipo de ajuda e busca em texto livre.
- **Badge de urgência** — verde, âmbar e vermelho para baixa, média e alta.
- **Mapa com toggles** — quatro tipos de pin (ajuda, oferecendo, ONGs, pontos de retirada) com contagem por tipo.
- **ONGs verificadas** — selo de verificação, avaliação média em estrelas e recursos disponíveis.
- **Chat com agendamento** — combinar dia, hora e local gera um registro de entrega, destacado no topo da conversa.
- **Meu impacto** — três contadores que crescem conforme as entregas são concluídas.
- **Modo visitante** — dá para explorar tudo sem criar conta; publicar exige login.

---

## `~/como-rodar`

### Ambientes do mobile

O app mobile fala exclusivamente com a API FastAPI; ele nunca recebe URL de
banco, credenciais Neon ou segredo JWT. O APK usa a API de produção por padrão:
`https://conecta-comunidade-wheat.vercel.app`.

Para desenvolvimento local, defina o ambiente antes de iniciar o Flet:

```powershell
$env:CONECTA_MOBILE_ENV = "development"
flet run mobile/main.py
```

Para voltar ao comportamento de produção no terminal atual:

```powershell
$env:CONECTA_MOBILE_ENV = "production"
```

### Pré-requisitos

- **Python 3.12+** (validado em 3.14)
- `pip` e `venv` (já vêm com o Python)
- Nenhum banco externo: o arquivo SQLite nasce do `alembic upgrade head`

### Passo a passo

```bash
# 1. clonar e entrar no projeto
$ git clone <url-do-repositorio> conecta-comunidade
$ cd conecta-comunidade

# 2. ambiente virtual
$ python -m venv .venv
$ .venv\Scripts\activate          # Windows
$ source .venv/bin/activate       # Linux / macOS

# 3. dependências
$ pip install -r requirements.txt

# 4. variáveis de ambiente
$ copy .env.example .env          # Windows
$ cp .env.example .env            # Linux / macOS

# 5. criar o schema (migrations) — passo obrigatório
$ alembic upgrade head

# 6. popular com dados de demonstração
$ python seed.py
```

> **O schema vem só do Alembic.** A API não cria tabela nenhuma ao subir: se
> você pular o passo 5, o `seed.py` avisa e as rotas falham por falta de
> tabela. O mesmo vale depois de um `git pull` que traga migrations novas —
> rode `alembic upgrade head` de novo (é idempotente: num banco já atualizado
> ele não faz nada).

Agora **dois terminais**, ambos com o `.venv` ativo:

```bash
# terminal 1 — API
$ uvicorn backend.main:app --reload
#   → http://127.0.0.1:8000/docs
```

```bash
# terminal 2 — app mobile
$ flet run mobile/main.py
```

> **Antes de apresentar:** rode o `seed.py`. O app abre com 8 solicitações, 5
> ONGs, 4 ofertas, um chat em andamento e uma entrega agendada — em vez de
> telas vazias.

### Contas de demonstração

Todas com a senha `senha123` (a tela de login traz atalhos de um toque):

| e-mail | perfil | região |
| --- | --- | --- |
| `ana@conecta.com` | solicitante | Vila Madalena |
| `carlos@conecta.com` | doador | Pinheiros |
| `juliana@conecta.com` | voluntária | Butantã |
| `marcos@conecta.com` | solicitante | Capão Redondo |
| `beatriz@semear.org` | ONG | Centro |

### Usar PostgreSQL

Troque uma linha no `.env` e rode as migrations de novo:

```bash
DATABASE_URL="postgresql+psycopg://usuario:senha@localhost:5432/conecta"
```

```bash
$ pip install "psycopg[binary]"
$ alembic upgrade head
$ python seed.py
```

---

## `$ testes`

```bash
# suíte completa
$ pytest

# com relatório de cobertura
$ pytest --cov=backend --cov=mobile --cov-report=term-missing

# relatório navegável em htmlcov/index.html
$ pytest --cov=backend --cov=mobile --cov-report=html
```

## Android

O empacotamento está configurado em `pyproject.toml` com o nome **Conecta
Comunidade**, versão `1.0.0` e bundle ID `br.edu.conectacomunidade.app`. O
arquivo raiz `requirements.txt` permanece compatível com a Vercel; os arquivos
`requirements-backend.txt`, `requirements-mobile.txt` e `requirements-dev.txt`
servem para instalações separadas locais.

Pré-requisitos: Python 3.12–3.14, JDK 17 e Android SDK. O Flet pode instalar
as ferramentas ausentes no primeiro build. Valide o ambiente com:

```bash
flet doctor
```

Gere um APK de apresentação a partir da raiz:

```bash
flet build apk --output build/apk --yes
```

O APK será criado sob `build/apk/`. Copie-o para o dispositivo Android e abra o
arquivo para instalar, autorizando instalação de fontes desconhecidas quando o
sistema solicitar. Para um futuro envio à Play Store, use `flet build aab` e
configure uma keystore fora do repositório por variáveis `FLET_ANDROID_*`.

## Segurança de produção

Na Vercel, `DATABASE_URL`, `SECRET_KEY` e `CORS_ORIGINS` são variáveis
exclusivas do backend. `SECRET_KEY` deve ser aleatória e real em produção; o
valor de fallback existe somente para desenvolvimento e testes. Não versione
`.env`, credenciais Neon, chaves JWT ou keystores Android.

**61 testes**, rodando em ~5 s, com **75% de cobertura** sobre `backend/` +
`mobile/` — e o núcleo de regra de negócio bem coberto: `geo_service` 100%,
`auth_service` 82%, `apresentacao` 72%. Divididos em:

| arquivo | cobre |
| --- | --- |
| `tests/test_auth.py` | cadastro, login, ciclo do JWT, hash de senha, rotas protegidas |
| `tests/test_geo_service.py` | haversine, simetria, coordenadas inválidas, formatação |
| `tests/test_solicitacoes.py` | criação, filtros, busca, ordenação por distância, emergência no topo, autorização |
| `tests/test_ofertas_mensagens.py` | ofertas, chat, entregas, impacto, ONGs, mapa |
| `tests/test_mobile_views.py` | monta **todas as 17 rotas** do app Flet em memória |

Os testes de interface rodam sem abrir janela e sem servidor: o transporte HTTP
do `ApiClient` é trocado pelo `TestClient` do FastAPI.

---

## `~/estrutura`

```
conecta-comunidade/
├── backend/                    # API FastAPI
│   ├── main.py                 # instância, CORS, routers, metadados do Swagger
│   ├── config.py               # settings via Pydantic Settings (.env)
│   ├── database.py             # engine e sessão (schema fica no Alembic)
│   ├── deps.py                 # get_session, UsuarioAtual, UsuarioOpcional
│   ├── models/                 # SQLModel: usuario, categoria, solicitacao,
│   │                           #   oferta, ong, mensagem, entrega, enums
│   ├── schemas/                # Pydantic v2 (request/response, com exemplos)
│   ├── routers/                # auth, usuarios, categorias, solicitacoes,
│   │                           #   ofertas, ongs, mensagens, entregas, mapa
│   └── services/
│       ├── auth_service.py     # hash bcrypt + emissão/validação de JWT
│       ├── geo_service.py      # haversine e formatação de distância
│       ├── apresentacao.py     # montagem dos schemas (evita N+1)
│       └── seed_service.py     # carga de demonstração
│
├── mobile/                     # aplicativo Flet
│   ├── main.py                 # App, pilha de rotas, navegação inferior
│   ├── api_client.py           # cliente httpx da API
│   ├── theme.py                # paleta, tokens de medida e primitivas visuais
│   ├── state.py                # token, usuário e pilha de navegação
│   ├── components/
│   │   ├── campos.py           # campos de formulário (o padrão único)
│   │   ├── comuns.py           # cabeçalho e cartões
│   │   ├── layout.py           # coluna central (largura máxima no desktop)
│   │   ├── nav_bar.py          # navegação inferior
│   │   ├── fab.py              # botão flutuante de publicar
│   │   └── avatar.py           # foto ou inicial do usuário
│   └── views/                  # uma tela por arquivo (24 rotas)
│
├── tests/                      # pytest (API + renderização das telas)
├── docs/
│   ├── arquitetura.md          # camadas + diagramas Mermaid (fluxo e ER)
│   ├── api.md                  # referência dos endpoints
│   ├── decisoes.md             # registro de decisões técnicas
│   └── assets/                 # logos e capturas de tela
├── alembic/                    # migrations (fonte única do schema)
├── seed.py                     # carga de dados de exemplo
├── requirements.txt            # versões fixadas
├── .env.example
└── LICENSE
```

### Paleta do produto

O app tem identidade própria — a marca VyteTech assina a autoria, não o produto.

| token | hex | uso |
| --- | --- | --- |
| Verde primário | `#2E9E5B` | ações principais |
| Verde escuro | `#1B6B3A` | gradientes e estados pressionados |
| Azul institucional | `#0E2A47` | títulos e textos |
| Fundo claro | `#F5F7F6` | fundo das telas |
| Urgência | `#E23B3B` | alertas e modo emergência |
| Texto secundário | `#6B7B72` | legendas e metadados |

---

## `// documentação`

| documento | conteúdo |
| --- | --- |
| [`docs/arquitetura.md`](docs/arquitetura.md) | Camadas, fluxo de requisição e **diagrama ER** (Mermaid) |
| [`docs/api.md`](docs/api.md) | Endpoints, query params, códigos de status |
| [`docs/decisoes.md`](docs/decisoes.md) | Por que Flet, por que SQLModel, como o JWT é validado, como a distância é calculada |
| `http://127.0.0.1:8000/docs` | Swagger UI interativo (com **Authorize**) |
| `http://127.0.0.1:8000/redoc` | ReDoc |

---

## `// roadmap`

- [ ] Upload real de fotos nas solicitações (hoje o campo aceita URLs)
- [ ] Mapa nativo com `flet-map` (ver decisão `06`)
- [ ] Notificações push para pedidos em emergência no raio do usuário
- [ ] GPS do dispositivo em vez de localidade escolhida no cadastro
- [ ] Login da ONG e chat direto com a instituição
- [ ] Histórico de avaliações por usuário (hoje só ONGs são avaliadas)
- [ ] Deploy: API em container + PostgreSQL, app empacotado com `flet build`

---

## `// autor`

<div align="center">

<img src="docs/assets/vytetech-symbol.svg" alt="VyteTech" width="52" />

Construído por **<span style="color:#22486C">Vyte</span><span style="color:#21BCCE">Tech</span>** — *Tecnologia para negócios.*

**Vitor Yoshii** · Fundador &amp; CEO

[![site](https://img.shields.io/badge/vytetech.com-21BCCE?style=flat-square&labelColor=0C1A22)](https://vytetech.com)
[![github](https://img.shields.io/badge/github-%7Bseu--github%7D-4A6076?style=flat-square&labelColor=0C1A22)](https://github.com/{seu-github})
[![linkedin](https://img.shields.io/badge/linkedin-%7Bseu--linkedin%7D-22486C?style=flat-square&labelColor=0C1A22)](https://linkedin.com/in/{seu-linkedin})

</div>

Licenciado sob **MIT** — ver [`LICENSE`](LICENSE).
