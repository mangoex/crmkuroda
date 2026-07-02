import sys

file_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update DOM object
dom_target = 'filterPromoSearch: document.getElementById("filter-promo-search"),'
dom_replacement = """filterPromoProveedor: document.getElementById("filter-promo-proveedor"),
    promoKpiProveedores: document.getElementById("promo-kpi-proveedores"),
    filterPromoSearch: document.getElementById("filter-promo-search"),"""
content = content.replace(dom_target, dom_replacement)

# 2. Add event listener
event_target = 'DOM.filterPromoSearch?.addEventListener("input", loadPromocionesData);'
event_replacement = """DOM.filterPromoProveedor?.addEventListener("change", loadPromocionesData);
DOM.filterPromoSearch?.addEventListener("input", loadPromocionesData);"""
content = content.replace(event_target, event_replacement)

# 3. Modify loadPromocionesData
# Find where sortFilter is read, and insert proveedorFilter
sort_target = 'const sortFilter = DOM.filterPromoSort ? DOM.filterPromoSort.value : "default";'
sort_replacement = sort_target + '\n    const proveedorFilter = DOM.filterPromoProveedor ? DOM.filterPromoProveedor.value : "todos";'
content = content.replace(sort_target, sort_replacement)

# Update the filter logic
filter_target = """        if (statusFilter !== "todas") {
            promociones = promociones.filter(p => {
                if (!p.valido_hasta) return statusFilter === "activas";
                const vDate = new Date(p.valido_hasta);
                const isActive = vDate >= today;
                return statusFilter === "activas" ? isActive : !isActive;
            });
        }"""
filter_replacement = filter_target + """
        
        if (proveedorFilter !== "todos") {
            promociones = promociones.filter(p => (p.proveedor || "Sin Proveedor") === proveedorFilter);
        }"""
content = content.replace(filter_target, filter_replacement)

# Inject KPI logic for Top Proveedores
kpi_target = """        // Top 4 por mayor margen promedio
        const topCommissions = [...categories].sort((a, b) => b.avgMargin - a.avgMargin).slice(0, 4);"""

kpi_replacement = kpi_target + """

        const provMap = {};
        activePromos.forEach(p => {
            const prov = p.proveedor || "Sin Proveedor";
            if (!provMap[prov]) {
                provMap[prov] = { name: prov, count: 0, sumMargin: 0 };
            }
            provMap[prov].count++;
            provMap[prov].sumMargin += (p.margen_promocion || 0);
        });

        const providers = Object.values(provMap).map(p => {
            p.avgMargin = p.count > 0 ? (p.sumMargin / p.count) : 0;
            return p;
        });
        
        const topProviders = [...providers].sort((a, b) => b.count - a.count).slice(0, 4);

        if (DOM.filterPromoProveedor && DOM.filterPromoProveedor.options.length <= 1) {
            const currentValue = DOM.filterPromoProveedor.value;
            DOM.filterPromoProveedor.innerHTML = '<option value="todos">Todos</option>';
            providers.sort((a, b) => a.name.localeCompare(b.name)).forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.name;
                opt.textContent = p.name;
                DOM.filterPromoProveedor.appendChild(opt);
            });
            DOM.filterPromoProveedor.value = currentValue;
        }"""
content = content.replace(kpi_target, kpi_replacement)

kpi_render_target = """            } else {
                DOM.promoKpiCommissions.innerHTML = `<div class="glass-card kpi-card" style="grid-column: 1 / -1;"><div class="kpi-data" style="text-align: center; width: 100%;"><p>No hay comisiones calculables</p></div></div>`;
            }
        }"""
kpi_render_replacement = kpi_render_target + """
        if (DOM.promoKpiProveedores) {
            if (topProviders.length > 0) {
                DOM.promoKpiProveedores.innerHTML = topProviders.map((p, i) => `
                    <div class="glass-card kpi-card animate-fade-in" onclick="const sel = document.getElementById('filter-promo-proveedor'); if(sel){ sel.value = '${escapeHTML(p.name)}'; sel.dispatchEvent(new Event('change')); }" style="animation-delay: ${i * 0.1}s; cursor: pointer; border-left: 4px solid #a855f7;">
                        <h4 style="color: #c084fc;">${escapeHTML(p.name)}</h4>
                        <div class="kpi-data" style="margin-top: 10px;">
                            <span style="font-size: 1.1rem; font-weight: 600;">${p.avgMargin.toFixed(2)}% Margen</span>
                            <span class="trend" style="font-size: 0.85rem; margin-top: 4px; display: block; color: hsl(var(--text-secondary));"><i class="fa-solid fa-boxes-stacked"></i> ${p.count} productos</span>
                        </div>
                    </div>
                `).join('');
            } else {
                DOM.promoKpiProveedores.innerHTML = `<div class="glass-card kpi-card" style="grid-column: 1 / -1;"><div class="kpi-data" style="text-align: center; width: 100%;"><p>No hay proveedores disponibles</p></div></div>`;
            }
        }"""
content = content.replace(kpi_render_target, kpi_render_replacement)


# Update Table row rendering
table_row_target = """            tr.innerHTML = `
                <td>${p.centro || '-'}</td>
                <td><strong>${p.codigo_material || '-'}</strong></td>
                <td>${p.descripcion_material || '-'}</td>
                <td><strong>$${(p.precio_promocion || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}</strong> ${p.moneda || ''}</td>
                <td>${p.margen_promocion ? (p.margen_promocion).toFixed(2) : '-'}</td>
                <td>${p.valido_hasta ? p.valido_hasta.split('T')[0] : '-'}</td>
            `;"""
table_row_replacement = """            tr.innerHTML = `
                <td>${p.centro || '-'}</td>
                <td><strong>${p.codigo_material || '-'}</strong></td>
                <td>${p.descripcion_material || '-'}</td>
                <td>${p.proveedor || '-'}</td>
                <td><strong>$${(p.precio_promocion || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}</strong> ${p.moneda || ''}</td>
                <td>${p.margen_promocion ? (p.margen_promocion).toFixed(2) : '-'}</td>
                <td>${p.inventario_disponible !== null && p.inventario_disponible !== undefined ? p.inventario_disponible : '-'}</td>
                <td>${p.valido_hasta ? p.valido_hasta.split('T')[0] : '-'}</td>
            `;"""
content = content.replace(table_row_target, table_row_replacement)


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("app.js updated successfully.")
