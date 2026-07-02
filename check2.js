const fs = require('fs');
let app = fs.readFileSync('static/app.js', 'utf8');

// Wrap loadPromocionesData body in try/catch
app = app.replace(
    'async function loadPromocionesData(forceRefresh = false) {\n    try {\n        if (forceRefresh || !state.promociones || state.promociones.length === 0) {',
    'async function loadPromocionesData(forceRefresh = false) {\n    try {\n        if (forceRefresh || !state.promociones || state.promociones.length === 0) {'
);
// Actually it already has a try block!
// Let's see what the catch block of loadPromocionesData does:
