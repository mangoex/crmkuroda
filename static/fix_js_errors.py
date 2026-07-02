import sys

js_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Fix toLowerCase
js = js.replace('p.codigo_material.toLowerCase()', 'String(p.codigo_material).toLowerCase()')
js = js.replace('p.descripcion_material.toLowerCase()', 'String(p.descripcion_material).toLowerCase()')
js = js.replace('p.descrip_gpo_materiales.toLowerCase()', 'String(p.descrip_gpo_materiales).toLowerCase()')
js = js.replace('p.proveedor === proveedorFilter', 'String(p.proveedor) === proveedorFilter')

# Add console logs to help debug in the browser
log_code = """
    console.log("loadPromocionesData called! searchTerm:", searchTerm, "proveedorFilter:", proveedorFilter, "statusFilter:", statusFilter);
    try {
"""
js = js.replace('    try {\n        if (forceRefresh', log_code + '        if (forceRefresh')

log_code2 = """
        console.log("Promociones before filter:", promociones.length);
        if (proveedorFilter !== "todos") {
            promociones = promociones.filter(p => (p.proveedor || "Sin Proveedor") === proveedorFilter);
            console.log("Promociones after proveedor filter:", promociones.length);
        }
"""
# Replace the current proveedor filter with this logged one
import re
js = re.sub(r'if \(proveedorFilter !== "todos"\) \{\s*promociones = promociones\.filter\(p => \(p\.proveedor \|\| "Sin Proveedor"\) === proveedorFilter\);\s*\}', log_code2, js)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Added safe toLowerCase and console logs.")
