# Arquitetura

`// visão geral do sistema` · Conecta Comunidade · por **VyteTech**

---

## `// resumo`

O projeto é uma aplicação de **duas camadas**, ambas escritas em Python:

| Camada | Papel | Tecnologia |
| --- | --- | --- |
| `mobile/` | Interface, navegação e estado da sessão | `flet` (Flutter renderizado via Python) |
| `backend/` | Regras de negócio, persistência e autenticação | `fastapi` + `sqlmodel` |

Elas se comunicam **apenas por HTTP/JSON**. O app não conhece o banco, e o
backend não conhece a interface — o contrato entre os dois é o OpenAPI gerado
automaticamente pelo FastAPI em `/docs`.

---

## `// fluxo de uma requisição`

```mermaid
flowchart LR
    subgraph MOBILE["mobile/ — app Flet"]
        V["views/<br/>13 telas"]
        S["state.py<br/>token + pilha de rotas"]
        A["api_client.py<br/>httpx"]
        V --> S
        V --> A
    end

    subgraph BACKEND["backend/ — API FastAPI"]
        R["routers/<br/>auth · solicitacoes · ofertas<br/>ongs · mensagens · entregas · mapa"]
        D["deps.py<br/>get_session · get_current_user"]
        SV["services/<br/>auth · geo · apresentacao · seed"]
        SC["schemas/<br/>Pydantic v2"]
        M["models/<br/>SQLModel"]
        R --> D
        R --> SV
        R --> SC
        SV --> M
        SC --> M
    end

    DB[("SQLite / PostgreSQL")]

    A -- "HTTP + JSON<br/>Bearer JWT" --> R
    M -- "SQLAlchemy" --> DB
    R -- "resposta JSON<br/>com distancia_km" --> A
```

### Passo a passo de um "ver pedidos próximos"

1. A view `home.py` chama `app.api.listar_solicitacoes(lat=..., long=...)`.
2. `api_client.py` monta `GET /solicitacoes?...` e injeta `Authorization: Bearer <jwt>`.
3. `deps.get_current_user_optional` resolve o usuário a partir do token (ou devolve `None`, no modo visitante).
4. O router filtra no banco por categoria/urgência/status.
5. `services/apresentacao.py` enriquece cada registro: nome da categoria, autor, `tempo_publicacao`.
6. `services/geo_service.py` calcula a distância haversine e formata em km.
7. A lista é ordenada — **emergências primeiro**, depois por proximidade.
8. O app recebe o JSON pronto e só desenha os cartões.

> A ordenação por distância acontece **em Python, após a consulta**, porque o
> SQLite não tem função haversine nativa. Para volumes maiores, o caminho
> natural é migrar para PostgreSQL + PostGIS e empurrar o cálculo para o SQL.

---

## `// modelo de dados`

```mermaid
erDiagram
    USUARIO ||--o{ SOLICITACAO : "publica"
    USUARIO ||--o{ OFERTA : "oferece"
    USUARIO ||--o{ MENSAGEM : "envia"
    USUARIO ||--o{ ENTREGA : "é doador em"
    CATEGORIA ||--o{ SOLICITACAO : "classifica"
    CATEGORIA ||--o{ OFERTA : "classifica"
    SOLICITACAO ||--o{ OFERTA : "recebe propostas"
    SOLICITACAO ||--o{ MENSAGEM : "dá contexto a"
    SOLICITACAO ||--o{ ENTREGA : "é atendida por"

    USUARIO {
        int id PK
        string nome
        string email UK
        string senha_hash
        enum tipo "solicitante|doador|voluntario|ong"
        string cidade
        float latitude
        float longitude
        string avatar_url
        datetime criado_em
        int solicitacoes_atendidas
        int doacoes_recebidas
        int acoes_voluntario
    }

    CATEGORIA {
        int id PK
        string nome UK
        string icone
    }

    SOLICITACAO {
        int id PK
        int usuario_id FK
        int categoria_id FK
        string titulo
        string descricao
        string quantidade
        enum urgencia "baixa|media|alta"
        enum status "ativa|em_andamento|concluida"
        int pessoas_beneficiadas
        float latitude
        float longitude
        string endereco
        json fotos
        bool emergencia
        datetime criada_em
    }

    OFERTA {
        int id PK
        int usuario_id FK
        int categoria_id FK
        int solicitacao_id FK "opcional"
        string titulo
        string descricao
        enum tipo_ajuda "tenho_item|posso_entregar|ponto_retirada"
        enum status "disponivel|em_andamento|concluida|cancelada"
        float latitude
        float longitude
        string endereco
        datetime criada_em
    }

    ONG {
        int id PK
        string nome
        string descricao
        float avaliacao
        int total_avaliacoes
        bool verificada
        json recursos_disponiveis
        string endereco
        float latitude
        float longitude
        string avatar_url
    }

    MENSAGEM {
        int id PK
        int remetente_id FK
        int destinatario_id FK
        int solicitacao_id FK "opcional"
        string texto
        datetime criada_em
        bool lida
    }

    ENTREGA {
        int id PK
        int solicitacao_id FK
        int doador_id FK
        string data
        string hora
        string local
        enum status "agendada|realizada|cancelada"
    }
```

**ONG** aparece sem relacionamento no diagrama porque, nesta versão, instituições
são um catálogo público consultado por proximidade — não têm ainda vínculo
transacional com pedidos. Ver `docs/decisoes.md`.

---

## `// camadas do backend`

```
routers/     → HTTP: rotas, query params, códigos de status
  ↓
deps.py      → sessão de banco + usuário autenticado
  ↓
services/    → regra de negócio pura (JWT, haversine, montagem de resposta)
  ↓
models/      → tabelas SQLModel
  ↓
database.py  → engine e sessão
```

Cada camada só conhece a de baixo. `services/geo_service.py`, por exemplo, não
importa nada do FastAPI — é uma função pura, o que o torna trivial de testar
(ver `tests/test_geo_service.py`).

## `// camadas do mobile`

```
views/           → 13 telas, cada uma com construir(app) -> ft.Control
  ↓
components/      → cartões, cabeçalho e navegação inferior reutilizáveis
  ↓
theme.py         → paleta e primitivas visuais
  ↓
state.py         → token, usuário e pilha de rotas
  ↓
api_client.py    → única porta de saída para a rede
```

### Navegação

O app mantém a **própria pilha de rotas** dentro do `AppState`, em vez de usar
o roteamento por URL do Flet:

```mermaid
stateDiagram-v2
    [*] --> Splash
    Splash --> Login
    Splash --> Cadastro
    Splash --> Home : visitante
    Login --> Home
    Cadastro --> Home
    Home --> Explorar : aba
    Home --> Publicar : aba (+)
    Home --> Mensagens : aba
    Home --> Perfil : aba
    Explorar --> DetalheSolicitacao
    DetalheSolicitacao --> QueroAjudar
    QueroAjudar --> Chat : cria oferta
    Mensagens --> Chat
    Chat --> Chat : agenda entrega
    Home --> Mapa
    Mapa --> DetalheSolicitacao
    Mapa --> PerfilONG
    Perfil --> MinhasSolicitacoes
    Perfil --> [*] : sair
```

As cinco abas da navegação inferior **reiniciam** a pilha; qualquer outra tela
**empilha**, e o botão voltar desempilha. Isso mantém o comportamento previsível
em qualquer profundidade.

---

## `// segurança`

- Senhas nunca são gravadas em texto puro: `passlib` + `bcrypt` (salt automático).
- O login devolve um JWT HS256 com o id do usuário no claim `sub` e validade de 7 dias.
- Toda rota de escrita depende de `UsuarioAtual`, que rejeita token ausente, inválido ou expirado com **401**.
- Rotas de leitura usam `UsuarioOpcional`: funcionam para visitantes, mas sem distância personalizada.
- Autorização por dono: só o autor edita a própria solicitação (**403** caso contrário).
- Nenhum segredo versionado — tudo em `.env`, ignorado pelo Git.

---

`Construído por` **VyteTech** — *Tecnologia para negócios.*
