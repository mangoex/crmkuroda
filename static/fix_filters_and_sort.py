import sys
import re

js_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update loadPromocionesData
old_func = """async function loadPromocionesData() {
    const searchTerm = DOM.filterPromoSearch ? DOM.filterPromoSearch.value.toLowerCase() : "";
    const statusFilter = DOM.filterPromoStatus ? DOM.filterPromoStatus.value : "activas";
    const sortFilter = DOM.filterPromoSort ? DOM.filterPromoSort.value : "default";
    const proveedorFilter = DOM.filterPromoProveedor ? DOM.filterPromoProveedor.value : "todos";
    let endpoint = "/api/v1/promociones/";
    
    try {
        const res = await apiRequest(endpoint);
        let promociones = res.data || [];"""

new_func = """async function loadPromocionesData(forceRefresh = false) {
    const searchTerm = DOM.filterPromoSearch ? DOM.filterPromoSearch.value.toLowerCase() : "";
    const statusFilter = DOM.filterPromoStatus ? DOM.filterPromoStatus.value : "activas";
    const sortFilter = DOM.filterPromoSort ? DOM.filterPromoSort.value : "default";
    const proveedorFilter = DOM.filterPromoProveedor ? DOM.filterPromoProveedor.value : "todos";
    let endpoint = "/api/v1/promociones/";
    
    try {
        if (forceRefresh || !state.promociones || state.promociones.length === 0) {
            const res = await apiRequest(endpoint);
            state.promociones = res.data || [];
        }
        let promociones = [...state.promociones];"""

if old_func in js:
    js = js.replace(old_func, new_func)
else:
    print("Could not find loadPromocionesData start.")

# 2. Add inv sorting logic
old_sort = """        } else if (sortFilter === "precio-asc") {
            promociones.sort((a, b) => (a.precio_promocion || 0) - (b.precio_promocion || 0));
        }"""
new_sort = """        } else if (sortFilter === "precio-asc") {
            promociones.sort((a, b) => (a.precio_promocion || 0) - (b.precio_promocion || 0));
        } else if (sortFilter === "inv-asc") {
            promociones.sort((a, b) => (a.inventario_disponible || 0) - (b.inventario_disponible || 0));
        } else if (sortFilter === "inv-desc") {
            promociones.sort((a, b) => (b.inventario_disponible || 0) - (a.inventario_disponible || 0));
        }"""
if old_sort in js:
    js = js.replace(old_sort, new_sort)
else:
    print("Could not find sort logic.")

# 3. Add DOM property for thInvDisp
old_dom = """    filterPromoSearch: document.getElementById("filter-promo-search"),"""
new_dom = """    filterPromoSearch: document.getElementById("filter-promo-search"),
    thInvDisp: document.getElementById("th-inv-disp"),"""
if old_dom in js:
    js = js.replace(old_dom, new_dom)
else:
    print("Could not find DOM property.")

# 4. Add event listener for thInvDisp and fix loadPromocionesData calls
old_events = """DOM.filterPromoProveedor?.addEventListener("change", loadPromocionesData);
DOM.filterPromoSearch?.addEventListener("input", loadPromocionesData);"""
new_events = """DOM.filterPromoProveedor?.addEventListener("change", () => loadPromocionesData(false));
DOM.filterPromoSearch?.addEventListener("input", () => loadPromocionesData(false));
DOM.thInvDisp?.addEventListener("click", () => {
    if (DOM.filterPromoSort) {
        if (DOM.filterPromoSort.value === "inv-asc") {
            DOM.filterPromoSort.value = "inv-desc";
        } else {
            DOM.filterPromoSort.value = "inv-asc";
        }
        loadPromocionesData(false);
    }
});"""
if old_events in js:
    js = js.replace(old_events, new_events)
else:
    print("Could not find event listeners.")

old_events_2 = """DOM.filterPromoStatus?.addEventListener("change", loadPromocionesData);
DOM.filterPromoSort?.addEventListener("change", loadPromocionesData);"""
new_events_2 = """DOM.filterPromoStatus?.addEventListener("change", () => loadPromocionesData(false));
DOM.filterPromoSort?.addEventListener("change", () => loadPromocionesData(false));"""
if old_events_2 in js:
    js = js.replace(old_events_2, new_events_2)

old_clear_event = """loadPromocionesData();
});"""
new_clear_event = """loadPromocionesData(false);
});"""
if old_clear_event in js:
    js = js.replace(old_clear_event, new_clear_event)

# 5. Fix border radius on cards
js = js.replace('border-left: 3px solid #38bdf8;', 'border-radius: 12px; border-left: 3px solid #38bdf8;')
js = js.replace('border-left: 4px solid #a855f7;', 'border-radius: 12px; border-left: 4px solid #a855f7;')
js = js.replace('border-left: 3px solid #10b981;', 'border-radius: 12px; border-left: 3px solid #10b981;')


# 6. Change activePromos mapping to use local data (wait, we already fixed res.data to state.promociones inside loadPromocionesData?
# Ah, the original code had: const activePromos = statusFilter === "activas" ? promociones : (res.data || []).filter...
# I need to change res.data to state.promociones there too.
old_active_promos = """const activePromos = statusFilter === "activas" ? promociones : (res.data || []).filter(p => {"""
new_active_promos = """const activePromos = statusFilter === "activas" ? promociones : (state.promociones || []).filter(p => {"""
if old_active_promos in js:
    js = js.replace(old_active_promos, new_active_promos)

# 7. Update upload form success handler to force refresh
old_upload = """                    showToast(result.message || "Promociones cargadas exitosamente.", "success");
                    await loadPromocionesData();"""
new_upload = """                    showToast(result.message || "Promociones cargadas exitosamente.", "success");
                    await loadPromocionesData(true);"""
if old_upload in js:
    js = js.replace(old_upload, new_upload)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("app.js updated.")

# Update index.html for th-inv-disp
html_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

old_th = """<th>Inv. Disp.</th>"""
new_th = """<th style="cursor: pointer; user-select: none;" id="th-inv-disp">Inv. Disp. <i class="fa-solid fa-sort" style="color: hsl(var(--text-secondary)); font-size: 12px; margin-left: 4px;"></i></th>"""
if old_th in html:
    html = html.replace(old_th, new_th)
else:
    print("Could not find <th>Inv. Disp.</th> in HTML.")

# Add sorting options to select
old_sort_html = """<option value="precio-asc">Menor Precio</option>"""
new_sort_html = """<option value="precio-asc">Menor Precio</option>
                                    <option value="inv-desc">Mayor Inventario</option>
                                    <option value="inv-asc">Menor Inventario</option>"""
if old_sort_html in html:
    html = html.replace(old_sort_html, new_sort_html)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("index.html updated.")
