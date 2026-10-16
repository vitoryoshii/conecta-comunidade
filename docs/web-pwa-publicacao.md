# Web Mobile / PWA — publicação independente

## Produção atual

| Item | Valor |
| --- | --- |
| URL | <https://conecta-comunidade-web.vercel.app> |
| Projeto | `conecta-comunidade-web` |
| Escopo Vercel | `vitor-yoshii-s-projects` |
| Deployment homologado | `dpl_GgdhJuaZ1muXTF5gu4gSoZaYfM6p` |

O frontend é um projeto Vercel separado da API. Não publique a raiz deste
repositório no projeto Web: ela contém a configuração do backend.

## Escopo

Esta PWA é estática: Flet e Python/Pyodide executam no navegador e consomem a
API FastAPI HTTPS existente. Publique-a em um projeto Vercel novo; não reuse o
projeto Vercel da API.

## Build de homologação

```powershell
.\scripts\build_web_pwa.ps1 -OutputDir build\web
```

O resultado é `build/web`. O script usa uma allowlist e inclui o `vercel.json`
do frontend no artefato. Não acrescente `.env`, chaves ou o repositório inteiro.

## Projeto Vercel separado

1. Crie um projeto Vercel novo sem conectá-lo ao projeto atual da API.
2. Não defina Build Command nem Output Directory: o artefato já está pronto.
3. No build local, configure `CONECTA_API_BASE_URL` para a URL HTTPS da API,
   sem barra final. Em produção ela é `https://conecta-comunidade-wheat.vercel.app`.
4. Confirme conta, escopo e Project ID antes do deploy. Com um perfil Vercel
   isolado, publique somente o diretório do artefato:

```powershell
npx vercel deploy --cwd build\web --project <project-id> --scope <scope> --prod --yes
```

5. Registre o ID do deployment e valide o domínio definitivo antes de descartar
   o artefato local. A Vercel preserva deployments anteriores para rollback.

O `vercel.json` do artefato aplica cache longo aos recursos versionados, evita
cache do HTML inicial e disponibiliza fallback SPA. A PWA usa rotas hash, então
o fallback é adicional e não depende da API.

## CORS e segurança

Antes de um domínio novo, a API precisa receber em `CORS_ORIGINS` as origens
HTTPS exatas da PWA, separadas por vírgula. Exemplo:

```text
CORS_ORIGINS=https://conecta-web-preview.exemplo.vercel.app,https://conecta.exemplo.com
```

A API não usa cookie de sessão: o JWT viaja no header `Authorization`. Por
isso CORS opera com `allow_credentials=False`; não use wildcard. Essa mudança
é da API e requer autorização/deploy separado do frontend. Um build ou deploy
Web não autoriza mudança de CORS, Neon, migrations ou variáveis da API.

## Checklist de validação

- `index.html`, manifest, favicon e todos os ícones respondem HTTP 200.
- `python-worker.js`, `pyodide/pyodide.mjs` e `assets/app/app.zip` respondem HTTP 200.
- O `app.zip` contém `assets/legal/termos-de-uso.md` e
  `assets/legal/politica-de-privacidade.md`.
- A tela de carregamento não mostra marca Flet e a Splash/Home do produto aparecem.
- Teste cadastro, Termos, Política, retorno e navegação em sessão limpa.
- Diferencie cache/service worker antigo de regressão no novo artefato.

No navegador o JWT fica apenas em memória. Reabrir/recarregar a aba pede login,
evitando token persistido em aparelho compartilhado. Apps instalados preservam
o comportamento próprio.

## Limitação conhecida

Avatar não é enviado pela PWA: a API não possui endpoint autenticado de upload
nem storage público, e o navegador não entrega caminho local gravável ao fluxo
existente. É necessário trabalho de backend aprovado antes de habilitá-lo.

## Plano gratuito

Uma PWA estática pode ficar no plano gratuito, sujeita aos limites e políticas
vigentes da Vercel. Pyodide é embutido para não depender de CDN externo, o que
aumenta tamanho de upload e a primeira instalação.
