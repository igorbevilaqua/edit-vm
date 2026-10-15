#!/usr/bin/env bash
# Prepara a gravação bruta antes de editar: cor e áudio corretos desde o início.
#   preparar.sh GRAVACAO.MOV PASTA
# Gera em PASTA:
#   proxy.mp4  1080x1920, 30 fps, SDR BT.709 marcado (HDR do iPhone convertido de verdade)
#   voz.wav    48 kHz mono, tratada e em -15 LUFS, SEM esmagar a dinâmica
#   voz16.wav  16 kHz mono para a transcrição
#   cor.txt    diagnóstico da imagem + a correção aplicada (se houver)
#
# Por quê (teste real, out/2026): o iPhone grava em HDR HLG/BT.2020. Ler esse vídeo
# direto para RGB sem tone mapping deixa a imagem lavada e esbranquiçada. E empurrar
# uma voz de -29 LUFS para -14 com o limitador dinâmico do loudnorm estoura o som.
set -euo pipefail
SRC=$1; OUT=$2; mkdir -p "$OUT"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
TAG=(-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv)

# ---------- 1. HDR -> SDR ----------
TRC=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of csv=p=0 "$SRC" | tr -d ",\n")  # vem com vírgula no fim
SDR=$SRC
if [[ $TRC == arib-std-b67 || $TRC == smpte2084 ]]; then
  echo "HDR detectado ($TRC): convertendo para SDR"
  if command -v avconvert >/dev/null; then  # tone mapping da Apple (o mesmo do app Fotos)
    avconvert -s "$SRC" -o "$TMP/sdr.mp4" -p Preset1920x1080 --replace >/dev/null
  elif ffmpeg -hide_banner -filters 2>/dev/null | grep -q " zscale "; then  # Linux: ffmpeg com libzimg
    ffmpeg -v error -y -i "$SRC" -vf "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p" -c:v libx264 -crf 12 -an "$TMP/sdr.mp4"
  else
    echo "ERRO: vídeo HDR e não há avconvert nem ffmpeg com zscale. Não siga: a imagem vai sair lavada." >&2; exit 1
  fi
  SDR=$TMP/sdr.mp4
fi

# ---------- 2. diagnóstico e correção de cor (só corrige o que está fora do normal) ----------
ffmpeg -v error -i "$SDR" -vf "fps=1,scale=540:-2,format=yuv420p,signalstats,metadata=print:file=-" -an -f null - |
  awk -F= '/(YMIN|YLOW|YAVG|YHIGH|YMAX|SATAVG)=/{split($1,k,".");n[k[3]]++;s[k[3]]+=$2} END{for(x in s) printf "%s=%.0f\n",x,s[x]/n[x]}' > "$OUT/cor.txt"
GRADE=$(python3 - "$OUT/cor.txt" <<'EOF'
import sys
s = dict(l.strip().split("=") for l in open(sys.argv[1]) if "=" in l); s = {k: float(v) for k, v in s.items()}
f = []
# preto lavado ou branco apagado -> estica os níveis (16-235)
if s["YMIN"] > 24 or s["YMAX"] < 220:
    lo, hi = min(s["YMIN"], 40) / 255, max(s["YMAX"], 200) / 255
    f.append(f"colorlevels=rimin={lo:.3f}:gimin={lo:.3f}:bimin={lo:.3f}:rimax={hi:.3f}:gimax={hi:.3f}:bimax={hi:.3f}")
# exposição fora da faixa -> gama suave (nunca brilho chapado, que lava a imagem)
if s["YAVG"] < 85:   f.append("eq=gamma=1.12")
if s["YAVG"] > 150:  f.append("eq=gamma=0.9")
# cor apagada -> saturação leve (teto 1.12 para não alaranjar a pele)
if s["SATAVG"] < 14: f.append("eq=saturation=1.12")
print(",".join(f))
EOF
)
echo "correcao=${GRADE:-nenhuma}" >> "$OUT/cor.txt"; cat "$OUT/cor.txt"

# ---------- 3. proxy 30 fps, marcado como BT.709 ----------
ffmpeg -v error -y -i "$SDR" -vf "${GRADE:+$GRADE,}fps=30,scale=-2:'min(1920,ih)',setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" -c:v libx264 -crf 14 -preset veryfast \
  -pix_fmt yuv420p "${TAG[@]}" -an "$OUT/proxy.mp4"

# ---------- 4. voz: limpeza leve, compressão suave, ganho linear e limiter transparente ----------
PRE="highpass=f=70,afftdn=nr=8:nf=-50,acompressor=threshold=-32dB:ratio=3:attack=12:release=180:knee=6"
ffmpeg -v error -y -i "$SRC" -vn -ac 1 -ar 48000 -af "$PRE" -c:a pcm_f32le "$TMP/pre.wav"
I=$(ffmpeg -hide_banner -i "$TMP/pre.wav" -af ebur128 -f null - 2>&1 | grep -A3 Summary | awk '/ I:/{print $2}')
G=$(python3 -c "print(round(-15 - ($I), 2))")
ffmpeg -v error -y -i "$TMP/pre.wav" -af "volume=${G}dB,alimiter=limit=0.84:attack=5:release=80:level=disabled" -c:a pcm_s24le "$OUT/voz.wav"
ffmpeg -v error -y -i "$OUT/voz.wav" -ar 16000 "$OUT/voz16.wav"
echo "voz: entrada $I LUFS, ganho +$G dB, saída ~-15 LUFS, pico <= -1.5 dBFS"
