# API

`// referência dos endpoints` · Conecta Comunidade · por **VyteTech**

A documentação **interativa** (a fonte da verdade) é gerada pelo próprio FastAPI:

| Interface | URL |
| --- | --- |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |
| Esquema OpenAPI | `http://127.0.0.1:8000/openapi.json` |

Este arquivo é o resumo de bolso.

---

## `// autenticação`

O fluxo é **Bearer JWT**:

```bash
# 1. entrar
$ curl -X POST http://127.0.0.1:8000/auth/login \
       -H "Content-Type: application/json" \
       -d '{"email":"ana@conecta.com","senha":"senha123"}'

# 2. usar o access_token devolvido
$ curl http://127.0.0.1:8000/auth/me \
       -H "Authorization: Bearer <access_token>"
```

No Swagger, clique em **Authorize** e cole apenas o token.

- Token ausente/inválido/expirado em rota protegida → **401**
- Tentativa de editar recurso de outra pessoa → **403**
- Validade padrão do token: **7 dias** (`ACCESS_TOKEN_EXPIRE_MINUTES`)

---

## `// endpoints`

Legenda de auth: `—` pública · `opcional` usa o token se houver (para calcular
distância) · **`JWT`** exige token.

### Autenticação

| Método | Rota | Auth | Descrição |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | — | Cria a conta e já devolve o token |
| `POST` | `/auth/login` | — | Autentica e devolve `access_token` + usuário |
| `GET` | `/auth/me` | **JWT** | Perfil do dono do token |

### Usuários e impacto

| Método | Rota | Auth | Descrição |
| --- | --- | --- | --- |
| `GET` | `/usuarios/{id}` | — | Perfil público |
| `PATCH` | `/usuarios/me` | **JWT** | Edita nome, cidade, coordenadas e avatar |
| `GET` | `/perfil/impacto` | **JWT** | Números de *Meu impacto* |

### Categorias

| Método | Rota | Auth | Descrição |
| --- | --- | --- | --- |
| `GET` | `/categorias` | — | Categorias com o nome do ícone usado no app |

### Solicitações

| Método | Rota | Auth | Descrição |
| --- | --- | --- | --- |
| `GET` | `/solicitacoes` | opcional | Lista com filtros e ordenação |
| `GET` | `/solicitacoes/{id}` | opcional | Detalhe com distância e autor |
| `POST` | `/solicitacoes` | **JWT** | Publica um pedido de ajuda |
| `PATCH` | `/solicitacoes/{id}` | **JWT** | Edita (somente o autor) |

Query params de `GET /solicitacoes`:

| Parâmetro | Tipo | Efeito |
| --- | --- | --- |
| `categoria_id` | `int` | Filtra pela categoria |
| `urgencia` | `baixa \| media \| alta` | Filtra pelo nível de urgência |
| `status` | `ativa \| em_andamento \| concluida` | Filtra pelo estado do pedido |
| `emergencia` | `bool` | Somente pedidos em modo emergência |
| `busca` | `str` | Procura no título e na descrição |
| `usuario_id` | `int` | Somente pedidos de um autor (aba *Minhas solicitações*) |
| `lat` / `long` | `float` | Origem do cálculo de distância |
| `ordenar_por` | `distancia \| recentes \| urgencia` | Critério de ordenação |
| `limite` | `int` (1–200) | Máximo de itens |

> Independentemente da ordenação escolhida, os pedidos com `emergencia = true`
> são sempre fixados no topo.

### Ofertas

| Método | Rota | Auth | Descrição |
| --- | --- | --- | --- |
| `GET` | `/ofertas` | opcional | Filtros: `categoria_id`, `tipo_ajuda`, `status`, `solicitacao_id`, `usuario_id`, `busca`, `lat`/`long`, `ordenar_por` |
| `POST` | `/ofertas` | **JWT** | Envia a proposta da tela *Quero ajudar* |

`POST /ofertas` com `solicitacao_id` produz três efeitos em uma chamada:
move o pedido para `em_andamento`, incrementa `acoes_voluntario` de quem ajuda
e, se vier `mensagem`, cria a primeira fala do chat.

### ONGs

| Método | Rota | Auth | Descrição |
| --- | --- | --- | --- |
| `GET` | `/ongs` | opcional | Busca, filtro `somente_verificadas`, ordenação por distância |
| `GET` | `/ongs/{id}` | opcional | Perfil com recursos disponíveis |
| `POST` | `/ongs/{id}/avaliar` | **JWT** | Nota de 1 a 5; recalcula a média |

### Mensagens

| Método | Rota | Auth | Descrição |
| --- | --- | --- | --- |
| `GET` | `/mensagens/conversas` | **JWT** | Lista de conversas com última fala e não lidas |
| `GET` | `/mensagens?com={id}` | **JWT** | Histórico do chat (marca recebidas como lidas) |
| `POST` | `/mensagens` | **JWT** | Envia uma mensagem |

### Entregas

| Método | Rota | Auth | Descrição |
| --- | --- | --- | --- |
| `GET` | `/entregas` | **JWT** | Agendamentos em que o usuário participa |
| `POST` | `/entregas` | **JWT** | Agenda o encontro combinado no chat |
| `PATCH` | `/entregas/{id}` | **JWT** | Reagenda, confirma (`realizada`) ou cancela |

Marcar como `realizada` conclui a solicitação e incrementa
`solicitacoes_atendidas` (doador) e `doacoes_recebidas` (solicitante).

### Mapa

| Método | Rota | Auth | Descrição |
| --- | --- | --- | --- |
| `GET` | `/mapa` | opcional | Pins unificados + contagem por tipo |

Params: `tipos` (repetível: `ajuda`, `oferecendo`, `ong`, `ponto_retirada`),
`lat`/`long`, `raio_km`.

```bash
$ curl "http://127.0.0.1:8000/mapa?tipos=ajuda&tipos=ong&lat=-23.55&long=-46.63"
```

---

## `// campos derivados`

Alguns campos das respostas **não existem no banco** — são calculados a cada
requisição por `services/apresentacao.py` e `services/geo_service.py`:

| Campo | Onde aparece | Como é obtido |
| --- | --- | --- |
| `distancia_km` | solicitações, ofertas, ONGs, pins | haversine (`geopy`) entre o usuário e o recurso |
| `distancia_formatada` | idem | `"350 m"` abaixo de 1 km, `"4,2 km"` acima |
| `tempo_publicacao` | solicitações, ofertas | `"agora"`, `"há 2 h"`, `"há 3 d"` |
| `categoria_nome` / `categoria_icone` | solicitações, ofertas | join em memória com `categoria` |
| `autor_nome` / `autor_avatar` | solicitações, ofertas | carregamento em lote dos autores |

Quando o usuário não tem coordenada, `distancia_km` volta `null` e
`distancia_formatada` volta `"--"` — a interface simplesmente omite o valor.

---

## `// códigos de status`

| Código | Quando acontece |
| --- | --- |
| `200` | Leitura ou atualização bem-sucedida |
| `201` | Recurso criado (cadastro, solicitação, oferta, mensagem, entrega) |
| `401` | Sem token, token inválido ou expirado |
| `403` | Token válido, mas sem permissão sobre o recurso |
| `404` | Recurso inexistente |
| `409` | E-mail já cadastrado |
| `422` | Payload inválido (validação do Pydantic) ou regra de domínio violada |

---

`Construído por` **VyteTech** — *Tecnologia para negócios.*
