// Extrae la sección CORE (funciones puras) de index.html y la expone como módulo CommonJS para las pruebas.
const fs = require('fs'), path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', '..', 'index.html'), 'utf8');
const a = html.indexOf('// ==CORE START=='), b = html.indexOf('// ==CORE END==');
if (a < 0 || b < 0) throw new Error('No se encuentran los marcadores ==CORE START== / ==CORE END== en index.html');
const src = html.slice(a, b);
const names = [...new Set([...src.matchAll(/^(?:function\s+([A-Za-z0-9_]+)|const\s+([A-Za-z0-9_]+)\s*=)/gm)].map(m => m[1] || m[2]))];
const mod = { exports: {} };
new Function('module', src + `\nmodule.exports = { ${names.join(', ')} };`)(mod);
module.exports = mod.exports;
