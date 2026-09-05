# `~/docs/assets`

Ativos de marca e mídia da documentação.

## Logos VyteTech — substituir pelos arquivos oficiais

Os SVGs abaixo neste diretório são **placeholders** gerados para o README não
ficar com imagem quebrada. Sobrescreva-os pelos arquivos oficiais mantendo
exatamente os mesmos nomes — o README e os docs já apontam para eles:

| Arquivo | Uso |
| --- | --- |
| `vytetech-symbol.svg` | Símbolo colorido (cabeçalho do README) |
| `vytetech-symbol-white.svg` | Versão branca, obrigatória sobre fundo ciano |

## Regras de uso do logo

- O símbolo colorido **nunca** vai sobre fundo ciano — use a versão branca.
- Não recolorir fora da paleta da marca.
- Não distorcer: escalar sempre proporcionalmente.
- Respiro mínimo de **1x** a largura do símbolo em volta dele.
- Ao embutir o SVG colorido mais de uma vez no mesmo HTML, dar **id único** a
  cada gradiente (`cyGrad1`, `cyGrad2`, ...), senão o segundo herda o primeiro.

## Prints e GIFs do app

Coloque aqui as capturas de tela citadas no README, com estes nomes:

```
tela-splash.png
tela-home.png
tela-explorar.png
tela-detalhe.png
tela-chat.png
tela-mapa.png
tela-ongs.png
tela-perfil.png
demo.gif
```

Para capturar: suba a API, rode `flet run mobile/main.py` e use a janela de
430x900 que o app já abre — a proporção é de celular.

## Paleta VyteTech (documentação)

| Token | Hex |
| --- | --- |
| Cyan | `#21BCCE` |
| Cyan Bright | `#35D2E4` |
| Navy | `#22486C` |
| Ink | `#0C1A22` |
| Void | `#070C14` |
| Signal Green | `#3DDC97` |
| Mist | `#EAF7F9` |
| Slate | `#4A6076` |
