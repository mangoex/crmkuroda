const fs = require('fs');
let code = fs.readFileSync('static/app.js', 'utf8');

// Replace all DOM.xxx.addEventListener with DOM.xxx?.addEventListener
code = code.replace(/DOM\.([a-zA-Z0-9_]+)\.addEventListener/g, 'DOM.$1?.addEventListener');

// Write back
fs.writeFileSync('static/app.js', code);
