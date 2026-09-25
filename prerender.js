// Ejecuta el script de index.html en Node, sin navegador, y devuelve en JSON:
// el HTML de cada vista (para páginas estáticas) y los datos (para llms-full.txt).
// Lo llama build.py; no hace falta usarlo a mano.
const fs = require("fs");
const src = fs.readFileSync(__dirname + "/index.html", "utf8");
let js = src.match(/<script>\n\(\(\) => \{([\s\S]*)\}\)\(\);\n<\/script>/)[1];

// Quita el arranque y expone lo que necesitamos.
const tail = js.lastIndexOf("// ================= INICIO =================");
js = js.slice(0, tail) + `
globalThis.__OUT__ = { PH, STEPS, FICHAS, CONCEPTS, SRC, PRAC, IG, SLUG, NAV,
  renderAt(r){ route = r; q = ""; render(); return { view: $("#view").innerHTML, nav: $("#nav").innerHTML }; } };`;

// DOM mínimo: solo lo que el script toca al cargar y al dibujar.
const els = {};
const el = () => ({ innerHTML: "", value: "", addEventListener(){}, scrollIntoView(){}, appendChild(){} });
globalThis.document = {
  querySelector: s => (els[s] ||= el()),
  getElementById: id => (els["#" + id] ||= el()),
  createElement: el, addEventListener(){}, body: el(),
  documentElement: { get outerHTML(){ return src; } },
};
globalThis.window = globalThis;
globalThis.addEventListener = () => {};
globalThis.scrollTo = () => {};
globalThis.requestAnimationFrame = f => f();
globalThis.location = { hash: "" };
globalThis.history = { pushState(){} };
globalThis.localStorage = { getItem(){ return null; }, setItem(){} };

new Function(js)();
const O = globalThis.__OUT__;
const routes = [...O.NAV.map(n => n[0]), "sobre", ...Object.keys(O.SLUG)];
const pages = {};
for (const r of routes) pages[r] = O.renderAt(r);

const data = { PH: O.PH, STEPS: O.STEPS, FICHAS: O.FICHAS, CONCEPTS: O.CONCEPTS, SRC: O.SRC, PRAC: O.PRAC, SLUG: O.SLUG, NAV: O.NAV };
process.stdout.write(JSON.stringify({ pages, data }));
