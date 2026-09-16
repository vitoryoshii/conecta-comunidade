"""
Cliente HTTP do aplicativo.

Encapsula todas as chamadas à API do Conecta Comunidade em métodos com nomes de
domínio (`listar_solicitacoes`, `enviar_mensagem`, ...). As views nunca montam
URLs nem cabeçalhos: elas conversam com esta classe.

O token JWT fica guardado na instância e é injetado automaticamente no header
`Authorization` de cada requisição autenticada.
"""

from typing import Any

import httpx

# Timeout curto: se a API não responder, é melhor mostrar o erro na tela do que
# deixar o app travado esperando.
TIMEOUT_SEGUNDOS = 15.0


class ErroApi(Exception):
    """Erro de comunicação com a API, já com uma mensagem pronta para a tela."""

    def __init__(self, mensagem: str, status: int | None = None) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


class ApiClient:
    """Fachada síncrona sobre a API REST."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None
        self._cliente: httpx.Client | None = None

    # A conexão é criada sob demanda: instanciar um `httpx.Client` monta um
    # contexto SSL, o que custa cerca de um segundo. Criar só na primeira
    # requisição deixa a abertura do app instantânea.
    @property
    def _http(self) -> httpx.Client:
        """Cliente HTTP subjacente, criado na primeira utilização."""
        if self._cliente is None:
            self._cliente = httpx.Client(base_url=self.base_url, timeout=TIMEOUT_SEGUNDOS)
        return self._cliente

    @_http.setter
    def _http(self, cliente: httpx.Client) -> None:
        """Permite injetar outro transporte (é o que os testes fazem)."""
        self._cliente = cliente

    # ----------------------------------------------------------------- #
    # Infraestrutura
    # ----------------------------------------------------------------- #
    def definir_token(self, token: str | None) -> None:
        """Guarda (ou limpa) o JWT usado nas rotas autenticadas."""
        self.token = token

    def _headers(self) -> dict[str, str]:
        """Monta os cabeçalhos, incluindo o Bearer quando há sessão ativa."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def _requisitar(
        self,
        metodo: str,
        caminho: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Executa a requisição e traduz falhas em `ErroApi`."""
        try:
            resposta = self._http.request(
                metodo, caminho, params=params, json=json, headers=self._headers()
            )
        except httpx.RequestError as erro:
            raise ErroApi(
                "Não foi possível falar com o servidor. "
                "Confira se a API está no ar em " + self.base_url
            ) from erro

        if resposta.status_code >= 400:
            raise ErroApi(self._mensagem_de_erro(resposta), resposta.status_code)

        if resposta.status_code == 204 or not resposta.content:
            return None
        return resposta.json()

    @staticmethod
    def _mensagem_de_erro(resposta: httpx.Response) -> str:
        """Extrai o `detail` do FastAPI, cobrindo também os erros de validação."""
        try:
            corpo = resposta.json()
        except ValueError:
            return f"Erro {resposta.status_code} ao falar com o servidor."

        detalhe = corpo.get("detail") if isinstance(corpo, dict) else None
        if isinstance(detalhe, str):
            return detalhe
        if isinstance(detalhe, list) and detalhe:
            # Erros 422 do Pydantic vêm como lista de problemas por campo.
            primeiro = detalhe[0]
            campo = ".".join(str(p) for p in primeiro.get("loc", [])[1:]) or "campo"
            return f"{campo}: {primeiro.get('msg', 'valor inválido')}"
        return f"Erro {resposta.status_code} ao falar com o servidor."

    def fechar(self) -> None:
        """Encerra a conexão HTTP (chamado quando o app fecha)."""
        if self._cliente is not None:
            self._cliente.close()
            self._cliente = None

    # ----------------------------------------------------------------- #
    # Autenticação
    # ----------------------------------------------------------------- #
    def registrar(self, dados: dict[str, Any]) -> dict[str, Any]:
        """`POST /auth/register` — cria a conta e já devolve o token."""
        return self._requisitar("POST", "/auth/register", json=dados)

    def login(self, email: str, senha: str) -> dict[str, Any]:
        """`POST /auth/login` — autentica e devolve token + usuário."""
        return self._requisitar("POST", "/auth/login", json={"email": email, "senha": senha})

    def recuperar_senha(self, email: str) -> dict[str, Any]:
        """`POST /auth/recuperar-senha` — pede o link de redefinição."""
        return self._requisitar("POST", "/auth/recuperar-senha", json={"email": email})

    def eu(self) -> dict[str, Any]:
        """`GET /auth/me` — perfil do usuário do token atual."""
        return self._requisitar("GET", "/auth/me")

    def atualizar_perfil(self, dados: dict[str, Any]) -> dict[str, Any]:
        """`PATCH /usuarios/me` — edita os dados do próprio perfil."""
        return self._requisitar("PATCH", "/usuarios/me", json=dados)

    def impacto(self) -> dict[str, Any]:
        """`GET /perfil/impacto` — números da seção "Meu impacto"."""
        return self._requisitar("GET", "/perfil/impacto")

    # ----------------------------------------------------------------- #
    # Localidades (estados e municípios do IBGE)
    # ----------------------------------------------------------------- #
    def listar_estados(self) -> list[dict[str, str]]:
        """`GET /localidades/estados` — as 27 UFs, ordenadas por nome."""
        return self._requisitar("GET", "/localidades/estados")

    def listar_cidades(self, sigla: str) -> list[dict[str, Any]]:
        """`GET /localidades/estados/{sigla}/cidades` — municípios da UF.

        Cada item traz `nome`, `lat` e `lng` (coordenadas da sede).
        """
        return self._requisitar("GET", f"/localidades/estados/{sigla}/cidades")

    # ----------------------------------------------------------------- #
    # Categorias
    # ----------------------------------------------------------------- #
    def listar_categorias(self) -> list[dict[str, Any]]:
        """`GET /categorias` — grade de categorias da Home."""
        return self._requisitar("GET", "/categorias")

    # ----------------------------------------------------------------- #
    # Solicitações
    # ----------------------------------------------------------------- #
    def listar_solicitacoes(self, **filtros: Any) -> list[dict[str, Any]]:
        """`GET /solicitacoes` — aceita todos os filtros da API."""
        return self._requisitar("GET", "/solicitacoes", params=self._limpar(filtros))

    def obter_solicitacao(
        self, solicitacao_id: int, lat: float | None = None, long: float | None = None
    ) -> dict[str, Any]:
        """`GET /solicitacoes/{id}` — detalhe de um pedido."""
        return self._requisitar(
            "GET", f"/solicitacoes/{solicitacao_id}", params=self._limpar({"lat": lat, "long": long})
        )

    def criar_solicitacao(self, dados: dict[str, Any]) -> dict[str, Any]:
        """`POST /solicitacoes` — publica um novo pedido."""
        return self._requisitar("POST", "/solicitacoes", json=dados)

    def atualizar_solicitacao(self, solicitacao_id: int, dados: dict[str, Any]) -> dict[str, Any]:
        """`PATCH /solicitacoes/{id}` — muda status ou conteúdo do pedido."""
        return self._requisitar("PATCH", f"/solicitacoes/{solicitacao_id}", json=dados)

    # ----------------------------------------------------------------- #
    # Ofertas
    # ----------------------------------------------------------------- #
    def listar_ofertas(self, **filtros: Any) -> list[dict[str, Any]]:
        """`GET /ofertas` — ofertas disponíveis, com filtros."""
        return self._requisitar("GET", "/ofertas", params=self._limpar(filtros))

    def criar_oferta(self, dados: dict[str, Any]) -> dict[str, Any]:
        """`POST /ofertas` — envia a proposta da tela *Quero ajudar*."""
        return self._requisitar("POST", "/ofertas", json=dados)

    # ----------------------------------------------------------------- #
    # ONGs
    # ----------------------------------------------------------------- #
    def listar_ongs(self, **filtros: Any) -> list[dict[str, Any]]:
        """`GET /ongs` — instituições ordenadas por proximidade."""
        return self._requisitar("GET", "/ongs", params=self._limpar(filtros))

    def obter_ong(
        self, ong_id: int, lat: float | None = None, long: float | None = None
    ) -> dict[str, Any]:
        """`GET /ongs/{id}` — perfil completo da instituição."""
        return self._requisitar(
            "GET", f"/ongs/{ong_id}", params=self._limpar({"lat": lat, "long": long})
        )

    def avaliar_ong(self, ong_id: int, nota: int) -> dict[str, Any]:
        """`POST /ongs/{id}/avaliar` — registra uma nota de 1 a 5."""
        return self._requisitar("POST", f"/ongs/{ong_id}/avaliar", json={"nota": nota})

    # ----------------------------------------------------------------- #
    # Mensagens e entregas
    # ----------------------------------------------------------------- #
    def listar_conversas(self) -> list[dict[str, Any]]:
        """`GET /mensagens/conversas` — aba Mensagens."""
        return self._requisitar("GET", "/mensagens/conversas")

    def listar_mensagens(self, com: int, solicitacao_id: int | None = None) -> list[dict[str, Any]]:
        """`GET /mensagens` — histórico do chat com uma pessoa."""
        return self._requisitar(
            "GET", "/mensagens", params=self._limpar({"com": com, "solicitacao_id": solicitacao_id})
        )

    def enviar_mensagem(
        self, destinatario_id: int, texto: str, solicitacao_id: int | None = None
    ) -> dict[str, Any]:
        """`POST /mensagens` — envia uma nova bolha no chat."""
        return self._requisitar(
            "POST",
            "/mensagens",
            json={
                "destinatario_id": destinatario_id,
                "texto": texto,
                "solicitacao_id": solicitacao_id,
            },
        )

    def listar_entregas(self, **filtros: Any) -> list[dict[str, Any]]:
        """`GET /entregas` — agendamentos do usuário logado."""
        return self._requisitar("GET", "/entregas", params=self._limpar(filtros))

    def criar_entrega(self, dados: dict[str, Any]) -> dict[str, Any]:
        """`POST /entregas` — agenda o encontro combinado no chat."""
        return self._requisitar("POST", "/entregas", json=dados)

    def atualizar_entrega(self, entrega_id: int, dados: dict[str, Any]) -> dict[str, Any]:
        """`PATCH /entregas/{id}` — confirma, reagenda ou cancela."""
        return self._requisitar("PATCH", f"/entregas/{entrega_id}", json=dados)

    # ----------------------------------------------------------------- #
    # Mapa
    # ----------------------------------------------------------------- #
    def pontos_do_mapa(self, **filtros: Any) -> dict[str, Any]:
        """`GET /mapa` — pins e contagem por tipo."""
        return self._requisitar("GET", "/mapa", params=self._limpar(filtros))

    # ----------------------------------------------------------------- #
    # Utilitários
    # ----------------------------------------------------------------- #
    @staticmethod
    def _limpar(parametros: dict[str, Any]) -> dict[str, Any]:
        """Remove chaves com valor `None` para não poluir a query string."""
        return {chave: valor for chave, valor in parametros.items() if valor is not None}
