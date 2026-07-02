import sys
import re

file_path = r'c:\Users\Miguel Gonzalez\Downloads\CRMK\crmkuroda\static\app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add state
if 'inventario_abcf: [],' not in content:
    content = content.replace('promociones: [],', 'promociones: [],\n    inventario_abcf: [],')

# 2. Add DOM
dom_addition = '''
    // Inventario ABC+F Section
    tableInventarioAbcf: document.querySelector("#table-inventario-abcf tbody"),
    uploadInventarioAbcfForm: document.getElementById("upload-inventario-abcf-form"),
    filterInvSucursal: document.getElementById("filter-inv-sucursal"),
    filterInvAbcf: document.getElementById("filter-inv-abcf"),
    filterInvSearch: document.getElementById("filter-inv-search"),
    btnClearInvFilters: document.getElementById("btn-clear-inv-filters"),
    pagInventarioAbcf: document.getElementById("pag-inventario-abcf"),
    fileInventarioAbcf: document.getElementById("file-inventario-abcf"),
'''
if 'tableInventarioAbcf:' not in content:
    content = content.replace('// Cotizaciones Section', dom_addition + '\n    // Cotizaciones Section')

# 3. Add to loadSectionData
load_section_addition = '''} else if (sectionId === "inventario-abcf") {
            await loadInventarioAbcfData();
        '''
if 'sectionId === "inventario-abcf"' not in content:
    content = content.replace('} else if (sectionId === "cotizaciones") {', load_section_addition + '} else if (sectionId === "cotizaciones") {')


# 4. Add loadInventarioAbcfData function and event listeners
inventario_logic = '''
async function loadInventarioAbcfData(forceRefresh = false) {
    const searchTerm = DOM.filterInvSearch ? DOM.filterInvSearch.value.toLowerCase() : "";
    const sucursalFilter = DOM.filterInvSucursal ? DOM.filterInvSucursal.value : "todos";
    const abcfFilter = DOM.filterInvAbcf ? DOM.filterInvAbcf.value : "todos";
    
    try {
        if (forceRefresh || !state.inventario_abcf || state.inventario_abcf.length === 0) {
            const res = await apiRequest("/api/v1/inventario-abcf/");
            state.inventario_abcf = res.data || [];
        }
        
        let inventario = [...state.inventario_abcf];
        
        // Populate Selects if empty
        if (DOM.filterInvSucursal && DOM.filterInvSucursal.options.length <= 1) {
            const currentSuc = DOM.filterInvSucursal.value;
            DOM.filterInvSucursal.innerHTML = '<option value="todos">Todos</option>';
            const sucursales = [...new Set(inventario.map(i => i.nombre_centro).filter(Boolean))].sort();
            sucursales.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s;
                opt.textContent = s;
                DOM.filterInvSucursal.appendChild(opt);
            });
            DOM.filterInvSucursal.value = currentSuc;
        }

        if (DOM.filterInvAbcf && DOM.filterInvAbcf.options.length <= 1) {
            const currentAbcf = DOM.filterInvAbcf.value;
            DOM.filterInvAbcf.innerHTML = '<option value="todos">Todos</option>';
            const abcfs = [...new Set(inventario.map(i => i.abc_f).filter(Boolean))].sort();
            abcfs.forEach(a => {
                const opt = document.createElement("option");
                opt.value = a;
                opt.textContent = a;
                DOM.filterInvAbcf.appendChild(opt);
            });
            DOM.filterInvAbcf.value = currentAbcf;
        }

        // Apply filters
        if (sucursalFilter !== "todos") {
            inventario = inventario.filter(i => i.nombre_centro === sucursalFilter);
        }
        if (abcfFilter !== "todos") {
            inventario = inventario.filter(i => i.abc_f === abcfFilter);
        }
        if (searchTerm) {
            inventario = inventario.filter(i => 
                (i.codigo_material && String(i.codigo_material).toLowerCase().includes(searchTerm)) ||
                (i.descripcion_material && String(i.descripcion_material).toLowerCase().includes(searchTerm))
            );
        }
        
        DOM.tableInventarioAbcf.innerHTML = "";
        if (inventario.length === 0) {
            DOM.tableInventarioAbcf.innerHTML = `<tr><td colspan="10" style="text-align: center;">No se encontraron registros de inventario.</td></tr>`;
            return;
        }
        
        // Pagination logic could be added here, for now limit to 100 or 50
        const pageItems = inventario.slice(0, 50);
        
        pageItems.forEach(i => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><span class="badge badge-secondary">${escapeHTML(i.nombre_centro || "-")}</span></td>
                <td>${escapeHTML(i.almacen || "-")}</td>
                <td><strong>${escapeHTML(i.abc_f || "-")}</strong></td>
                <td><code>${escapeHTML(i.codigo_material || "-")}</code></td>
                <td style="max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHTML(i.descripcion_material || "")}">${escapeHTML(i.descripcion_material || "-")}</td>
                <td>${i.cantidad_propia !== null ? i.cantidad_propia.toLocaleString() : "-"}</td>
                <td>${i.existencia_consignacion !== null ? i.existencia_consignacion.toLocaleString() : "-"}</td>
                <td>$${i.costo_promedio_unitario !== null ? i.costo_promedio_unitario.toLocaleString(undefined, {minimumFractionDigits: 2}) : "0.00"}</td>
                <td><strong style="color: #10b981;">$${i.importe_inventario_propio !== null ? i.importe_inventario_propio.toLocaleString(undefined, {minimumFractionDigits: 2}) : "0.00"}</strong></td>
                <td>${escapeHTML(i.ubicacion || "-")}</td>
            `;
            DOM.tableInventarioAbcf.appendChild(tr);
        });

        // Basic pagination info
        if(DOM.pagInventarioAbcf) {
            DOM.pagInventarioAbcf.innerHTML = `<span>Mostrando ${pageItems.length} de ${inventario.length} registros</span>`;
        }
        
    } catch (e) {
        console.error("Error loading inventario:", e);
        DOM.tableInventarioAbcf.innerHTML = `<tr><td colspan="10" style="text-align: center; color: #ef4444;">Error al cargar datos</td></tr>`;
    }
}
'''

if 'async function loadInventarioAbcfData' not in content:
    content = content.replace('async function loadPromocionesData(forceRefresh = false) {', inventario_logic + '\nasync function loadPromocionesData(forceRefresh = false) {')


event_listeners_addition = '''
    if (DOM.uploadInventarioAbcfForm) {
        DOM.uploadInventarioAbcfForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const file = DOM.fileInventarioAbcf.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append("file", file);
            
            const btn = DOM.uploadInventarioAbcfForm.querySelector('button[type="submit"]');
            const ogHtml = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Subiendo...';
            btn.disabled = true;
            
            try {
                const res = await fetch("/api/v1/inventario-abcf/upload", {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${state.token}` },
                    body: formData
                });
                const data = await res.json();
                
                if (res.ok) {
                    showToast(data.message, "success");
                    DOM.fileInventarioAbcf.value = "";
                    document.getElementById('file-inv-name').textContent = "Seleccionar Archivo";
                    await loadInventarioAbcfData(true);
                } else {
                    showToast(data.detail || "Error al subir inventario", "error");
                }
            } catch (err) {
                showToast("Error de conexión", "error");
            } finally {
                btn.innerHTML = ogHtml;
                btn.disabled = false;
            }
        });
    }

    if (DOM.filterInvSucursal) DOM.filterInvSucursal.addEventListener("change", () => loadInventarioAbcfData());
    if (DOM.filterInvAbcf) DOM.filterInvAbcf.addEventListener("change", () => loadInventarioAbcfData());
    if (DOM.filterInvSearch) DOM.filterInvSearch.addEventListener("input", () => {
        clearTimeout(window.invSearchTimeout);
        window.invSearchTimeout = setTimeout(() => loadInventarioAbcfData(), 300);
    });
    if (DOM.btnClearInvFilters) {
        DOM.btnClearInvFilters.addEventListener("click", () => {
            if (DOM.filterInvSucursal) DOM.filterInvSucursal.value = "todos";
            if (DOM.filterInvAbcf) DOM.filterInvAbcf.value = "todos";
            if (DOM.filterInvSearch) DOM.filterInvSearch.value = "";
            loadInventarioAbcfData();
        });
    }
'''

if 'DOM.uploadInventarioAbcfForm.addEventListener' not in content:
    # Inject inside document.addEventListener("DOMContentLoaded")
    content = content.replace('// Global Events', '// Global Events\n' + event_listeners_addition)


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('app.js injected successfully')
