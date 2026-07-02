import sys

file_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add menuApi to DOM
dom_target = 'menuVendedores: document.getElementById("menu-vendedores"),'
dom_replacement = dom_target + '\n    menuApi: document.getElementById("menu-api"),'
if dom_target in content and 'menuApi:' not in content:
    content = content.replace(dom_target, dom_replacement)
    print("Added menuApi to DOM object.")

# 2. Add visibility logic
role_target = 'DOM.btnGenerateGoalsModal.classList.add("hidden");'
role_replacement = role_target + '\n            if (DOM.menuApi) DOM.menuApi.classList.add("hidden");'
if role_target in content and 'DOM.menuApi.classList.add("hidden")' not in content:
    content = content.replace(role_target, role_replacement)
    print("Added hidden logic for menuApi.")

role_target2 = 'DOM.btnGenerateGoalsModal.classList.remove("hidden");'
role_replacement2 = role_target2 + '\n            if (DOM.menuApi) DOM.menuApi.classList.remove("hidden");'
if role_target2 in content and 'DOM.menuApi.classList.remove("hidden")' not in content:
    content = content.replace(role_target2, role_replacement2)
    print("Added remove hidden logic for menuApi.")

# We don't necessarily need to add logic for section toggling because app.js handles navigation dynamically using data-section and sections querySelectorAll, which will automatically include the new menu item and section if we just re-query them.
# Wait, `menuItems` and `sections` are queried statically on load. Since we inserted them in HTML before the script runs, `document.querySelectorAll` will pick them up automatically. No need to update the query!

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
