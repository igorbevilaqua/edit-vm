#!/usr/bin/env python3
"""Busca manchetes REAIS no Google Notícias (edição Brasil) e devolve JSON.

Uso:  python3 manchetes.py "termo de busca" [--dias 30] [--max 10]
Saída: lista de {titulo, veiculo, site, data, link} — o título vem exatamente
como o veículo publicou (só remove o " - Veículo" que o Google acrescenta).

ponytail: RSS público do Google Notícias, sem chave e sem docs oficiais; se um
dia quebrar, troque por GDELT (api.gdeltproject.org/api/v2/doc/doc, 1 req/5 s).
"""
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

RSS = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"


def parse(xml_bytes):
    out = []
    for item in ET.fromstring(xml_bytes).iter("item"):
        src = item.find("source")
        veiculo = src.text if src is not None else ""
        titulo = item.findtext("title", "")
        if veiculo and titulo.endswith(" - " + veiculo):
            titulo = titulo[: -len(veiculo) - 3]
        data = item.findtext("pubDate", "")
        out.append({
            "titulo": titulo,
            "veiculo": veiculo,
            "site": src.get("url", "") if src is not None else "",
            "data": parsedate_to_datetime(data).date().isoformat() if data else "",
            "link": item.findtext("link", ""),  # redireciona p/ a matéria; abra no navegador/Playwright
        })
    return out


def buscar(termo, dias=30, maximo=10):
    q = urllib.parse.quote(f"{termo} when:{dias}d")
    req = urllib.request.Request(RSS.format(q=q), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return parse(r.read())[:maximo]


def _check():
    xml = b"""<rss><channel><item><title>FMI alerta para 40% dos empregos - VEJA</title>
    <link>https://news.google.com/rss/articles/x</link><pubDate>Mon, 13 Oct 2026 12:00:00 GMT</pubDate>
    <source url="https://veja.abril.com.br">VEJA</source></item></channel></rss>"""
    [m] = parse(xml)
    assert m["titulo"] == "FMI alerta para 40% dos empregos", m
    assert (m["veiculo"], m["site"], m["data"]) == ("VEJA", "https://veja.abril.com.br", "2026-10-13"), m
    print("ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--check"]:
        _check()
        sys.exit()
    if not a:
        sys.exit(__doc__)
    dias = int(a[a.index("--dias") + 1]) if "--dias" in a else 30
    maximo = int(a[a.index("--max") + 1]) if "--max" in a else 10
    termo = " ".join(x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or not a[i - 1].startswith("--")))
    print(json.dumps(buscar(termo, dias, maximo), ensure_ascii=False, indent=1))
