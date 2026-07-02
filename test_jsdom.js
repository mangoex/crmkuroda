const fs = require('fs');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

const html = fs.readFileSync('static/index.html', 'utf8');
const js = fs.readFileSync('static/app.js', 'utf8');

const dom = new JSDOM(html, { runScripts: "dangerously" });
dom.window.onerror = function(msg, source, lineno, colno, error) {
    console.error('ERROR in app.js on line', lineno, ':', msg);
};

// Provide necessary mocks
dom.window.localStorage = {
    getItem: () => null,
    setItem: () => {},
    removeItem: () => {}
};
dom.window.Chart = class { constructor() {} };

const script = dom.window.document.createElement('script');
script.textContent = js;
dom.window.document.body.appendChild(script);

console.log("Done initializing.");
