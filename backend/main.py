"""
Ponto de entrada da API do Conecta Comunidade.

Sobe com:

    uvicorn backend.main:app --reload

O schema do banco vem exclusivamente do Alembic — rode `alembic upgrade head`
antes de subir a API pela primeira vez (e depois de cada `git pull` que traga
migrations novas).

Documentação interativa em http://127.0.0.1:8000/docs (Swagger UI) e
http://127.0.0.1:8000/redoc (ReDoc).
"""

from fastapi import FastAPI
from backend.config import settings
from backend.cors import configurar_cors
from backend.routers import (
    auth,
    categorias,
    entregas,
    favoritos,
    localidades,
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
    {"name": "Localidades", "description": "Estados e municípios do IBGE usados no cadastro."},
    {"name": "Solicitações", "description": "Pedidos de ajuda, com filtros e ordenação por distância."},
    {"name": "Ofertas", "description": "Propostas de quem tem item, pode entregar ou oferece retirada."},
    {"name": "ONGs", "description": "Instituições parceiras, avaliações e selo de verificação."},
    {"name": "Mensagens", "description": "Chat entre usuários e lista de conversas."},
    {"name": "Entregas", "description": "Agendamentos combinados dentro do chat."},
    {"name": "Mapa", "description": "Pins de solicitações, ofertas, pontos de retirada e ONGs."},
]


app = FastAPI(
    title=settings.app_nome,
    version=settings.app_versao,
    description=DESCRICAO,
    openapi_tags=TAGS_METADATA,
    contact={"name": "VyteTech", "url": "https://vytetech.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

# Android/desktop chamam a API diretamente; somente clientes no navegador usam
# CORS. O JWT é enviado em Authorization, sem cookie, portanto credenciais de
# origem cruzada não são necessárias.
configurar_cors(app, settings.lista_cors_origins)

# --- Registro dos routers --------------------------------------------------
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(usuarios.router_perfil)
app.include_router(categorias.router)
app.include_router(localidades.router)
app.include_router(solicitacoes.router)
app.include_router(ofertas.router)
app.include_router(ongs.router)
app.include_router(mensagens.router)
app.include_router(entregas.router)
app.include_router(mapa.router)
app.include_router(favoritos.router)


@app.get("/", tags=["Autenticação"], summary="Healthcheck", include_in_schema=False)
def raiz() -> dict[str, str]:
    """Endpoint simples para conferir se a API está no ar."""
    return {
        "aplicacao": settings.app_nome,
        "versao": settings.app_versao,
        "documentacao": "/docs",
        "status": "no ar",
    }
