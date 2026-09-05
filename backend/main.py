"""
Ponto de entrada da API do Conecta Comunidade.

Sobe com:

    uvicorn backend.main:app --reload

Documentação interativa em http://127.0.0.1:8000/docs (Swagger UI) e
http://127.0.0.1:8000/redoc (ReDoc).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import init_db
from backend.routers import (
    auth,
    categorias,
    entregas,
    mapa,
    mensagens,
    ofertas,
    ongs,
    solicitacoes,
    usuarios,
)

# Descrição exibida no topo do Swagger — funciona como um resumo do projeto.
DESCRICAO = """
Plataforma que conecta **quem precisa de ajuda** a **quem pode ajudar**:
doações, voluntariado e emergências, sempre organizados por proximidade.

### Como usar esta documentação

1. Crie uma conta em `POST /auth/register` (ou entre em `POST /auth/login`).
2. Copie o `access_token` da resposta.
3. Clique em **Authorize** aqui no topo e cole o token.
4. As rotas de escrita passam a funcionar autenticadas.

### Conceitos

* **Distância** — todo recurso georreferenciado aceita `lat`/`long` e devolve
  `distancia_km` calculada por haversine (biblioteca `geopy`).
* **Modo emergência** — solicitações com `emergencia = true` são fixadas no topo
  das listagens e destacadas no mapa.
* **Impacto** — cada conclusão de entrega alimenta os contadores exibidos em
  `GET /perfil/impacto`.
"""

# Ordem das seções na Swagger UI, com uma linha de contexto em cada uma.
TAGS_METADATA = [
    {"name": "Autenticação", "description": "Cadastro, login e identificação via JWT."},
    {"name": "Usuários", "description": "Perfil público, edição e números de *Meu impacto*."},
    {"name": "Categorias", "description": "Tipos de necessidade usados nos filtros e na Home."},
    {"name": "Solicitações", "description": "Pedidos de ajuda, com filtros e ordenação por distância."},
    {"name": "Ofertas", "description": "Propostas de quem tem item, pode entregar ou oferece retirada."},
    {"name": "ONGs", "description": "Instituições parceiras, avaliações e selo de verificação."},
    {"name": "Mensagens", "description": "Chat entre usuários e lista de conversas."},
    {"name": "Entregas", "description": "Agendamentos combinados dentro do chat."},
    {"name": "Mapa", "description": "Pins de solicitações, ofertas, pontos de retirada e ONGs."},
]


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Cria as tabelas na subida da aplicação.

    Em um cenário real o schema viria exclusivamente do Alembic; aqui o
    `init_db` garante que o projeto rode logo após o clone, sem passos extras.
    """
    init_db()
    yield


app = FastAPI(
    title=settings.app_nome,
    version=settings.app_versao,
    description=DESCRICAO,
    openapi_tags=TAGS_METADATA,
    contact={"name": "VyteTech", "url": "https://vytetech.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    lifespan=ciclo_de_vida,
)

# O app Flet roda em outra origem (desktop/web), então o CORS precisa liberá-la.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.lista_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Registro dos routers --------------------------------------------------
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(usuarios.router_perfil)
app.include_router(categorias.router)
app.include_router(solicitacoes.router)
app.include_router(ofertas.router)
app.include_router(ongs.router)
app.include_router(mensagens.router)
app.include_router(entregas.router)
app.include_router(mapa.router)


@app.get("/", tags=["Autenticação"], summary="Healthcheck", include_in_schema=False)
def raiz() -> dict[str, str]:
    """Endpoint simples para conferir se a API está no ar."""
    return {
        "aplicacao": settings.app_nome,
        "versao": settings.app_versao,
        "documentacao": "/docs",
        "status": "no ar",
    }
