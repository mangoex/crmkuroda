import sys

html_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the unstyled divs with input-group
html = html.replace('<div style="display: flex; flex-direction: column; gap: 6px;">', '<div class="input-group">')

# Add magnifying glass to search input (wrapping it in a div if needed, or just changing the label)
# The search input HTML is currently:
# <label for="filter-promo-search" style="font-size: 0.85rem; color: hsl(var(--text-secondary));">Buscar Promoción</label>
# <input type="text" id="filter-promo-search" class="form-control" placeholder="Buscar..." style="width: 100%;">
search_label = '<label for="filter-promo-search" style="font-size: 0.85rem; color: hsl(var(--text-secondary));">Buscar Promoción</label>'
new_search_label = '<label for="filter-promo-search" style="font-size: 0.85rem; color: hsl(var(--text-secondary));"><i class="fa-solid fa-magnifying-glass"></i> Buscar Promoción</label>'
html = html.replace(search_label, new_search_label)

# Add arrow icons to Inv. Disp. header if it's missing or improve it
inv_th = '<th id="th-inv-disp" style="cursor: pointer; position: relative;">Inv. Disp.</th>'
new_inv_th = '<th id="th-inv-disp" style="cursor: pointer; position: relative; white-space: nowrap;">Inv. Disp. <i class="fa-solid fa-sort" style="color: hsl(var(--primary)); margin-left: 4px;"></i></th>'
html = html.replace(inv_th, new_inv_th)
# Also check if it was already replaced
inv_th2 = '<th id="th-inv-disp" style="cursor: pointer;">Inv. Disp.</th>'
html = html.replace(inv_th2, new_inv_th)

# Bump version to 1.0.15 to ensure no caching
html = html.replace('app.js?v=1.0.14', 'app.js?v=1.0.15')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("index.html updated successfully.")
