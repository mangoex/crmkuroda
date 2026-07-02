import sys

js_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# We need to extract the search filter logic and move it up.
search_filter_code = """
        // Filter Search Text
        if (searchTerm) {
            promociones = promociones.filter(p => 
                (p.codigo_material && p.codigo_material.toLowerCase().includes(searchTerm)) ||
                (p.descripcion_material && p.descripcion_material.toLowerCase().includes(searchTerm)) ||
                (p.descrip_gpo_materiales && p.descrip_gpo_materiales.toLowerCase().includes(searchTerm))
            );
        }
"""

if search_filter_code in js:
    js = js.replace(search_filter_code, "")
    
    insert_point = js.find('// --- CALCULAR Y RENDERIZAR KPIs DE PROMOCIONES ---')
    if insert_point != -1:
        js = js[:insert_point] + search_filter_code[1:] + "\n        " + js[insert_point:]
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(js)
        print("app.js updated successfully.")
    else:
        print("Could not find insertion point.")
else:
    print("Could not find search filter code block.")
