# Edit VM

Skill do Claude Code para editar vídeos verticais no estilo **VM Labs**: tela dividida, apelo visual com contraste em cima, manchete de notícia real no meio, apresentador embaixo, hook com placa vermelha e legenda palavra a palavra.

## Instalar

```bash
git clone https://github.com/igorbevilaqua/edit-vm.git && cp -r edit-vm/edit-vm ~/.claude/skills/edit-vm
```

Depois é só pedir no Claude Code: "edita esse vídeo no estilo edit vm".

## Conteúdo

- `edit-vm/SKILL.md`: o estilo e o pipeline.
- `edit-vm/references/fontes.md`: onde buscar manchetes, imagens, vídeos, dados e fontes tipográficas.
- `edit-vm/scripts/manchetes.py`: busca manchetes reais no Google Notícias BR (`--check` roda o autoteste).
- `edit-vm/scripts/trecho.sh`: baixa só um trecho de vídeo (YouTube/redes) em 1080p, com áudio.
- `edit-vm/scripts/mapa.py`: motion graphic de localização (zoom no globo ou no mapa do Brasil até a cidade).

Requisitos: ffmpeg, Python 3, Node e `uv` (para `uvx yt-dlp`, `mlx-whisper`, `playwright` e `uv run --with numpy --with pillow`).
