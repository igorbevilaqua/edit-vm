# Fontes de material para o Edit VM

Onde buscar cada peça da edição, por ordem de preferência. Tudo foi testado em out/2026, salvo onde está marcado.

Regra que vale para tudo: **material real primeiro**. A ordem é a seguinte:

1. o que o usuário mandou;
2. foto ou vídeo real da coisa citada;
3. motion graphic feito em código;
4. ilustração gerada por IA, só como metáfora (seção 4).

Nunca use IA para fingir uma foto real de um evento real.

---

## 1. Manchetes (faixa do meio)

A manchete serve para **provar** o que está sendo dito. O texto tem de ser exatamente o publicado, de um veículo real e com data.

| Fonte | Como | Observações |
|---|---|---|
| **Google Notícias RSS** (principal) | `python3 scripts/manchetes.py "termo" --dias 30` | Sem chave, edição BR (`hl=pt-BR&gl=BR&ceid=BR:pt-419`). Devolve título, veículo, site, data e link. Não tem documentação oficial: se quebrar, use o GDELT. |
| **GDELT DOC 2.0** (reserva) | `https://api.gdeltproject.org/api/v2/doc/doc?query=TERMO%20sourcelang:portuguese&mode=artlist&format=json&maxrecords=20` | Global e gratuito, mas no máximo **1 requisição a cada 5 s** (bloqueia o IP se passar disso). |
| **Busca no site do veículo** | skill `firecrawl-search`/`firecrawl-scrape`, ou WebSearch | Quando você já sabe qual veículo quer (g1, Folha, Estadão, CNN Brasil, Exame, InfoMoney, Valor, VEJA, UOL). |

**Como transformar a manchete em imagem** (os Reels de referência usam as duas formas):

- **Card recriado (padrão):** cartão branco, texto preto em sans bold (Inter/Poppins SemiBold), **marca-texto amarelo** (#FFE600) nas palavras-chave, revelado no ritmo da fala, e logo do veículo no topo (g1, CNN Money, Exame…). O texto é copiado letra por letra do título real.
- **Print real:** abra o `link` no Playwright (o link do Google redireciona com JS, então use navegador e não `curl`), faça `page.locator("h1").screenshot()` e recorte. Fica mais "prova", mas o visual é menos limpo. Use em temas polêmicos, onde a credibilidade importa mais que a estética.
  - Neste Mac já existe Chromium em `~/Library/Caches/ms-playwright/`: `uvx --with playwright python -c ...` ou `npx playwright`.
  - Paywall ou bloqueio: tente `https://archive.ph/newest/URL` ou a versão AMP.

Guarde sempre `{titulo, veiculo, data, link}` num `fontes.json` do projeto. O usuário pode precisar mostrar a fonte nos comentários.

---

## 2. Imagens e vídeos reais (painel de cima)

**Banco de imagens é proibido por padrão.** O usuário odeia imagem genérica. O que vale é a foto ou o vídeo **real do acontecimento**: a pessoa citada, o lugar de verdade, o produto real, a cena que viralizou. Prefira **vídeo**. Foto só serve se for animada (veja o SKILL.md §4).

Ordem de busca:

1. Material do usuário.
2. **Vídeo real do fato.**
3. **Foto da própria matéria** da manchete.
4. Fotos reais do fato em outras fontes.
5. Arquivo (Wikimedia, Internet Archive).

| Fonte | Para quê | Acesso |
|---|---|---|
| **Material do usuário** | sempre primeiro | pasta do projeto |
| **Foto da matéria** (og:image) | a foto real que o veículo usou para o fato | abra o link da manchete (Playwright) e leia `meta[property="og:image"]`. Dê crédito ao veículo/agência. |
| **Vídeo do fato em redes e TV** | o discurso, a cena viral, a reportagem | busque no YouTube, Instagram, X e TikTok (`site:` no WebSearch), baixe com `uvx yt-dlp` e recorte de 2 a 6 s |
| **Busca de imagens do fato** | quando a matéria não tem foto boa | WebSearch/`firecrawl-search` com o nome do evento + data. Use a foto do veículo ou da agência que cobriu o fato. |
| **Wikimedia Commons API** | pessoas públicas, lugares, logos, fotos históricas, vídeo de arquivo | sem chave: `commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=TERMO&gsrnamespace=6&prop=imageinfo&iiprop=url\|extmetadata&format=json` (mande um User-Agent). Licença no `extmetadata`. |
| **Agência Brasil (EBC)** | política e economia brasileira, Brasília, ministros | agenciabrasil.ebc.com.br, crédito "Fotógrafo/Agência Brasil". Tem licença CC BY, mas **confira a licença da foto**: o que foi produzido depois de fev/2017 pode ter outros termos. |
| **Flickr do Planalto / órgãos públicos** | fotos oficiais de governo | flickr.com/photos/palaciodoplanalto (confira a licença de cada foto) |
| **Internet Archive** | vídeos antigos, propagandas, TV de arquivo | `archive.org/advancedsearch.php?q=TERMO+AND+mediatype:movies&fl[]=identifier&output=json` |
| **Vídeos de notícia (YouTube/Instagram/X/TikTok)** | o trecho real do fato (discurso, entrevista, cena viral) | `uvx yt-dlp URL` (o yt-dlp do Homebrew neste Mac está quebrado, falta o módulo expat). Recorte só o necessário (2–6 s), dê crédito na tela e avise o usuário que é material de terceiros. |
| **Cenas de filmes e séries** | narrar uma situação ou cena que não tem registro real (uma reunião secreta, o golpe acontecendo, alguém perdendo tudo, o pânico no mercado) | busque "FILME cena DESCRIÇÃO" no YouTube (canais de clipes e trailers, como Movieclips) e baixe com `uvx yt-dlp`. Filmes conhecidos funcionam melhor (Lobo de Wall Street, A Grande Aposta, O Poderoso Chefão…). |
| **Logos de empresas** | aparecem MUITO no estilo (Pão de Açúcar, Shell, Lilly…) | Wikimedia Commons (SVG), press kit/site da empresa, `simpleicons.org` para marcas tech |
| **Prints de redes** (tweet, perfil, post) | reação do público, polêmica | print real via Playwright ou enviado pelo usuário. Borre nomes de pessoas comuns. |

**Cenas de filme, como capturar** (testado em out/2026):

1. **Escolher o filme:** pense em filmes conhecidos que tenham a situação com a emoção certa, ou pesquise ("cena filme pânico bolsa de valores"). O IMDb e o TMDB ajudam a confirmar a cena.
2. **Achar o clipe** sem chave de API:
   ```bash
   uvx yt-dlp --flat-playlist --print "%(id)s | %(duration)s s | %(channel)s | %(title)s" "ytsearch10:the big short scene market crash"
   ```
   Prefira os canais de clipes (Movieclips, Binge Society, Extractor, NOW PLAYING), que costumam ter os trechos em HD.
3. **Achar o segundo exato:**
   - **Pela fala:** baixe só a legenda automática, que vem com o tempo de cada palavra, e procure a fala:
     ```bash
     uvx --from "yt-dlp[default]" yt-dlp --js-runtimes node --skip-download --write-auto-subs --sub-langs en -o subs URL
     grep -i "mortgage" subs.en.vtt
     ```
   - **Pela imagem:** baixe o clipe em 360p (`--extractor-args youtube:player_client=mweb -f b`) e monte uma folha de contato (1 frame/s).
4. **Baixar só o trecho em HD:** `scripts/trecho.sh URL 00:01:13 00:01:18 cena.mp4` (acrescente `--sem-audio` quando a voz do apresentador for por cima).
   - O YouTube bloqueia o áudio no cliente padrão (erro 403), e o cliente `mweb` só entrega 360p. Por isso o script junta o vídeo HD de um com o áudio do outro.
   - Depende de `uv` e `node`.
5. Corte a marca d'água do canal (ex.: "BINGE SOCIETY" no canto superior esquerdo) com crop.

**Cenas de filme, regras:**

- Trechos de 2 a 5 s.
- Escolha a cena pela **emoção** que a frase pede, não só pelo assunto.
- Normalmente sem o áudio original (a voz do apresentador continua por cima). O áudio do filme só entra se a fala da cena for o próprio ponto.
- Recorte legendas queimadas e marcas d'água de canais.
- Crédito pequeno opcional ("cena: A Grande Aposta, 2015").
- É material protegido. Trechos curtos, usados para comentar, são a prática comum, mas avise o usuário quais cenas entraram.

**Material vertical** (para os layouts RECORTE e VOICE OVER):

- Reels, TikToks e Shorts do fato já vêm em 9:16.
- Foto de pessoa ou lugar: recorte vertical da foto real, com zoom lento.
- Se só existir na horizontal, dá para usar com fundo desfocado (a mesma imagem ampliada e borrada atrás) ou num cartão sobre a tela.

**Último recurso: banco de imagens** (Pexels, Pixabay). Use só para um conceito abstrato sem fato concreto por trás, e só depois de esgotar o real e de considerar um motion graphic. Avise o usuário em quais trechos usou.

**Rostos de pessoas comuns** (antes/depois, vídeos virais): **borre o rosto** (os Reels de referência fazem isso).

---

## 3. Gráficos e números

- Dado oficial: IBGE (`servicodados.ibge.gov.br/api`), Banco Central SGS (`api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json`: Selic=432, IPCA=433, dólar=1), B3, relatórios da empresa (RI).
- Desenhe o gráfico em código (barras vermelhas sobre um cartão branco, como no Reel do Pão de Açúcar) e escreva a fonte pequena embaixo.

---

## 3b. Mapas e lugares (motion graphic de localização)

`scripts/mapa.py` (testado). Rode com `uv run --no-project --with numpy --with pillow python scripts/mapa.py ...`:

- **País ou cidade estrangeira:** `mapa.py globo --lat -23.4 --lon -58.4 --nome PARAGUAI -o paraguai.mp4`. O globo gira até o alvo, dá zoom e o pino entra com o rótulo na placa vermelha.
- **Cidade no Brasil:** `mapa.py brasil --cidade Campinas --uf SP -o campinas.mp4`. Mostra o Brasil inteiro com os estados, o estado em amarelo e a cidade em vermelho, e dá zoom até a cidade (que nunca sai da tela).
- `--altura 800` gera no tamanho do painel de cima do SPLIT, e `--dur` ajusta a duração do zoom.

Dados (baixados uma vez e guardados em `~/.cache/edit-vm`):

| Dado | Fonte | Licença |
|---|---|---|
| Textura do globo | NASA Blue Marble Next Generation 5400×2700 (`eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg`) | domínio público, crédito "NASA Earth Observatory" |
| Contornos do Brasil, estados e municípios | API de malhas do IBGE (`servicodados.ibge.gov.br/api/v3/malhas/...`) + lista de municípios (`/api/v1/localidades/municipios`) | dado público |
| Contornos de países do mundo | Natural Earth GeoJSON (`raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson`) | domínio público |
| Bandeiras | `flagcdn.com/w1280/{código}.png` (br, py, us…) | domínio público |

Depois do zoom, complete com o que caracteriza o lugar: **bandeira**, paisagem ou cartão-postal real (Wikimedia), e o vídeo real do lugar.

O script não destaca a fronteira de outros países no globo. Se precisar, projete o GeoJSON do Natural Earth com a função `orto()`.

---

## 4. Ilustração por IA (só quando não existe imagem real)

Os Reels de referência usam IA para **metáforas de conflito**: águia × dragão no cabo de guerra (EUA × China), robôs Lilly × Novo Nordisk, Trump rasgando um "VISTO", Lula com marionetes, prédio do Pão de Açúcar em ruínas com logos de empresas falidas.

- Ferramenta: o MCP **Higgsfield** (`generate_image`) já está conectado neste ambiente. Na dúvida sobre o modelo, use `models_explore(action:'recommend')`.
- Use quando não existe foto real com a **emoção** ou o **contraste** que o roteiro pede (rosto chorando, rindo, preocupado; dois polos em conflito). Antes de gerar, procure de verdade a imagem real.
- Prompt: cena editorial hiper-realista, **com a emoção explícita no rosto**, 1080×800 (painel de cima), contraste forte entre os dois polos, cores quentes no lado "problema".
- **Proibido:** gerar foto que pareça o registro real de um fato que não aconteceu (ex.: "foto" de político num lugar onde ele não esteve, apresentada como notícia). Metáfora óbvia pode; falsificação, não.

---

## 5. Transcrição e tempo das palavras (legenda e cortes)

- **Mac Apple Silicon (este ambiente):** `uvx --from mlx-whisper mlx_whisper AUDIO.wav --model mlx-community/whisper-large-v3-turbo --language pt --word-timestamps True --output-format json`. Devolve o tempo de cada palavra.
- **Sem acesso ao HuggingFace (sandbox):** use sherpa-onnx (Whisper turbo + Parakeet para os tempos por palavra), com os modelos baixados dos releases do GitHub do k2-fsa/sherpa-onnx.
- Corrija nomes próprios antes de gerar a legenda (Retatrutida, Eli Lilly, Raízen, ether.fi…).

---

## 6. Fontes tipográficas (Google Fonts, `raw.githubusercontent.com/google/fonts/main/ofl/...`)

| Uso | Fonte |
|---|---|
| Legenda "condensada" | Anton ou Bebas Neue (branca, sombra preta) |
| Legenda "serifa" | Libre Baskerville / Lora (branca, contorno preto fino) |
| Placa do hook, títulos, números | Montserrat ExtraBold / Poppins Black |
| Card de manchete | Inter SemiBold / Poppins SemiBold |
| Palavra de destaque itálica ("de dívida", "de prejuízo") | Playfair Display Italic |

---

## 7. Safe zones 1080×1920 (Reels/TikTok/Shorts)

Nenhuma fonte oficial da Meta/TikTok. Consenso dos guias de 2026:

- **Livre embaixo:** os últimos ~420 px (y > 1500). Ali ficam o nome, a descrição e a barra de áudio.
- **Livre em cima:** ~200 px (y < 200).
- **Livre na direita:** ~120 px (x > 960), por causa dos botões de curtir/comentar/compartilhar.
- Texto crítico: dentro de x 60–960, y 200–1500.
