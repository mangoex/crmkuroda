import sys

file_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = 'opt.textContent = v.email;'
replacement = """let displayName = v.email;
            if (v.codigo_vendedor && v.nombre_completo) {
                displayName = `${v.codigo_vendedor} ${v.nombre_completo}`;
            } else if (v.codigo_vendedor) {
                displayName = v.codigo_vendedor;
            } else if (v.nombre_completo) {
                displayName = v.nombre_completo;
            }
            opt.textContent = displayName;"""

content = content.replace(target, replacement)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("app.js updated.")
