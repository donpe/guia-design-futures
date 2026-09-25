"""Genera docs/, el sitio que publica GitHub Pages, a partir de index.html.

index.html es la fuente del artifact de Claude (sin <html>/<head>, el visor los agrega).
Este script:
  1. Envuelve la página con un <head> completo (SEO, Open Graph, datos estructurados).
  2. Crea una página estática por sección (/empezar/, /conceptos/, /framing/…) con el
     contenido ya dibujado, para que buscadores y modelos de lenguaje lo lean sin JavaScript.
     El contenido lo dibuja prerender.js ejecutando el mismo script de la app en Node.
  3. Escribe sitemap.xml, robots.txt, llms.txt y llms-full.txt.

Uso:  python3 build.py
"""
import datetime, html, json, pathlib, re, shutil, subprocess

SITE = "https://donpe.github.io/guia-design-futures/"
BASE = "/guia-design-futures/"
AUTHOR = {"@type": "Person", "name": "Evelio Ramirez", "sameAs": "https://www.linkedin.com/in/evelioramirez/"}
BOOK = {
    "@type": "Book", "name": "The Field Guide to Design Futures", "isbn": "979-12-985986-2-1",
    "author": [{"@type": "Person", "name": "Giovanni Caruso"}, {"@type": "Person", "name": "Silvio Cioni"}],
    "publisher": {"@type": "Organization", "name": "Fictional"}, "datePublished": "2026-01",
    "numberOfPages": 231, "inLanguage": "en", "url": "https://designfutures.guide",
    "license": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
}
TODAY = datetime.date.today().isoformat()

# Título y descripción de cada sección (lo que muestran Google y las redes al compartir).
META = {
    "inicio": ("Guía de estudio de The Field Guide to Design Futures, en español",
               "Guía en español, no oficial, para leer, entender y aplicar The Field Guide to Design Futures de Giovanni Caruso y Silvio Cioni: el proceso, 175 fichas por página, 52 conceptos, infografías y práctica."),
    "empezar": ("Qué es Design Futures: empezar aquí",
                "Introducción a Design Futures para quien empieza: la diferencia entre diseño y estudios de futuros, lo que no es, cinco ideas clave y por dónde leer el libro de Caruso y Cioni."),
    "recorrido": ("El proceso de Design Futures en 5 pasos",
                  "Futuring by Design, el proceso del libro: Framing, Scanning y Sense-making, Visioning, Dissemination y Assessment, y Taking Action, con sus páginas."),
    "libro": ("The Field Guide to Design Futures, página por página",
              "175 fichas en español que resumen cada página con texto del libro de Caruso y Cioni: textos de los autores, de más de treinta colaboradores y citas."),
    "conceptos": ("Glosario de Design Futures: 52 conceptos",
                  "Glosario de Design Futures en español: señales, drivers, escenarios, artefactos del futuro, framing, futuros experienciales y más, con las páginas del libro."),
    "infografias": ("Infografías de Design Futures",
                    "18 infografías que ordenan ideas del libro: el proceso, el cono de futuros, señales y drivers, escenarios, disonancia discursiva y futuros experienciales."),
    "practica": ("Cómo hacer un proyecto de Design Futures: lista práctica",
                 "Lista de práctica paso a paso para aplicar Design Futures en un proyecto, basada en The Field Guide to Design Futures, con la página de cada punto."),
    "fuentes": ("Fuentes y bibliografía de The Field Guide to Design Futures",
                "Las 171 fuentes que cita el libro, con las páginas donde aparecen y el enlace impreso o encontrado."),
    "voces": ("Autores y colaboradores de The Field Guide to Design Futures",
              "Las voces del libro: Caruso y Cioni y más de treinta colaboradores de la academia y la práctica, con sus textos."),
    "sobre": ("Sobre esta guía: cómo está hecha",
              "Detalles técnicos de la guía: herramientas, cómo se construyó, cómo está organizado el código y licencia."),
    "marco": ("Qué es Design Futures (pp. 27–48)",
              "Definición de Design Futures según Caruso y Cioni: práctica híbrida entre diseño y estudios de futuros, mentalidad y práctica, y el proceso."),
    "framing": ("Framing en Design Futures: cómo encuadrar un proyecto",
                "Paso 1 de Design Futures: definir alcance, propósito, preguntas, actores y supuestos. Resumen del libro con páginas."),
    "scanning": ("Scanning en Design Futures: señales y escaneo del horizonte",
                 "Paso 2 de Design Futures: escaneo del entorno y del horizonte, señales débiles, etnografía periférica y trabajo de campo."),
    "sensemaking": ("Sense-making en Design Futures: de señales a drivers",
                    "Cómo agrupar señales en drivers de cambio, construir un inventario y dar sentido a la investigación de futuros."),
    "visioning": ("Visioning en Design Futures: escenarios y artefactos del futuro",
                  "Paso 3 de Design Futures: escenarios de futuro, artefactos del futuro, arquetipos de ficción de diseño y disonancia discursiva."),
    "dissemination": ("Dissemination en Design Futures: futuros experienciales",
                      "Paso 4 de Design Futures: compartir escenarios y artefactos, futuros experienciales, juegos de futuros y contextualización."),
    "assessment": ("Assessment en Design Futures: evaluar visiones de futuro",
                   "Cómo evaluar críticamente escenarios y visiones de futuro con audiencias y actores, según el libro."),
    "action": ("Taking Action en Design Futures: del futuro a la acción",
               "Paso 5 de Design Futures: llevar visiones de largo plazo a acciones de hoy; platforming y plataformas de futuros."),
    "vivo": ("Design Futures es plural y está vivo (pp. 196–207)",
             "Cierre del libro: una práctica plural e indisciplinada, co-creación de futuros y futuros regenerativos."),
}

root = pathlib.Path(__file__).parent
out = root / "docs"
src = (root / "index.html").read_text(encoding="utf-8")
title_tag = re.search(r"<title>.*?</title>", src, re.S).group(0)
body = src.replace(title_tag, "", 1)
m = re.match(r"\s*((?:<link[^>]*>\s*)+)(<style>.*?</style>)", body, re.S)
head_links, body = m.group(1) + m.group(2), body[m.end():]

pre = json.loads(subprocess.run(["node", str(root / "prerender.js")], capture_output=True, check=True, text=True).stdout)
pages, data = pre["pages"], pre["data"]

def path_of(r):
    return "" if r == "inicio" else f"{r}/"

def real_links(h):
    """En la copia estática, los enlaces #seccion pasan a rutas reales (rastreables)."""
    return re.sub(r'href="#([a-z]+)"', lambda m: f'href="{path_of(m.group(1))}"' if m.group(1) in pages else m.group(0), h)

def jsonld(r):
    url = SITE + path_of(r)
    site = {"@type": "WebSite", "@id": SITE + "#site", "name": "Guía de estudio de The Field Guide to Design Futures",
            "url": SITE, "inLanguage": "es", "author": AUTHOR, "license": BOOK["license"]}
    page = {"@type": "WebPage", "@id": url, "url": url, "name": META[r][0], "description": META[r][1],
            "inLanguage": "es", "isPartOf": {"@id": SITE + "#site"}, "about": BOOK, "dateModified": TODAY}
    graph = [site, page]
    if r == "inicio":
        graph.append({"@type": "LearningResource", "name": site["name"], "url": SITE, "inLanguage": "es",
                      "learningResourceType": "Guía de estudio", "educationalLevel": "Principiante",
                      "teaches": "Design Futures, estudios de futuros, diseño especulativo, escenarios",
                      "isBasedOn": BOOK, "author": AUTHOR, "license": BOOK["license"], "isAccessibleForFree": True})
    if r == "conceptos":
        graph.append({"@type": "DefinedTermSet", "name": "Conceptos de Design Futures", "url": url, "inLanguage": "es",
                      "hasDefinedTerm": [{"@type": "DefinedTerm", "name": c["t"], "alternateName": c["en"],
                                          "description": c["d"]} for c in data["CONCEPTS"]]})
    if r != "inicio":
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": META[r][0], "item": url}]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)

def page_html(r):
    t, d = META[r]
    url = SITE + path_of(r)
    full_t = t if r == "inicio" else f"{t} · Guía de estudio Design Futures"
    shell = body.replace('<main class="wrap" id="view"></main>', f'<main class="wrap" id="view">{real_links(pages[r]["view"])}</main>', 1)
    shell = shell.replace('<nav class="nav" id="nav" aria-label="Secciones"></nav>', f'<nav class="nav" id="nav" aria-label="Secciones">{real_links(pages[r]["nav"])}</nav>', 1)
    shell = real_links_footer(shell)
    e = html.escape
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<base href="{BASE}">
<title>{e(full_t)}</title>
<meta name="description" content="{e(d)}">
<link rel="canonical" href="{url}">
<meta name="author" content="Evelio Ramirez">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#602866">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_CO">
<meta property="og:site_name" content="Guía de estudio · The Field Guide to Design Futures">
<meta property="og:title" content="{e(t)}">
<meta property="og:description" content="{e(d)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(t)}">
<meta name="twitter:description" content="{e(d)}">
<meta name="twitter:image" content="{SITE}og.png">
<link rel="alternate" type="text/plain" title="Resumen para modelos de lenguaje" href="{SITE}llms.txt">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' rx='3' fill='%23602866'/%3E%3Crect x='7' y='3' width='7' height='3' fill='%23F72411'/%3E%3Crect x='5' y='6' width='7' height='3' fill='%23F72411'/%3E%3C/svg%3E">
<script type="application/ld+json">{jsonld(r)}</script>
<script>window.__ROUTE__={json.dumps(r)};</script>
{head_links}
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
{shell}
</body>
</html>
"""

def real_links_footer(h):
    # el pie y el encabezado están fuera de <main>: también pasan a rutas reales
    return re.sub(r'(<footer.*?</footer>)', lambda m: real_links(m.group(1)), h, flags=re.S)

# ---------- páginas ----------
if out.exists():
    for p in out.iterdir():
        if p.is_dir() and p.name != "img": shutil.rmtree(p)
out.mkdir(exist_ok=True)
for r in pages:
    d = out / path_of(r)
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page_html(r), encoding="utf-8")
shutil.copyfile(out / "index.html", out / "404.html")
shutil.copytree(root / "img", out / "img", dirs_exist_ok=True)
(out / ".nojekyll").write_text("")

# ---------- sitemap y robots ----------
(out / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{SITE}{path_of(r)}</loc><lastmod>{TODAY}</lastmod><priority>{'1.0' if r == 'inicio' else '0.8' if r in ('empezar', 'recorrido', 'conceptos', 'libro') else '0.6'}</priority></url>\n" for r in pages)
    + "</urlset>\n", encoding="utf-8")
(out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8")

# ---------- llms.txt ----------
PH, STEPS, FI, CO, SRC = data["PH"], data["STEPS"], data["FICHAS"], data["CONCEPTS"], data["SRC"]
SLUG_OF = {v: k for k, v in data["SLUG"].items()}
TY = {"a": "Autores", "c": "Colaborador", "q": "Cita (paráfrasis)"}
intro = ("Guía de estudio en español, no oficial, de *The Field Guide to Design Futures* de Giovanni Caruso y Silvio Cioni "
         "(Fictional, 1.ª edición, enero de 2026, 231 páginas, ISBN 979-12-985986-2-1). Todo el contenido sale del libro y "
         "lleva su número de página impresa; los textos en español son paráfrasis, no traducciones literales. "
         "Libro original: https://designfutures.guide. Licencia CC BY-NC-SA 4.0. Editada por Evelio Ramirez "
         "(https://www.linkedin.com/in/evelioramirez/).")
llms = [f"# Guía de estudio de The Field Guide to Design Futures", "", f"> {intro}", "",
        "Design Futures es una práctica que une el diseño con los estudios de futuros para explorar y dar forma a presentes "
        "alternativos y futuros posibles, haciéndolos tangibles con narrativas, prototipos y artefactos; no predice, sino que "
        "ayuda a cuestionar supuestos y a decidir mejor en el presente (p. 31).", "",
        "## Proceso (Futuring by Design, p. 42)", ""]
llms += [f"{s['n']}. **{s['t']}** ({s['es']}): {s['d']}" for s in STEPS] + ["", "## Páginas", ""]
llms += [f"- [{META[r][0]}]({SITE}{path_of(r)}): {META[r][1]}" for r in pages]
llms += ["", "## Texto completo", "", f"- [llms-full.txt]({SITE}llms-full.txt): todas las fichas por página, los conceptos, la práctica y las fuentes, en Markdown.", ""]
(out / "llms.txt").write_text("\n".join(llms), encoding="utf-8")

full = [f"# Guía de estudio de The Field Guide to Design Futures (texto completo)", "", f"> {intro}", "",
        "Cómo citar: usa el libro original y su número de página. Esta guía es una paráfrasis en español.", "",
        "## Proceso: Futuring by Design (p. 42)", ""]
full += [f"{s['n']}. **{s['t']}** ({s['es']}): {s['d']}" for s in STEPS]
full += ["", "## Fichas, página por página", ""]
order = ["pre", "df", "fr", "sc", "sm", "vi", "di", "as", "ta", "viva", "post"]
for k in order:
    fs = [f for f in FI if f["ph"] == k]
    if not fs: continue
    ph = PH[k]
    full += [f"### {ph['t']}{' · ' + ph['es'] if ph.get('es') else ''} (pp. {ph['pp']})", ""]
    for f in fs:
        full += [f"#### p. {f['p']} · {f['t']}", f"*{TY[f['ty']]}: {f['a']}*", "", f["x"].strip(), ""]
full += ["## Conceptos", ""]
for c in sorted(CO, key=lambda c: c["t"].lower()):
    full += [f"- **{c['t']}** ({c['en']}), p. {', '.join(map(str, c['p']))}: {c['d']}"]
full += ["", "## Fuentes citadas en el libro", ""]
for sid, s in sorted(SRC.items(), key=lambda kv: kv[1]["r"].lower()):
    pp = ", ".join(str(u[0]) for u in s.get("use", []))
    link = s.get("u") or s.get("f") or ""
    tag = " (enlace impreso en el libro)" if s.get("u") else " (enlace encontrado, no está en el libro)" if s.get("f") else ""
    full += [f"- {s['r']} Páginas: {pp}.{(' ' + link + tag) if link else ''}"]
(out / "llms-full.txt").write_text("\n".join(full) + "\n", encoding="utf-8")

# ---------- imagen para compartir ----------
og = out / "og.png"
if not (root / "og.png").exists():
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "#FBF9FB"); dr = ImageDraw.Draw(im)
    for i, (x, y, w) in enumerate([(820, 40, 340), (780, 76, 380), (760, 112, 360)]):
        dr.rectangle([x, y, x + w, y + 36], fill="#F72411")
    for i, (x, y, w) in enumerate([(60, 470, 260), (60, 506, 300), (60, 542, 240)]):
        dr.rectangle([x, y, x + w, y + 36], fill="#602866")
    bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"; reg = "/System/Library/Fonts/Supplemental/Arial.ttf"
    dr.text((60, 60), "GUÍA DE ESTUDIO · EN ESPAÑOL", font=ImageFont.truetype(reg, 26), fill="#6A5A6D")
    y = 120
    for line in ["The Field Guide", "to Design Futures"]:
        dr.text((60, y), line, font=ImageFont.truetype(bold, 84), fill="#602866"); y += 96
    dr.text((60, 330), "El proceso, 175 fichas por página, 52 conceptos,", font=ImageFont.truetype(reg, 34), fill="#1D1320")
    dr.text((60, 374), "infografías y práctica. Caruso y Cioni, 2026.", font=ImageFont.truetype(reg, 34), fill="#1D1320")
    ill = Image.open(root / "img" / "p41.png").convert("RGBA"); ill.thumbnail((380, 380))
    im.paste(ill, (W - ill.width - 60, H - ill.height - 40), ill)
    im.save(root / "og.png", optimize=True)
shutil.copyfile(root / "og.png", og)

print(f"{len(pages)} páginas · llms.txt · llms-full.txt ({(out / 'llms-full.txt').stat().st_size // 1024} KB) · sitemap · og.png")
