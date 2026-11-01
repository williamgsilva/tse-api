# 0006 — Desenhar os mapas com as malhas do IBGE e d3-geo

- **Status:** Aceito
- **Data:** 2026-10-30
- **Decisores:** @williamgsilva

## Contexto

O painel ganhou um mapa interativo: Brasil por estado, região e cada estado por município, coloridos pelo
partido mais votado ou pelo comparecimento. Para isso são necessários os limites geográficos e uma forma de
desenhá-los, ligando cada área ao resultado do TSE.

## Opções consideradas

1. **Biblioteca de mapas com tiles (Leaflet, MapLibre)**: oferece zoom e base cartográfica, mas é pesada
   (centenas de KB), depende de servidor de tiles e é desnecessária para um mapa coroplético.
2. **GeoJSON embutido no build do frontend**: funciona offline, mas aumenta o bundle (o Brasil por município
   passa de 3 MB) e fica desatualizado se os limites mudarem.
3. **API de malhas do IBGE servida pela própria API (com cache em disco) + `d3-geo` no navegador**: a fonte é
   oficial, o mapa de cada estado só é baixado quando é aberto e o `d3-geo` (licença ISC, ~30 KB) só projeta
   o GeoJSON em caminhos SVG.

## Decisão

Opção 3.

- O módulo `geography` busca `paises/BR` (por UF) e `estados/{código IBGE}` (por município) na qualidade
  mínima, normaliza as feições para `{codigo_ibge}` (mais `uf` e `regiao` nas UFs), arredonda as coordenadas
  em 4 casas decimais e guarda em `data/cache/ibge/`. As respostas saem com `Cache-Control` de um dia.
- A ligação com o TSE é o código IBGE, que o TSE publica para cada município (`/municipios`).
- Os resultados para colorir vêm de `/resultados/{uf}/{cargo}/subdivisoes`, que consulta cada UF ou município
  em paralelo (limitado pelo cliente do TSE) e devolve os primeiros colocados.
- O frontend inverte o sentido dos anéis antes de projetar: o `d3-geo` (esférico) espera o oposto da RFC 7946.

## Consequências

- **Positivas:** sem dependência pesada nem tiles; mapa acessível (cada área é um botão com rótulo); as cores
  seguem a ordem nacional dos partidos e não mudam ao navegar entre níveis.
- **Negativas / trade-offs:** a primeira consulta de um estado grande faz uma requisição ao TSE por
  município (~20 s em SP; depois fica em cache); o mapa do exterior não existe.
- **O que precisa ser feito:** se a carga no TSE incomodar, pré-calcular as subdivisões na importação da base
  local.
