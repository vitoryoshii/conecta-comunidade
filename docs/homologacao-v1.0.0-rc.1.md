# Homologação `v1.0.0-rc.1`

Registro operacional da entrega final de homologação do Conecta Comunidade.
Não substitui revisão jurídica, publicação oficial Android ou gestão de
credenciais.

## Web/PWA

| Item | Evidência |
| --- | --- |
| URL | <https://conecta-comunidade-web.vercel.app> |
| Projeto Vercel | `conecta-comunidade-web` |
| Deployment | `dpl_GgdhJuaZ1muXTF5gu4gSoZaYfM6p` |
| Estado | `READY` |
| `app.zip` SHA-256 | `B22D001F764BD677CAB1608F65F314AFE4CCF8F047AF53CA10484B5A020DC42A` |

O artefato publicado contém favicon, ícones 16/32, Apple Touch Icon, PWA
192/512, variantes maskable, `python-worker.js`, Pyodide local e os dois
Markdown legais dentro de `assets/app/app.zip`.

O splash HTML preserva os elementos esperados por `removeSplashFromWeb()` do
Flet, com apresentação neutra e sem logotipo padrão do framework.

## Android

| Item | Evidência |
| --- | --- |
| APK de homologação | `conecta-comunidade-homologacao.apk` |
| SHA-256 | `E4F22FC4638390F7FEAE915DC39A3AA173063ADA244A184B9B7E68CB63A51E7E` |
| Tamanho | 140.618.703 bytes |
| Assinatura | `C=US, O=Android, CN=Android Debug` |
| Package ID | `br.edu.conectacomunidade.app` |

O APK foi produzido pelo pipeline de homologação, passou no scanner do projeto
e contém os documentos legais. O ícone adaptativo oficial usa fundo `#0E6B42`.

**Limite de distribuição:** uma assinatura Android Debug é aceitável apenas
para homologação manual. Gere e valide uma assinatura de release antes de
distribuir como versão oficial.

## Git e qualidade

- Tag: `v1.0.0-rc.1`.
- Correção legal: PR #3, merge commit `5805263`.
- Testes automatizados e `git diff --check` aprovados no gate final.
- Scanner do artefato Web e do APK aprovado; nenhum segredo ou keystore foi
  incluído no repositório ou nos artefatos de entrega.

## Itens que exigem revisão humana

- Conteúdo jurídico sobre exclusão/anonimização, CPF, retenção, compartilhamento
  e comunicação de alterações deve ser confirmado com a implementação e revisão
  jurídica antes de lançamento público.
- O APK de homologação deve ser publicado somente como pre-release de teste.
