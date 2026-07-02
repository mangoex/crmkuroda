const fs = require('fs');
const lines = fs.readFileSync('static/app.js', 'utf8').split('\n');
let openBraces = 0;
let inDOM = false;
for (let i = 0; i < lines.length; i++) {
    let l = lines[i];
    if (l.includes('document.addEventListener("DOMContentLoaded"')) {
        inDOM = true;
        openBraces += (l.match(/\{/g) || []).length;
        openBraces -= (l.match(/\}/g) || []).length;
        continue;
    }
    if (inDOM) {
        openBraces += (l.match(/\{/g) || []).length;
        openBraces -= (l.match(/\}/g) || []).length;
        if (openBraces <= 0) {
            console.log('Closes at', i + 1);
            inDOM = false;
        }
    }
}
