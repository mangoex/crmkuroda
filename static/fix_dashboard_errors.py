import sys

js_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/crmkuroda/static/app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Fix renderSalesChart
js = js.replace('const label = sellerEmail.includes("@") ? sellerEmail.split("@")[0] : sellerEmail;', 'const label = String(sellerEmail).includes("@") ? String(sellerEmail).split("@")[0] : String(sellerEmail);')

# Fix renderGoalsChart
js = js.replace('return (sellers.find(s => s.id === sid)?.email || sid).split("@")[0];', 'return String(sellers.find(s => String(s.id) === String(sid))?.email || sid).split("@")[0];')
js = js.replace('if (sid === state.user.id)', 'if (String(sid) === String(state.user.id))')

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Fixed dashboard string errors.")
