# Guía de estudio · The Field Guide to Design Futures

Micrositio en español, **no oficial**, para leer, estudiar y aplicar
*The Field Guide to Design Futures* de Giovanni Caruso y Silvio Cioni
(Fictional, 1.ª edición, enero de 2026).

**Sitio:** https://donpe.github.io/guia-design-futures/
**Libro original:** https://designfutures.guide

## Qué contiene

- **Empezar aquí:** resumen para quien no conoce Design Futures.
- **Recorrido:** los 5 pasos que propone el libro (Framing, Scanning y Sense-making, Visioning, Dissemination y Assessment, Taking Action).
- **Leer el libro:** una ficha por cada página con texto, resumida en español.
- **Conceptos, infografías, práctica paso a paso y voces.**
- **Fuentes:** todo lo que el libro cita, con las páginas donde aparece.
  Se distingue el enlace impreso en el libro del enlace encontrado después.

Todo el contenido sale del libro y lleva su número de página impresa.
Los textos en español son paráfrasis; para citar, usa el original.

## Licencia

El libro se publica bajo [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
Esta guía es una adaptación y se comparte bajo la misma licencia, sin uso comercial.
Las ilustraciones son de Stefano Cardini y provienen del libro.

## Estructura

- `index.html`: fuente de la página (formato de Claude Artifacts, sin `<html>`/`<head>`).
- `img/`: ilustraciones, nombradas por página impresa.
- `build.py`: genera `docs/`, lo que publica GitHub Pages: una página estática por sección (con el contenido ya escrito, para buscadores), `sitemap.xml`, `robots.txt`, `llms.txt`, `llms-full.txt` y la imagen para compartir.
- `prerender.js`: ejecuta el script de la página en Node para dibujar cada sección sin navegador. Lo usa `build.py`.

```
python3 build.py
```
