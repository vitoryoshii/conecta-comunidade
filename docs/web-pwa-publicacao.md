# Web Mobile / PWA — publicação independente

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
4. Publique preview com `vercel --cwd build/web` e, após aprovação,
   `vercel --cwd build/web --prod`.

O `vercel.json` do artefato aplica cache longo aos recursos versionados, evita
cache do HTML inicial e disponibiliza fallback SPA. A PWA usa rotas hash, então
o fallback é adicional e não depende da API.

## CORS e segurança

No estado atual a API aceita CORS `*`, suficiente para Bearer token sem cookies.
Antes de expor um domínio definitivo, por autorização separada, restrinja
`CORS_ORIGINS` da API à origem HTTPS exata da PWA. Não altere essa configuração
no projeto frontend.

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
