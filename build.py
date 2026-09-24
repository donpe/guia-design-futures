"""Genera docs/ (sitio autónomo para GitHub Pages) a partir de index.html.

index.html es la fuente del artifact de Claude (sin <html>/<head>, el visor los agrega).
Aquí se envuelve con el esqueleto HTML completo para servirlo en cualquier lado.
"""
import pathlib, re, shutil

root = pathlib.Path(__file__).parent
src = (root / "index.html").read_text(encoding="utf-8")
title = re.search(r"<title>.*?</title>", src, re.S).group(0)
body = src.replace(title, "", 1)
head_links, rest = [], body
# mueve <link> y <style> iniciales al <head>
m = re.match(r"\s*((?:<link[^>]*>\s*)+)(<style>.*?</style>)", rest, re.S)
if m:
    head_links = [m.group(1), m.group(2)]
    rest = rest[m.end():]
page = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Guía de estudio en español, no oficial, de The Field Guide to Design Futures (Caruso y Cioni, 2026).">
{title}
{''.join(head_links)}
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
{rest}
</body>
</html>
"""
out = root / "docs"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(page, encoding="utf-8")
shutil.copytree(root / "img", out / "img", dirs_exist_ok=True)
(out / ".nojekyll").write_text("")
print("docs/index.html", len(page))
