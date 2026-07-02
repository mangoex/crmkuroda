import sys
import re

html_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'
js_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/app.js'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

btn_html = """
                                <div class="input-group-inline" style="margin-bottom: 0;">
                                    <button type="button" id="btn-clear-promo-filters" class="btn btn-secondary" style="height: 100%; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-filter-circle-xmark"></i> Limpiar Filtros
                                    </button>
                                </div>"""

# Insert it after the filter-promo-search input group
search_group = """                                <div class="input-group-inline" style="margin-bottom: 0;">
                                    <label for="filter-promo-search">Buscar:</label>
                                    <input type="text" id="filter-promo-search" placeholder="Código o Descripción...">
                                </div>"""

if search_group in html:
    html = html.replace(search_group, search_group + btn_html)
else:
    print("Warning: Could not find exact search_group string in index.html, using regex")
    # regex fallback
    html = re.sub(r'(<input type="text" id="filter-promo-search"[^>]*>\s*</div>)', r'\1' + btn_html, html)


with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("index.html updated.")

with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Add DOM reference
dom_search = 'filterPromoSearch: document.getElementById("filter-promo-search"),'
dom_replace = dom_search + '\n    btnClearPromoFilters: document.getElementById("btn-clear-promo-filters"),'
js = js.replace(dom_search, dom_replace)

# Add event listener
event_search = 'DOM.filterPromoSearch?.addEventListener("input", loadPromocionesData);'
event_replace = event_search + """
DOM.btnClearPromoFilters?.addEventListener("click", () => {
    if (DOM.filterPromoSearch) DOM.filterPromoSearch.value = '';
    if (DOM.filterPromoStatus) DOM.filterPromoStatus.value = 'activas';
    if (DOM.filterPromoSort) DOM.filterPromoSort.value = 'default';
    if (DOM.filterPromoProveedor) DOM.filterPromoProveedor.value = 'todos';
    loadPromocionesData();
});"""
js = js.replace(event_search, event_replace)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("app.js updated.")
