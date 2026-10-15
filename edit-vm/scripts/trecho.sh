#!/usr/bin/env bash
# Baixa SÓ um trecho de um vídeo (YouTube, Instagram, X, TikTok…) em até 1080p.
#   trecho.sh URL INICIO FIM SAIDA.mp4 [--sem-audio]
#   trecho.sh "https://youtu.be/YgF98vyn2fY" 00:01:13 00:01:18 cena.mp4
#
# Por que é assim (testado em out/2026): no YouTube o cliente padrão entrega o
# vídeo HD, mas o áudio dá 403; o cliente "mweb" entrega o áudio, mas só em 360p.
# Então o script baixa o vídeo HD de um, o áudio do outro, e junta os dois.
set -euo pipefail
URL=$1; INI=$2; FIM=$3; OUT=$4; SEM_AUDIO=${5:-}
YT=(uvx --from "yt-dlp[default]" yt-dlp --no-warnings -q --js-runtimes node --download-sections "*$INI-$FIM")
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

if [[ $URL != *youtu* ]]; then  # outras redes: download direto
  "${YT[@]}" -S "res:1080,ext:mp4:m4a" -o "$TMP/v.%(ext)s" "$URL"
  ffmpeg -v error -y -i "$TMP"/v.* ${SEM_AUDIO:+-an} -c:v libx264 -crf 16 -c:a aac "$OUT"; exit
fi

"${YT[@]}" -f "bv*[height<=1080][protocol=https]" -o "$TMP/v.%(ext)s" "$URL"
if [[ -n $SEM_AUDIO ]]; then
  ffmpeg -v error -y -i "$TMP"/v.* -an -c:v libx264 -crf 16 "$OUT"; exit
fi
"${YT[@]}" --extractor-args "youtube:player_client=mweb" -f b -o "$TMP/a.%(ext)s" "$URL"
ffmpeg -v error -y -i "$TMP"/v.* -i "$TMP"/a.* -map 0:v -map 1:a -c:v libx264 -crf 16 -c:a aac -shortest "$OUT"
