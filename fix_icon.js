const fs = require('fs');
let code = fs.readFileSync('static/app.js', 'utf8');

const oldListener = `DOM.thInvDisp?.addEventListener("click", () => {
    if (DOM.filterPromoSort) {
        if (DOM.filterPromoSort.value === "inv-asc") {
            DOM.filterPromoSort.value = "inv-desc";
        } else {
            DOM.filterPromoSort.value = "inv-asc";
        }
        loadPromocionesData(false);
    }
});`;

const newListener = `DOM.thInvDisp?.addEventListener("click", () => {
    if (DOM.filterPromoSort) {
        const icon = DOM.thInvDisp.querySelector("i");
        if (DOM.filterPromoSort.value === "inv-asc") {
            DOM.filterPromoSort.value = "inv-desc";
            if(icon) icon.className = "fa-solid fa-sort-down";
        } else {
            DOM.filterPromoSort.value = "inv-asc";
            if(icon) icon.className = "fa-solid fa-sort-up";
        }
        loadPromocionesData(false);
    }
});`;

code = code.replace(oldListener, newListener);
fs.writeFileSync('static/app.js', code);
