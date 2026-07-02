import sys

html_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Header
header_start = html.find('<div class="panel-header">', html.find('id="section-promociones"'))
header_end = html.find('</div>', header_start) + 6

old_header = html[header_start:header_end]
new_header = """<div class="panel-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <h2>Promociones Activas</h2>
                        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                            <form id="upload-promociones-form" onsubmit="event.preventDefault();" style="display: flex; gap: 10px; align-items: center; margin: 0;">
                                <label for="file-promociones" class="btn btn-secondary btn-sm" style="cursor: pointer; display: flex; align-items: center; gap: 8px; margin: 0; padding: 0.5rem 1rem;">
                                    <i class="fa-solid fa-file-excel"></i> <span id="file-promo-name">Seleccionar Archivo</span>
                                </label>
                                <input type="file" id="file-promociones" accept=".xlsx" required style="display: none;" onchange="document.getElementById('file-promo-name').textContent = this.files[0] ? this.files[0].name : 'Seleccionar Archivo';">
                                <button type="submit" class="btn btn-primary btn-sm"><i class="fa-solid fa-upload"></i> Subir Promociones</button>
                            </form>
                            <button id="btn-generate-goals-modal" class="btn btn-glow"><i class="fa-solid fa-wand-magic-sparkles"></i> Generar Metas de Promo con IA</button>
                        </div>
                    </div>"""
html = html.replace(old_header, new_header)

# 2. Update Filters
filters_start = html.find('<div class="glass-card filters-card margin-bottom">')
filters_end = html.find('</div>', html.find('</div>', html.find('id="filter-promo-search"'))) + 6
# Actually let's just find the whole filters-card div block
filters_end = html.find('</div>', html.find('id="btn-clear-promo-filters"'))
filters_end = html.find('</div>', filters_end + 6) + 6
filters_end = html.find('</div>', filters_end + 6) + 6

# It might be safer to use regex or string parsing if it's complex, but I can just find the bounds.
# Let's extract the exact string I want to replace using regex.
import re
match = re.search(r'(<div class="glass-card filters-card margin-bottom">.*?</form>.*?</div>.*?</div>\s*</div>\s*</div>\s*</div>)', html, re.DOTALL)
if match:
    old_filters = match.group(1)
    new_filters = """<div class="glass-card filters-card margin-bottom" style="padding: 20px;">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; align-items: end;">
                            <div style="display: flex; flex-direction: column; gap: 6px;">
                                <label for="filter-promo-status" style="font-size: 0.85rem; color: hsl(var(--text-secondary));">Estado</label>
                                <select id="filter-promo-status" class="form-control" style="width: 100%;">
                                    <option value="activas">Activas</option>
                                    <option value="vencidas">Vencidas</option>
                                    <option value="todas">Todas</option>
                                </select>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 6px;">
                                <label for="filter-promo-proveedor" style="font-size: 0.85rem; color: hsl(var(--text-secondary));">Proveedor</label>
                                <select id="filter-promo-proveedor" class="form-control" style="width: 100%;">
                                    <option value="todos">Todos</option>
                                </select>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 6px;">
                                <label for="filter-promo-sort" style="font-size: 0.85rem; color: hsl(var(--text-secondary));">Ordenar por</label>
                                <select id="filter-promo-sort" class="form-control" style="width: 100%;">
                                    <option value="default">Por Defecto</option>
                                    <option value="margen-desc">Mayor Margen</option>
                                    <option value="margen-asc">Menor Margen</option>
                                    <option value="precio-desc">Mayor Precio</option>
                                    <option value="precio-asc">Menor Precio</option>
                                </select>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 6px; grid-column: 1 / -1;">
                                <label for="filter-promo-search" style="font-size: 0.85rem; color: hsl(var(--text-secondary));">Buscar Promoción</label>
                                <div style="display: flex; gap: 10px;">
                                    <input type="text" id="filter-promo-search" class="form-control" placeholder="Código o Descripción..." style="flex-grow: 1;">
                                    <button type="button" id="btn-clear-promo-filters" class="btn btn-secondary" title="Limpiar Filtros" style="display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-filter-circle-xmark"></i> Limpiar Filtros
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>"""
    html = html.replace(old_filters, new_filters)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("index.html updated successfully.")
else:
    print("Error: Could not match filters section.")
