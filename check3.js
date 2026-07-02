const fs = require('fs');
const lines = fs.readFileSync('static/app.js', 'utf8').split('\n');
let inDOMContentLoaded = false;
for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('document.addEventListener("DOMContentLoaded"')) {
        inDOMContentLoaded = true;
    }
    if (inDOMContentLoaded) {
        console.log(i + 1, lines[i]);
    }
    if (inDOMContentLoaded && lines[i].includes('// --- COTIZACIONES UPLOAD LOGIC ---')) {
        break;
    }
}
