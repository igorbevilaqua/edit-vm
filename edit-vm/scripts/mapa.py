#!/usr/bin/env python3
"""Motion graphic de localização: zoom no globo ou no mapa do Brasil.

  python3 mapa.py globo  --lat -23.4 --lon -58.4 --nome "PARAGUAI" -o paraguai.mp4
  python3 mapa.py brasil --cidade "Campinas" --uf SP -o campinas.mp4
  python3 mapa.py --check

Opções: --largura 1080 --altura 1920 (use --altura 800 para o painel de cima), --dur 3.0
Dados: textura NASA Blue Marble (crédito "NASA Earth Observatory") e malhas do IBGE.
ponytail: globo é projeção ortográfica em numpy, sem contorno de país. Se precisar
destacar fronteira, projete o GeoJSON do Natural Earth com a mesma função `orto`.
"""
import argparse, json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

CACHE = os.path.expanduser("~/.cache/edit-vm")
BLUE_MARBLE = "https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg"
IBGE = "https://servicodados.ibge.gov.br/api"
FONTES = ["~/Library/Fonts/Montserrat-ExtraBold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
FPS = 30


def baixar(url, nome):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, nome)
    if not os.path.exists(p):  # ponytail: curl, porque o certificado do IBGE falha no ssl do Python
        subprocess.run(["curl", "-sSfL", "-A", "edit-vm", "-o", p, url], check=True)
    return p


def fonte(tam):
    for f in FONTES:
        f = os.path.expanduser(f)
        if os.path.exists(f):
            return ImageFont.truetype(f, tam)
    return ImageFont.load_default()


def ease(t):  # ease-in-out cúbico
    return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2


def encoder(saida, w, h):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", saida],
                            stdin=subprocess.PIPE)


def pino(img, x, y, nome, s):
    d = ImageDraw.Draw(img)
    r = int(14 * s)
    d.ellipse([x - r * 2, y - r * 2, x + r * 2, y + r * 2], outline=(255, 214, 0), width=max(2, int(4 * s)))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(229, 20, 26))
    if nome:
        f = fonte(int(64 * s))
        tw = d.textlength(nome, font=f)
        bx, by = x - tw / 2 - 24 * s, y - r * 2 - 110 * s
        d.rounded_rectangle([bx, by, bx + tw + 48 * s, by + 88 * s], 14 * s, fill=(229, 20, 26))
        d.text((bx + 24 * s, by + 8 * s), nome, font=f, fill=(255, 255, 255))


# ---------- globo ----------
def orto(lat, lon, lat0, lon0):
    """lat/lon (graus) -> (x, y, visível) na projeção ortográfica centrada em lat0/lon0, raio 1."""
    la, lo, la0, lo0 = map(np.radians, (lat, lon, lat0, lon0))
    x = np.cos(la) * np.sin(lo - lo0)
    y = np.cos(la0) * np.sin(la) - np.sin(la0) * np.cos(la) * np.cos(lo - lo0)
    vis = np.sin(la0) * np.sin(la) + np.cos(la0) * np.cos(la) * np.cos(lo - lo0) >= 0
    return x, y, vis


def globo_frame(tex, w, h, lat0, lon0, zoom):
    R = min(w, h) * 0.42 * zoom
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    x, y = (xx - w / 2) / R, -(yy - h / 2) / R
    rho2 = x * x + y * y
    dentro = rho2 <= 1
    z = np.sqrt(np.clip(1 - rho2, 0, 1))
    la0, lo0 = math.radians(lat0), math.radians(lon0)
    lat = np.arcsin(np.clip(z * math.sin(la0) + y * math.cos(la0), -1, 1))
    lon = lo0 + np.arctan2(x, z * math.cos(la0) - y * math.sin(la0))
    th, tw = tex.shape[:2]
    u = ((np.degrees(lon) + 180) % 360 / 360 * tw).astype(np.int32).clip(0, tw - 1)
    v = ((90 - np.degrees(lat)) / 180 * th).astype(np.int32).clip(0, th - 1)
    out = np.zeros((h, w, 3), np.uint8)
    out[:] = (8, 10, 18)
    out[dentro] = (tex[v, u][dentro] * (0.35 + 0.65 * z[dentro, None])).astype(np.uint8)  # sombreado nas bordas
    return out


def globo(a):
    tex = np.asarray(Image.open(baixar(BLUE_MARBLE, "bluemarble.jpg")).convert("RGB"))
    lat_ini, lon_ini = 10, a.lon + 70  # começa girado, longe do alvo, sem mostrar polo
    enc, n = encoder(a.o, a.largura, a.altura), int(a.dur * FPS)
    for i in range(n + FPS // 2):  # meio segundo parado no fim, com o pino
        t = ease(min(i / n, 1))
        lat0, lon0 = lat_ini + (a.lat - lat_ini) * t, lon_ini + (a.lon - lon_ini) * t
        zoom = math.exp(math.log(a.zoom) * ease(max(0, (i / n - .3) / .7)) if i < n else math.log(a.zoom))
        img = Image.fromarray(globo_frame(tex, a.largura, a.altura, lat0, lon0, zoom))
        if i / n > .75:
            x, y, _ = orto(a.lat, a.lon, lat0, lon0)
            R = min(a.largura, a.altura) * 0.42 * zoom
            pino(img, a.largura / 2 + x * R, a.altura / 2 - y * R, a.nome, a.largura / 1080)
        enc.stdin.write(img.tobytes())
    enc.stdin.close(); enc.wait()


# ---------- brasil ----------
def anel(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [np.array(p[0]) for p in polys]


def brasil(a):
    ufs = json.load(open(baixar(f"{IBGE}/v3/malhas/paises/BR?formato=application/vnd.geo+json&intrarregiao=UF&qualidade=minima", "br_ufs.json")))
    munis = json.load(open(baixar(f"{IBGE}/v1/localidades/municipios", "municipios.json")))
    alvo = next((m for m in munis if m["nome"].lower() == a.cidade.lower()
                 and m["microrregiao"]["mesorregiao"]["UF"]["sigla"] == a.uf.upper()), None)
    if not alvo:
        sys.exit(f"município não encontrado: {a.cidade}/{a.uf}")
    cid = json.load(open(baixar(f"{IBGE}/v3/malhas/municipios/{alvo['id']}?formato=application/vnd.geo+json", f"m{alvo['id']}.json")))
    uf_cod = str(alvo["id"])[:2]
    cid_aneis = anel(cid["features"][0]["geometry"])
    pts = np.vstack(cid_aneis)
    W, H = a.largura, a.altura
    k = math.cos(math.radians(-15))  # correção de aspecto (equiretangular)
    alvo_c = ((pts[:, 0].min() + pts[:, 0].max()) / 2, (pts[:, 1].min() + pts[:, 1].max()) / 2)
    ini_c = (-53.9, -14.2)  # centro do Brasil (bbox -74..-34, -34..5)
    s0 = min(W * .9 / (40 * k), H * .9 / 39)  # pixels por grau: Brasil inteiro
    s1 = min(W, H) * .3 / max(np.ptp(pts[:, 0]) * k, np.ptp(pts[:, 1]))  # cidade ~30% da tela
    enc, n = encoder(a.o, W, H), int(a.dur * FPS)
    nome = a.nome or alvo["nome"].upper()
    for i in range(n + FPS // 2):
        t = ease(min(i / n, 1))
        s = math.exp(math.log(s0) + (math.log(s1) - math.log(s0)) * t)
        f_ = s0 / s  # zoom em direção ao ponto: o alvo nunca sai da tela
        lon_c = alvo_c[0] + (ini_c[0] - alvo_c[0]) * f_
        lat_c = alvo_c[1] + (ini_c[1] - alvo_c[1]) * f_
        P = lambda r: [(W / 2 + (lo - lon_c) * s * k, H / 2 - (la - lat_c) * s) for lo, la in r]
        img = Image.new("RGB", (W, H), (14, 14, 16))
        d = ImageDraw.Draw(img)
        for f in ufs["features"]:
            meu = f["properties"]["codarea"] == uf_cod
            for r in anel(f["geometry"]):
                d.polygon(P(r), fill=(255, 196, 0) if meu else (31, 122, 58), outline=(235, 235, 235))
        for r in cid_aneis:
            d.polygon(P(r), fill=(229, 20, 26), outline=(255, 255, 255))
        if t > .6:
            pino(img, *P([alvo_c])[0], nome, W / 1080)
        enc.stdin.write(img.tobytes())
    enc.stdin.close(); enc.wait()


def _check():
    x, y, v = orto(-23.4, -58.4, -23.4, -58.4)
    assert abs(x) < 1e-9 and abs(y) < 1e-9 and v, "centro do globo tem de cair no centro da tela"
    x, y, v = orto(10, 120, -23.4, -58.4)
    assert not v, "ponto do outro lado do planeta tem de ficar invisível"
    assert ease(0) == 0 and ease(1) == 1 and abs(ease(.5) - .5) < 1e-9
    print("ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        _check(); sys.exit()
    p = argparse.ArgumentParser()
    p.add_argument("modo", choices=["globo", "brasil"])
    p.add_argument("--lat", type=float); p.add_argument("--lon", type=float)
    p.add_argument("--cidade"); p.add_argument("--uf"); p.add_argument("--nome", default="")
    p.add_argument("--zoom", type=float, default=3.5)
    p.add_argument("--largura", type=int, default=1080); p.add_argument("--altura", type=int, default=1920)
    p.add_argument("--dur", type=float, default=3.0); p.add_argument("-o", required=True)
    a = p.parse_args()
    globo(a) if a.modo == "globo" else brasil(a)
