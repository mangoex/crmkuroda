import sys

file_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add KPI block for Proveedores
kpi_commissions_end = content.find('</div>', content.find('id="promo-kpi-commissions"')) + len('</div>')
if kpi_commissions_end != -1:
    new_kpi = """

                        <div class="kpi-section-title" style="margin-bottom: 16px; margin-top: 24px;">
                            <h3 style="font-size: 16px; display: flex; align-items: center; gap: 8px;">
                                <i class="fa-solid fa-truck-fast text-glow" style="color: #a855f7;"></i> Top Proveedores
                            </h3>
                            <p style="font-size: 13px; color: hsl(var(--text-secondary)); margin-top: 4px;">Proveedores con mayor cantidad de productos en promoción.</p>
                        </div>
                        <div class="kpi-grid" id="promo-kpi-proveedores" style="margin-bottom: 24px;">
                            <!-- Dynamically loaded -->
                        </div>"""
    content = content[:kpi_commissions_end] + new_kpi + content[kpi_commissions_end:]

# 2. Add Select Filter
status_filter_end = content.find('</div>', content.find('id="filter-promo-status"')) + len('</div>')
if status_filter_end != -1:
    new_filter = """
                                <div class="input-group-inline" style="margin-bottom: 0;">
                                    <label for="filter-promo-proveedor">Proveedor:</label>
                                    <select id="filter-promo-proveedor" style="width: auto; max-width: 150px;">
                                        <option value="todos">Todos</option>
                                    </select>
                                </div>"""
    content = content[:status_filter_end] + new_filter + content[status_filter_end:]

# 3. Update Table Headers
table_head_start = content.find('<th>Centro</th>', content.find('id="table-promociones"'))
table_head_end = content.find('</tr>', table_head_start)
if table_head_start != -1 and table_head_end != -1:
    old_tr = content[table_head_start:table_head_end]
    new_tr = """<th>Centro</th>
                                    <th>Código</th>
                                    <th>Descripción</th>
                                    <th>Proveedor</th>
                                    <th>Precio Promo</th>
                                    <th>Margen</th>
                                    <th>Inv. Disp.</th>
                                    <th>Válido Hasta</th>
                                """
    content = content.replace(old_tr, new_tr)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("index.html updated successfully.")
