const fs = require('fs');
const css = `
/* Forms & Inputs */
.form-control, .form-select {
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.2);
    color: hsl(var(--text-primary));
    font-size: 0.9rem;
    transition: all 0.2s ease;
}
.form-control:focus, .form-select:focus {
    outline: none;
    border-color: hsl(var(--primary));
    box-shadow: 0 0 0 3px hsla(var(--primary), 0.2);
    background: rgba(0, 0, 0, 0.4);
}
.form-select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='4 6 8 10 12 6'%3E%3C/polyline%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 14px center;
    background-size: 14px;
    padding-right: 36px;
}
.form-select option {
    background: hsl(var(--card-bg));
    color: hsl(var(--text-primary));
}
`;
fs.appendFileSync('static/style.css', css);
// Also bump index.html version for style.css to 1.0.5
let html = fs.readFileSync('static/index.html', 'utf8');
html = html.replace('style.css?v=1.0.4', 'style.css?v=1.0.5');
fs.writeFileSync('static/index.html', html);
